import time

from backend.store import GameStore


class GameEngine:
    def __init__(self, store: GameStore):
        self.store = store

    def start(self, show_target: bool, timer_seconds: int | None) -> bool:
        data = self.store.load()
        if data["layout"] is None or len(data["bases"]) < 3:
            data["state"]["mode"] = "layout_ready" if data["layout"] else "idle"
            self.store.save(data)
            return False
        target = self._next_target(data)
        data["state"].update({
            "mode": "seeking",
            "target_base_id": target["id"],
            "show_target": bool(show_target),
            "timer_seconds": timer_seconds,
            "round": data["state"].get("round", 0) + 1,
            "arrival_streak": 0,
            "started_at": int(time.time()),
        })
        data["settings"]["show_target"] = bool(show_target)
        data["settings"]["timer_seconds"] = timer_seconds
        self.store.save(data)
        return True

    def stop(self) -> dict:
        data = self.store.load()
        data["state"].update({"mode": "game_available" if len(data["bases"]) >= 3 else "layout_ready", "target_base_id": None})
        return self.store.save(data)

    def next_target(self) -> dict | None:
        data = self.store.load()
        if len(data["bases"]) < 3:
            self.stop()
            return None
        target = self._next_target(data)
        data["state"].update({
            "mode": "seeking",
            "target_base_id": target["id"],
            "round": data["state"].get("round", 0) + 1,
            "arrival_streak": 0,
            "started_at": int(time.time()),
        })
        self.store.save(data)
        return target

    def update_arrival(self, warm_value: float, threshold: float, arrival_ticks: int) -> bool:
        data = self.store.load()
        streak = data["state"].get("arrival_streak", 0)
        streak = streak + 1 if warm_value >= threshold else 0
        if streak >= arrival_ticks:
            data["state"]["score"] = data["state"].get("score", 0) + 1
            data["state"]["mode"] = "found"
            data["state"]["arrival_streak"] = 0
            self.store.save(data)
            return True
        data["state"]["arrival_streak"] = streak
        self.store.save(data)
        return False

    def _next_target(self, data: dict) -> dict:
        bases = data["bases"]
        current_id = data["state"].get("target_base_id")
        if not current_id:
            return bases[0]
        for index, base in enumerate(bases):
            if base["id"] == current_id:
                return bases[(index + 1) % len(bases)]
        return bases[0]
