import math
from dataclasses import dataclass


EPSILON = 0.000001


@dataclass(frozen=True)
class Baseline:
    mean: dict[int, float]
    std: dict[int, float]

    @property
    def node_ids(self) -> list[int]:
        return sorted(self.mean)


def build_baseline(samples: list[dict[int, float]]) -> Baseline:
    node_ids = sorted({node_id for sample in samples for node_id in sample})
    means: dict[int, float] = {}
    stds: dict[int, float] = {}
    for node_id in node_ids:
        values = [sample[node_id] for sample in samples if node_id in sample]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        means[node_id] = mean
        stds[node_id] = max(math.sqrt(variance), EPSILON)
    return Baseline(mean=means, std=stds)


def baseline_from_json(payload: dict) -> Baseline:
    return Baseline(
        mean={int(node_id): float(value) for node_id, value in (payload.get("mean") or {}).items()},
        std={int(node_id): float(value) for node_id, value in (payload.get("std") or {}).items()},
    )


def baseline_to_json(baseline: Baseline) -> dict:
    return {
        "mean": {str(node_id): value for node_id, value in baseline.mean.items()},
        "std": {str(node_id): value for node_id, value in baseline.std.items()},
        "node_ids": baseline.node_ids,
    }


def disturbance_vector(values: dict[int, float], baseline: Baseline) -> dict[int, float]:
    scores: dict[int, float] = {}
    for node_id in baseline.node_ids:
        if node_id not in values:
            scores[node_id] = 0.0
            continue
        scores[node_id] = abs(values[node_id] - baseline.mean[node_id]) / max(baseline.std[node_id], EPSILON)
    return scores


def build_signature(samples: list[dict[int, float]]) -> dict[int, float]:
    node_ids = sorted({node_id for sample in samples for node_id in sample})
    signature: dict[int, float] = {}
    for node_id in node_ids:
        values = [sample.get(node_id, 0.0) for sample in samples]
        signature[node_id] = sum(values) / len(values)
    return signature


def cosine_similarity(left: dict[int, float], right: dict[int, float]) -> float:
    node_ids = sorted(set(left) | set(right))
    dot = sum(left.get(node_id, 0.0) * right.get(node_id, 0.0) for node_id in node_ids)
    left_norm = math.sqrt(sum(left.get(node_id, 0.0) ** 2 for node_id in node_ids))
    right_norm = math.sqrt(sum(right.get(node_id, 0.0) ** 2 for node_id in node_ids))
    if left_norm <= EPSILON or right_norm <= EPSILON:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def warmth(live: dict[int, float], target: dict[int, float], movement_floor: float) -> float:
    total_disturbance = sum(max(0.0, value) for value in live.values())
    if total_disturbance < movement_floor:
        return 0.0
    motion_scale = min(1.0, total_disturbance / max(movement_floor * 4.0, EPSILON))
    return cosine_similarity(live, target) * motion_scale
