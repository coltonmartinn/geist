import json
import unittest
from pathlib import Path

from backend.csi_source import extract_node_values


FIXTURE = Path(__file__).parent / "fixtures" / "ruview_one_node.json"


class CSISourceTests(unittest.TestCase):
    def test_extracts_motion_band_power_from_node_features(self):
        payload = json.loads(FIXTURE.read_text())

        values = extract_node_values(payload)

        self.assertEqual(set(values), {1})
        self.assertAlmostEqual(values[1], 1722.7913520072377)

    def test_falls_back_to_variance_when_motion_band_power_missing(self):
        payload = {
            "node_features": [
                {"node_id": 2, "features": {"variance": 42.5}, "stale": False},
                {"node_id": 3, "features": {"motion_band_power": 9.0}, "stale": True},
            ]
        }

        values = extract_node_values(payload)

        self.assertEqual(values, {2: 42.5})

    def test_falls_back_to_amplitude_variance_when_node_features_missing(self):
        payload = {
            "nodes": [
                {"node_id": 7, "amplitude": [10.0, 12.0, 14.0, 16.0], "stale": False}
            ]
        }

        values = extract_node_values(payload)

        self.assertEqual(set(values), {7})
        self.assertAlmostEqual(values[7], 5.0)


if __name__ == "__main__":
    unittest.main()
