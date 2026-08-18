"""验证闭环纯函数测试：Tier-2 判定 + 置信度校准 + 震荡统计。"""

import unittest

import app


class TestTier2Verdict(unittest.TestCase):
    def test_up(self):
        self.assertEqual(app._tier2_verdict("up", 2.0, 1.0), "✅")
        self.assertEqual(app._tier2_verdict("up", 0.5, 1.0), "➡️")
        self.assertEqual(app._tier2_verdict("up", -1.0, 1.0), "❌")

    def test_down(self):
        self.assertEqual(app._tier2_verdict("down", -2.0, 1.0), "✅")
        self.assertEqual(app._tier2_verdict("down", -0.3, 1.0), "➡️")
        self.assertEqual(app._tier2_verdict("down", 1.0, 1.0), "❌")

    def test_flat(self):
        self.assertEqual(app._tier2_verdict("flat", 0.5, 1.0), "✅")
        self.assertEqual(app._tier2_verdict("flat", 1.5, 1.0), "➡️")
        self.assertEqual(app._tier2_verdict("flat", 3.0, 1.0), "❌")


class TestOscillationCount(unittest.TestCase):
    def test_counts_flat(self):
        data = [
            {"date": "2026-07-06", "predictions": {
                "A": {"direction": "up"},
                "B": {"direction": "flat"},
            }},
            {"date": "2026-07-07", "predictions": {
                "A": {"direction": "flat-down"},
            }},
        ]
        total, neutral = app._count_oscillation_predictions(data)
        self.assertEqual(total, 3)
        self.assertEqual(neutral, 2)


class TestConfidenceCalibration(unittest.TestCase):
    def test_bucket_counts_with_backfilled_actual(self):
        data = [
            {"date": "2026-07-06", "predictions": {
                "A": {"direction": "up", "confidence": "高", "actual": 2.5},
                "B": {"direction": "up", "confidence": "高", "actual": -1.0},
                "C": {"direction": "down", "confidence": "低", "actual": -3.0},
            }},
        ]
        buckets = app._compute_confidence_calibration(data, [])
        self.assertEqual(buckets["高"]["total"], 2)
        self.assertEqual(buckets["高"]["correct"], 1)
        self.assertEqual(buckets["低"]["total"], 1)
        self.assertEqual(buckets["低"]["correct"], 1)

    def test_unknown_confidence_falls_back_to_low(self):
        data = [
            {"date": "2026-07-06", "predictions": {
                "A": {"direction": "up", "confidence": "极高", "actual": 2.0},
            }},
        ]
        buckets = app._compute_confidence_calibration(data, [])
        self.assertEqual(buckets["低"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
