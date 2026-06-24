import tempfile
import unittest
from pathlib import Path

from backend.app import GeistApp
from backend.config import Config


class AppTests(unittest.TestCase):
    def test_health_reports_mock_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = GeistApp(Config(data_path=Path(tmp) / "game.json", source_mode="mock"))

            status, body = app.handle_get("/health")

            self.assertEqual(status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["source"], "mock")

    def test_snapshot_includes_detected_node_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = GeistApp(Config(data_path=Path(tmp) / "game.json", source_mode="mock"))

            status, body = app.handle_get("/api/snapshot")

            self.assertEqual(status, 200)
            self.assertEqual(body["node_ids"], [1, 2, 3, 4, 5, 6])
            self.assertGreater(body["values"]["1"], 0)


if __name__ == "__main__":
    unittest.main()
