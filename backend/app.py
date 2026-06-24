import json
import time
from pathlib import Path
from typing import Any

from backend.config import Config
from backend.csi_source import MockSource, RuViewSource, Snapshot
from backend.scoring import (
    baseline_from_json,
    baseline_to_json,
    build_baseline,
    build_signature,
    disturbance_vector,
    warmth,
)
from backend.state import GameEngine
from backend.store import GameStore


class GeistApp:
    def __init__(self, config: Config):
        self.config = config
        self.store = GameStore(config.data_path)
        self.engine = GameEngine(self.store)
        self.source = MockSource() if config.source_mode == "mock" else RuViewSource(config.ruview_base_url)

    def handle_get(self, path: str) -> tuple[int, dict[str, Any]]:
        if path == "/health":
            return 200, {
                "ok": True,
                "source": self.config.source_mode,
                "ruview_base_url": self.config.ruview_base_url,
            }
        if path == "/api/snapshot":
            return 200, self.snapshot()
        return 404, {"error": "not found"}

    def handle_post(self, path: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if path == "/api/layout/reset":
            self.store.reset_layout()
            return 200, self.snapshot()
        if path == "/api/layout/baseline":
            seconds = float(body.get("seconds", 10))
            return self._capture_baseline(seconds)
        if path == "/api/bases/capture":
            name = str(body.get("name") or f"Base {len(self.store.load()['bases']) + 1}")
            seconds = float(body.get("seconds", 12))
            return self._capture_base(name, seconds)
        if path == "/api/game/start":
            show_target = bool(body.get("show_target", True))
            timer_seconds = body.get("timer_seconds")
            if timer_seconds in ("", 0):
                timer_seconds = None
            started = self.engine.start(show_target=show_target, timer_seconds=timer_seconds)
            return (200 if started else 409), self.snapshot()
        if path == "/api/game/stop":
            self.engine.stop()
            return 200, self.snapshot()
        if path == "/api/game/next":
            target = self.engine.next_target()
            return (200 if target else 409), self.snapshot()
        return 404, {"error": "not found"}

    def handle_patch(self, path: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if path == "/api/game/settings":
            self.store.update_settings(body)
            return 200, self.snapshot()
        return 404, {"error": "not found"}

    def handle_delete(self, path: str) -> tuple[int, dict[str, Any]]:
        prefix = "/api/bases/"
        if path.startswith(prefix):
            deleted = self.store.delete_base(path[len(prefix):])
            return (200 if deleted else 404), self.snapshot()
        return 404, {"error": "not found"}

    def snapshot(self) -> dict[str, Any]:
        source_snapshot = self.source.latest()
        data = self.store.load()
        data = self._apply_timer(data)
        live_disturbance: dict[int, float] = {}
        warm_value = 0.0
        target = None
        warnings = self._warnings(source_snapshot, data)
        if source_snapshot.ok and data.get("layout"):
            baseline = baseline_from_json(data["layout"])
            live_disturbance = disturbance_vector(source_snapshot.values, baseline)
            target = self._target_base(data)
            if target:
                signature = {int(node_id): float(value) for node_id, value in target["signature"].items()}
                warm_value = warmth(live_disturbance, signature, self.config.movement_floor)
                if data["state"].get("mode") == "seeking":
                    self.engine.update_arrival(warm_value, target.get("threshold", self.config.arrival_threshold), self.config.arrival_ticks)
                    data = self.store.load()
        return {
            "source_ok": source_snapshot.ok,
            "source": source_snapshot.source,
            "source_error": source_snapshot.error,
            "node_ids": source_snapshot.node_ids,
            "values": {str(node_id): value for node_id, value in source_snapshot.values.items()},
            "disturbance": {str(node_id): value for node_id, value in live_disturbance.items()},
            "warmth": warm_value,
            "target": self._public_target(data, target),
            "layout": data.get("layout"),
            "bases": data.get("bases", []),
            "state": data.get("state", {}),
            "settings": data.get("settings", {}),
            "warnings": warnings,
        }

    def _apply_timer(self, data: dict) -> dict:
        state = data.get("state", {})
        timer_seconds = state.get("timer_seconds")
        started_at = state.get("started_at")
        if state.get("mode") == "seeking" and timer_seconds and started_at:
            if time.time() - float(started_at) >= float(timer_seconds):
                state["mode"] = "time_up"
                state["target_base_id"] = None
                state["arrival_streak"] = 0
                self.store.save(data)
        return data

    def _capture_baseline(self, seconds: float) -> tuple[int, dict[str, Any]]:
        samples = self._collect_samples(seconds)
        if not samples:
            return 503, {"error": "No RuView node values received"}
        baseline = build_baseline(samples)
        self.store.save_layout(baseline_to_json(baseline))
        return 200, self.snapshot()

    def _capture_base(self, name: str, seconds: float) -> tuple[int, dict[str, Any]]:
        data = self.store.load()
        if not data.get("layout"):
            return 409, {"error": "Create a layout baseline first"}
        baseline = baseline_from_json(data["layout"])
        samples = [disturbance_vector(sample, baseline) for sample in self._collect_samples(seconds)]
        if not samples:
            return 503, {"error": "No RuView node values received"}
        signature = build_signature(samples)
        threshold = max(0.45, min(0.85, sum(signature.values()) / max(len(signature), 1) / 6.0))
        self.store.add_base(name, signature, threshold=threshold)
        return 200, self.snapshot()

    def _collect_samples(self, seconds: float) -> list[dict[int, float]]:
        interval = 1.0 / max(self.config.poll_hz, 1.0)
        count = max(1, int(seconds * self.config.poll_hz))
        samples: list[dict[int, float]] = []
        for index in range(count):
            snapshot = self.source.latest()
            if snapshot.ok and snapshot.values:
                samples.append(snapshot.values)
            if index != count - 1:
                time.sleep(interval)
        return samples

    def _target_base(self, data: dict) -> dict | None:
        target_id = data.get("state", {}).get("target_base_id")
        for base in data.get("bases", []):
            if base["id"] == target_id:
                return base
        return None

    def _public_target(self, data: dict, target: dict | None) -> dict | None:
        if not target:
            return None
        if not data.get("state", {}).get("show_target", True):
            return {"hidden": True}
        return {"id": target["id"], "name": target["name"]}

    def _warnings(self, snapshot: Snapshot, data: dict) -> list[str]:
        warnings: list[str] = []
        if not snapshot.ok:
            warnings.append(f"Cannot reach RuView at {self.config.ruview_base_url}")
        if 0 < len(snapshot.node_ids) < 3:
            warnings.append("Fewer than 3 nodes detected. Good for connectivity testing, weak for gameplay.")
        if 3 <= len(snapshot.node_ids) < 6:
            warnings.append("Geist works with this node count, but 6 spread-out nodes improve fidelity.")
        if data.get("layout") and sorted(data["layout"].get("node_ids", [])) != snapshot.node_ids and snapshot.node_ids:
            warnings.append("Current node IDs differ from the saved layout. Recreate the layout if hardware moved.")
        return warnings


def load_sample_data() -> dict:
    sample = Path("data/sample_layout.json")
    if sample.exists():
        return json.loads(sample.read_text())
    return {}
