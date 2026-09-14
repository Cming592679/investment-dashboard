import os
import unittest

from rules import load_rules, validate_rules


RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules.yaml")


class TestRulesLoader(unittest.TestCase):
    def test_loads_required_structure(self):
        rules = load_rules(RULES_PATH)
        self.assertEqual(rules["version"], 1.2)
        self.assertIn("position_tiers", rules)
        self.assertIn("risk_limits", rules)
        self.assertIn("trend_gate", rules)
        self.assertIn("rsi", rules)
        self.assertIn("divergence", rules)
        self.assertIn("cadence", rules)

    def test_position_tiers_values(self):
        rules = load_rules(RULES_PATH)
        tiers = rules["position_tiers"]
        self.assertEqual(tiers["explore"], 0.03)
        self.assertEqual(tiers["watch"], 0.05)
        self.assertEqual(tiers["verify"], 0.08)
        self.assertEqual(tiers["core"], 0.15)

    def test_cash_reserve_tiers_are_monotonic(self):
        """分层现金储备：下限必须逐档递减，且不高于 base_floor（v1.2）"""
        rules = load_rules(RULES_PATH)
        cr = rules["cash_reserve"]
        self.assertTrue(cr["enabled"])
        self.assertEqual(cr["base_floor"], 0.10)
        self.assertGreaterEqual(cr["l1_floor"], cr["l2_floor"])
        self.assertGreaterEqual(cr["l2_floor"], cr["l3_floor"])
        self.assertEqual(cr["l3_floor"], 0.0)   # 允许归零（用户决策）
        self.assertLessEqual(cr["l1_floor"], cr["base_floor"])
        self.assertEqual(cr["return_deadline_days"], 20)
        self.assertEqual(cr["return_basis"], "exit-condition-not-pnl")

    def test_cash_reserve_thresholds_match_backtest(self):
        """阈值来自 2020-2026 回测，频率应逐档递减（2.99 → 1.04 → 0.45）"""
        cr = load_rules(RULES_PATH)["cash_reserve"]
        freqs = [cr["l1_freq_per_year"], cr["l2_freq_per_year"], cr["l3_freq_per_year"]]
        self.assertEqual(freqs, sorted(freqs, reverse=True))
        self.assertGreater(cr["l1_min_sector_rsi20"], 0)
        self.assertLess(cr["l2_index_drop_20d"], 0)
        self.assertLess(cr["l3_dev_ma50"], 0)

    def test_validation_catches_bad_cash_reserve(self):
        """校验能发现下限顺序错误"""
        bad = {
            "version": 1.2, "position_tiers": {"explore": .03, "watch": .05, "verify": .08, "core": .15},
            "risk_limits": {"single_fund_max": .15, "sector_max": .2,
                            "theme_cluster_max": .3, "cash_floor": .1},
            "cash_reserve": {"enabled": True, "base_floor": 0.10,
                             "l1_floor": 0.02, "l2_floor": 0.05, "l3_floor": 0.0},  # L1 < L2 错误
            "trend_gate": {}, "rsi": {}, "divergence": {}, "panic": {},
            "structural_stop": {}, "rebalance": {}, "cadence": {},
        }
        warnings = validate_rules(bad)
        self.assertTrue(any("逐档递减" in w for w in warnings))
        self.assertTrue(any("return_deadline_days" in w for w in warnings))

    def test_risk_limits_and_modes(self):
        rules = load_rules(RULES_PATH)
        limits = rules["risk_limits"]
        self.assertEqual(limits["cash_floor"], 0.10)
        self.assertEqual(limits["single_fund_max"], 0.15)
        self.assertEqual(limits["sector_max"], 0.20)
        self.assertEqual(limits["theme_cluster_max"], 0.30)
        # v1.1：只有 cash_floor 是 hard，其余是参考线
        self.assertEqual(limits["mode"]["cash_floor"], "hard")
        self.assertEqual(limits["mode"]["single_fund_max"], "reference")
        self.assertEqual(limits["mode"]["sector_max"], "reference")
        self.assertEqual(limits["mode"]["theme_cluster_max"], "reference")

    def test_trend_gate_is_default_filter(self):
        rules = load_rules(RULES_PATH)
        self.assertEqual(rules["trend_gate"]["type"], "default-filter")
        self.assertTrue(rules["trend_gate"]["three_tier"])

    def test_rsi_is_signal_input_only(self):
        rules = load_rules(RULES_PATH)
        self.assertEqual(rules["rsi"]["role"], "signal-input-only")

    def test_divergence_six_classes_auto_only_thesis(self):
        rules = load_rules(RULES_PATH)
        self.assertEqual(len(rules["divergence"]["classes"]), 6)
        self.assertEqual(rules["divergence"]["auto_execute_only"], "thesis-invalidation")

    def test_validate_real_file_no_warnings(self):
        rules = load_rules(RULES_PATH)
        self.assertEqual(validate_rules(rules), [])


if __name__ == "__main__":
    unittest.main()
