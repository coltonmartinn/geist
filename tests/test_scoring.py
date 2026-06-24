import unittest

from backend.scoring import (
    Baseline,
    build_baseline,
    build_signature,
    cosine_similarity,
    disturbance_vector,
    warmth,
)


class ScoringTests(unittest.TestCase):
    def test_build_baseline_computes_mean_and_std_per_node(self):
        baseline = build_baseline([{1: 10.0}, {1: 12.0}, {1: 14.0}])

        self.assertEqual(baseline.node_ids, [1])
        self.assertAlmostEqual(baseline.mean[1], 12.0)
        self.assertAlmostEqual(baseline.std[1], 1.632993161855452)

    def test_disturbance_vector_normalizes_against_baseline(self):
        baseline = Baseline(mean={1: 10.0, 2: 20.0}, std={1: 2.0, 2: 5.0})

        scores = disturbance_vector({1: 14.0, 2: 15.0}, baseline)

        self.assertEqual(scores, {1: 2.0, 2: 1.0})

    def test_build_signature_averages_disturbance_samples(self):
        signature = build_signature([
            {1: 1.0, 2: 3.0},
            {1: 3.0, 2: 5.0},
            {1: 5.0, 2: 7.0},
        ])

        self.assertEqual(signature, {1: 3.0, 2: 5.0})

    def test_cosine_similarity_handles_missing_and_zero_values(self):
        self.assertAlmostEqual(
            cosine_similarity({1: 1.0, 2: 0.0}, {1: 1.0, 2: 0.0}),
            1.0,
        )
        self.assertEqual(cosine_similarity({1: 0.0}, {1: 0.0}), 0.0)
        self.assertEqual(cosine_similarity({1: 1.0}, {2: 1.0}), 0.0)

    def test_warmth_requires_motion_floor(self):
        target = {1: 3.0, 2: 1.0}

        cold = warmth({1: 0.1, 2: 0.1}, target, movement_floor=1.0)
        hot = warmth({1: 3.0, 2: 1.0}, target, movement_floor=1.0)

        self.assertEqual(cold, 0.0)
        self.assertAlmostEqual(hot, 1.0)


if __name__ == "__main__":
    unittest.main()
