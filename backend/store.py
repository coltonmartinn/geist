import json
import time
from pathlib import Path
from uuid import uuid4


def _default_state() -> dict:
    return {
        "layout": None,
        "bases": [],
        "state": {
            "mode": "idle",
            "target_base_id": None,
            "show_target": True,
            "timer_seconds": None,
            "round": 0,
            "score": 0,
            "arrival_streak": 0,
            "started_at": None,
        },
        "settings": {
            "audio_mode": "clicks",
            "show_target": True,
            "timer_seconds": None,
        },
    }


class GameStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        if not self.path.exists():
            return _default_state()
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True))
        return data

    def reset_layout(self) -> dict:
        return self.save(_default_state())

    def save_layout(self, layout: dict) -> dict:
        data = self.load()
        data["layout"] = layout
        data["bases"] = []
        data["state"] = _default_state()["state"]
        data["state"]["mode"] = "layout_ready"
        return self.save(data)

    def add_base(self, name: str, signature: dict[str, float] | dict[int, float], threshold: float) -> dict:
        data = self.load()
        base = {
            "id": str(uuid4()),
            "name": name,
            "signature": {str(node_id): float(value) for node_id, value in signature.items()},
            "threshold": float(threshold),
            "created_at": int(time.time()),
        }
        data["bases"].append(base)
        data["state"]["mode"] = "game_available" if len(data["bases"]) >= 3 else "layout_ready"
        self.save(data)
        return base

    def delete_base(self, base_id: str) -> bool:
        data = self.load()
        before = len(data["bases"])
        data["bases"] = [base for base in data["bases"] if base["id"] != base_id]
        if data["state"].get("target_base_id") == base_id:
            data["state"]["target_base_id"] = None
            data["state"]["mode"] = "game_available" if len(data["bases"]) >= 3 else "layout_ready"
        self.save(data)
        return len(data["bases"]) != before

    def update_state(self, patch: dict) -> dict:
        data = self.load()
        data["state"].update(patch)
        return self.save(data)

    def update_settings(self, patch: dict) -> dict:
        data = self.load()
        data["settings"].update(patch)
        if "show_target" in patch:
            data["state"]["show_target"] = bool(patch["show_target"])
        if "timer_seconds" in patch:
            data["state"]["timer_seconds"] = patch["timer_seconds"]
        return self.save(data)
