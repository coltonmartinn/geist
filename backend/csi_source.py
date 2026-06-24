import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class SourceError(RuntimeError):
    pass


def extract_node_values(payload: dict[str, Any]) -> dict[int, float]:
    values: dict[int, float] = {}
    for item in payload.get("node_features", []) or []:
        if item.get("stale"):
            continue
        node_id = item.get("node_id")
        features = item.get("features") or {}
        value = features.get("motion_band_power", features.get("variance"))
        if node_id is not None and value is not None:
            values[int(node_id)] = float(value)
    if values:
        return values

    for item in payload.get("nodes", []) or []:
        if item.get("stale"):
            continue
        node_id = item.get("node_id")
        amplitude = item.get("amplitude") or []
        if node_id is None or len(amplitude) < 2:
            continue
        mean = sum(float(v) for v in amplitude) / len(amplitude)
        variance = sum((float(v) - mean) ** 2 for v in amplitude) / len(amplitude)
        values[int(node_id)] = variance
    return values


@dataclass
class Snapshot:
    values: dict[int, float]
    source: str
    ok: bool
    error: str | None = None

    @property
    def node_ids(self) -> list[int]:
        return sorted(self.values)


class RuViewSource:
    def __init__(self, base_url: str, timeout: float = 2.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def latest(self) -> Snapshot:
        url = f"{self.base_url}/api/v1/sensing/latest"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            return Snapshot(values={}, source="ruview", ok=False, error=str(exc))
        return Snapshot(values=extract_node_values(payload), source="ruview", ok=True)


class MockSource:
    def __init__(self):
        self.tick = 0

    def latest(self) -> Snapshot:
        self.tick += 1
        target = ((self.tick // 24) % 6) + 1
        values: dict[int, float] = {}
        for node_id in range(1, 7):
            distance = abs(node_id - target)
            wave = 1.0 + math.sin((self.tick + node_id) / 4.0) * 0.12
            values[node_id] = max(0.1, (6.0 - distance) * wave)
        return Snapshot(values=values, source="mock", ok=True)


class RecordedSource:
    def __init__(self, frames: list[dict[int, float]]):
        self.frames = frames or [{1: 1.0}]
        self.index = 0

    def latest(self) -> Snapshot:
        frame = self.frames[self.index % len(self.frames)]
        self.index += 1
        time.sleep(0)
        return Snapshot(values=frame, source="recorded", ok=True)
