import unittest

from divergence import fundamental_state, fundamental_context, classify_divergence


class TestFundamentalState(unittest.TestCase):
    def test_weak_when_conclusion_runaway(self):
        st = fundamental_state({"assessment": {"conclusion": "考虑跑路"}})
        self.assertEqual(st["level"], "weak")
        self.assertIn("基本面走弱", st["message"])

    def test_warning_when_any_down_indicator(self):
        st = fundamental_state({
            "assessment": {"conclusion": "安心持有"},
            "leading_indicators": {"a": {"trend": "up"}, "b": {"trend": "down"}},
        })
        self.assertEqual(st["level"], "warning")
        self.assertIn("领先 1↑0→1↓", st["message"])

    def test_ok_when_no_down(self):
        st = fundamental_state({
            "assessment": {"conclusion": "安心持有"},
            "leading_indicators": {"a": {"trend": "up"}},
        })
        self.assertEqual(st["level"], "ok")

    def test_empty_input_is_ok(self):
        st = fundamental_state(None)
        self.assertEqual(st["level"], "ok")

    def test_context_weak_advises_exit_plan(self):
        ctx = fundamental_context({"assessment": {"conclusion": "高位警惕"}})
        self.assertIn("离场计划", ctx)


class TestClassifyDivergence(unittest.TestCase):
    def test_thesis_invalidation_is_auto_exit(self):
        d = classify_divergence(thesis_invalidated=True)
        self.assertEqual(d["category"], "⑥")
        self.assertEqual(d["disposition"], "exit")
        self.assertTrue(d["auto"])
        self.assertFalse(d["needs_confirm"])

    def test_weak_fundamental_is_reduce_candidate(self):
        d = classify_divergence(fundamental={"level": "weak"})
        self.assertEqual(d["category"], "③")
        self.assertEqual(d["disposition"], "reduce_candidate")
        self.assertTrue(d["needs_confirm"])
        self.assertFalse(d["auto"])

    def test_pullback_with_ok_fundamental_is_inhale_candidate(self):
        d = classify_divergence(fundamental={"level": "ok"}, day_return_pct=-4.2)
        self.assertEqual(d["category"], "②a")
        self.assertEqual(d["disposition"], "add_candidate")
        self.assertTrue(d["needs_confirm"])

    def test_surge_with_ok_fundamental_is_observe(self):
        d = classify_divergence(fundamental={"level": "ok"}, day_return_pct=3.1)
        self.assertEqual(d["category"], "②b")
        self.assertEqual(d["disposition"], "observe")
        self.assertFalse(d["needs_confirm"])

    def test_small_move_is_price_only(self):
        d = classify_divergence(fundamental={"level": "ok"}, day_return_pct=0.5)
        self.assertEqual(d["category"], "①")
        self.assertEqual(d["disposition"], "observe")

    def test_labels_match_legacy_ui(self):
        legacy = [
            ({"level": "weak"}, None, "基本面走弱 → 离场/减仓优先"),
            ({"level": "ok"}, -4.2, "价格回调+基本面完好 → 逆向吸入候选（人工确认）"),
            ({"level": "ok"}, 3.1, "今日大涨+基本面未变 → 观察不追高"),
        ]
        for fs, r, want in legacy:
            self.assertEqual(
                classify_divergence(fundamental=fs, day_return_pct=r)["label"], want
            )


if __name__ == "__main__":
    unittest.main()
