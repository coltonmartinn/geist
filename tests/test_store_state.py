import tempfile
import unittest
from pathlib import Path

from backend.state import GameEngine
from backend.store import GameStore


class StoreStateTests(unittest.TestCase):
    def test_game_requires_three_bases(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = GameStore(Path(tmp) / "game.json")
            engine = GameEngine(store)
            store.save_layout({"mean": {"1": 10.0}, "std": {"1": 1.0}, "node_ids": [1]})
            store.add_base("Door", {"1": 1.0}, threshold=0.6)
            store.add_base("Window", {"1": 2.0}, threshold=0.6)

            started = engine.start(show_target=True, timer_seconds=None)

            self.assertFalse(started)
            self.assertEqual(store.load()["state"]["mode"], "layout_ready")

    def test_game_picks_target_when_three_bases_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = GameStore(Path(tmp) / "game.json")
            engine = GameEngine(store)
            store.save_layout({"mean": {"1": 10.0}, "std": {"1": 1.0}, "node_ids": [1]})
            for name in ["Door", "Window", "Desk"]:
                store.add_base(name, {"1": 1.0}, threshold=0.6)

            started = engine.start(show_target=False, timer_seconds=60)
            state = store.load()["state"]

            self.assertTrue(started)
            self.assertEqual(state["mode"], "seeking")
            self.assertFalse(state["show_target"])
            self.assertEqual(state["timer_seconds"], 60)
            self.assertIsNotNone(state["target_base_id"])


if __name__ == "__main__":
    unittest.main()
