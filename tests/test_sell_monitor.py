"""卖出监控纯函数测试：A/B/D/再平衡四轨状态与距离计算。"""

import unittest

from sell_monitor import build_sell_monitor


def _holding(code="019633", fid="019633", sector="半导体设备", stage_evidence="verify",
             amount=10000.0, ret=0.4, theme=None):
    h = {
        "fund_code": code,
        "dashboard_id": fid,
        "fund_name": f"基金{code}",
        "sector": sector,
        "amount": amount,
        "holding_return_pct": ret,
        "evidence_stage": stage_evidence,
    }
    if theme:
        h["theme"] = theme
    return h


def _exposure(sector_pct=15.6, cluster_pct=20.0, sector_name="半导体设备"):
    return {
        "sectors": [{"name": sector_name, "pct": sector_pct, "limit": 20.0}],
        "themes": [],
        "clusters": [{"label": "HBM 内存三寡头", "pct": cluster_pct, "limit": 30.0}],
    }


class TestDistances(unittest.TestCase):
    def test_negative_return_mid_tiers(self):
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [
                _holding(code="015789", fid="015789", sector="军工电子", ret=-15.4)]},
            action_result={"sell_profit": [], "sell_stop": []},
            exposure=_exposure(sector_pct=25.0),
        )
        h = m["holdings"][0]
        self.assertEqual(h["stage"], "mid")
        # mid 档位 20/30/45：从 -15.4% 到各档分别需 +41.8%/+53.7%/+71.4%
        self.assertAlmostEqual(h["distances"][0], 41.8, places=1)
        self.assertAlmostEqual(h["distances"][1], 53.7, places=1)
        self.assertAlmostEqual(h["distances"][2], 71.4, places=1)
        self.assertEqual(h["tier_hit"], -1)
        self.assertIn("A轨够不着", h["note"])

    def test_positive_return_early_tiers(self):
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [
                _holding(ret=6.81)]},
            action_result={"sell_profit": [], "sell_stop": []},
            exposure=_exposure(),
        )
        h = m["holdings"][0]
        self.assertEqual(h["stage"], "early")
        self.assertAlmostEqual(h["distances"][0], 17.0, places=1)
        self.assertAlmostEqual(h["distances"][1], 31.1, places=1)
        self.assertAlmostEqual(h["distances"][2], 49.8, places=1)
        self.assertEqual(h["tier_hit"], -1)
        self.assertEqual(h["note"], "")

    def test_tier_hit(self):
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [_holding(ret=26.0)]},
            action_result={"sell_profit": [], "sell_stop": []},
            exposure=_exposure(),
        )
        h = m["holdings"][0]
        self.assertEqual(h["tier_hit"], 0)
        self.assertTrue(h["a_active"])
        self.assertIn("一档", h["a_status"])


class TestTracks(unittest.TestCase):
    def test_d_track_and_priority_note(self):
        action_result = {
            "sell_profit": [],
            "sell_stop": [{
                "fund_id": "019633", "track": "D-领先指标恶化",
                "sell_pct": 30, "reason": "≥2个领先指标转down → 减30%",
            }],
        }
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [_holding()]},
            action_result=action_result,
            exposure=_exposure(),
        )
        h = m["holdings"][0]
        self.assertTrue(h["d_active"])
        self.assertTrue(h["d_status"].startswith("D-领先指标恶化"))
        self.assertIn("D-逻辑止损", h["exit_paths"])
        self.assertIn("优先", h["note"])

    def test_b_track_mapped(self):
        action_result = {
            "sell_profit": [{
                "fund_id": "019633", "track": "B-技术过热(RSI+KDJ)",
                "sell_pct": 15, "reason": "RSI+KDJ 双热",
            }],
            "sell_stop": [],
        }
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [_holding(ret=26.0)]},
            action_result=action_result,
            exposure=_exposure(),
        )
        h = m["holdings"][0]
        self.assertTrue(h["b_active"])
        self.assertIn("B-技术过热", h["b_status"])
        self.assertIn("B-技术过热", h["exit_paths"])


class TestRebalance(unittest.TestCase):
    def test_sector_over_reference(self):
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [
                _holding(sector="军工电子", ret=-15.4)]},
            action_result={"sell_profit": [], "sell_stop": []},
            exposure=_exposure(sector_pct=25.0, sector_name="军工电子"),
        )
        h = m["holdings"][0]
        self.assertTrue(h["over_reference"])
        self.assertTrue(any("板块" in o for o in h["over_lines"]))
        self.assertIn("再平衡(超参考线)", h["exit_paths"])
        self.assertEqual(m["summary"]["over_reference"], 1)

    def test_tier_cap_over(self):
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [
                _holding(amount=20000.0, ret=0.0, stage_evidence="verify")]},
            action_result={"sell_profit": [], "sell_stop": []},
            exposure=_exposure(),
        )
        h = m["holdings"][0]
        self.assertTrue(any("档位上限" in o for o in h["over_lines"]))

    def test_near_first_tier_count(self):
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": [_holding(ret=12.0)]},
            action_result={"sell_profit": [], "sell_stop": []},
            exposure=_exposure(),
        )
        self.assertEqual(m["summary"]["near_first_tier"], 1)

    def test_empty_holdings(self):
        m = build_sell_monitor(
            {"total_assets": 100000, "holdings": []},
            action_result={"sell_profit": [], "sell_stop": []},
            exposure=_exposure(),
        )
        self.assertEqual(m["holdings"], [])
        self.assertEqual(m["summary"]["over_reference"], 0)


if __name__ == "__main__":
    unittest.main()
