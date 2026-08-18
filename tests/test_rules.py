import os
import unittest

from rules import load_rules, validate_rules


RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules.yaml")


class TestRulesLoader(unittest.TestCase):
    def test_loads_required_structure(self):
        rules = load_rules(RULES_PATH)
        self.assertEqual(rules["version"], 1.1)
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
