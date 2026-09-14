"""分层现金储备测试：层级判定、数据缺失保守回退、归还规则（v1.2）。"""

import unittest
from datetime import date, timedelta

from cash_reserve import (
    TIER_ORDER,
    check_return,
    evaluate_tier,
    next_tier_hint,
    resolve_floor_pct,
    start_deployment,
)


def _sectors(n, value, others=2, other_value=50.0):
    """构造 n 个板块取 value、others 个板块取 other_value 的 RSI 字典。"""
    d = {f"S{i}": value for i in range(n)}
    d.update({f"O{i}": other_value for i in range(others)})
    return d


class TestEvaluateTier(unittest.TestCase):
    def test_l0_when_no_condition_met(self):
        r = evaluate_tier(sector_rsi=_sectors(0, 0, 6, 45.0),
                          sector_dev_ma50={"A": -5.0, "B": -3.0},
                          index_drop_20d=-1.0)
        self.assertEqual(r["tier"], "L0")
        self.assertEqual(r["floor_pct"], 10.0)
        self.assertFalse(r["deployment_allowed"])

    def test_l1_four_sectors_rsi20(self):
        """≥4 板块 RSI≤20 → L1（现金下限 7%）"""
        r = evaluate_tier(sector_rsi=_sectors(4, 18.0, 2, 50.0),
                          sector_dev_ma50={"A": -12.0},
                          index_drop_20d=-5.0)
        self.assertEqual(r["tier"], "L1")
        self.assertEqual(r["floor_pct"], 7.0)
        self.assertTrue(r["deployment_allowed"])

    def test_l1_not_triggered_with_three_sectors(self):
        """只有 3 个板块超卖 → 不触发（阈值 4 个）"""
        r = evaluate_tier(sector_rsi=_sectors(3, 18.0, 3, 50.0), index_drop_20d=-5.0)
        self.assertEqual(r["tier"], "L0")

    def test_l2_requires_index_drop_too(self):
        """≥4 板块 RSI≤30 但大盘 20 日未跌够 → 不触发 L2"""
        r = evaluate_tier(sector_rsi=_sectors(4, 28.0, 2, 55.0), index_drop_20d=-3.0)
        self.assertEqual(r["tier"], "L0")

    def test_l2_triggered(self):
        """≥4 板块 RSI≤30 且大盘 20 日 ≤-8% → L2（现金下限 4%）"""
        r = evaluate_tier(sector_rsi=_sectors(4, 28.0, 2, 55.0), index_drop_20d=-9.0)
        self.assertEqual(r["tier"], "L2")
        self.assertEqual(r["floor_pct"], 4.0)

    def test_l3_triggered_by_ma50_deviation(self):
        """≥4 板块偏离 MA50 ≤-20% → L3（允许归零）"""
        r = evaluate_tier(
            sector_rsi=_sectors(4, 35.0, 2, 50.0),
            sector_dev_ma50={"A": -22.0, "B": -25.0, "C": -21.0, "D": -30.0, "E": -5.0},
            index_drop_20d=-6.0,
        )
        self.assertEqual(r["tier"], "L3")
        self.assertEqual(r["floor_pct"], 0.0)

    def test_strictest_tier_wins(self):
        """同时满足 L1 与 L3 → 取更严的 L3"""
        r = evaluate_tier(
            sector_rsi=_sectors(4, 15.0, 2, 50.0),          # 满足 L1
            sector_dev_ma50={"A": -21.0, "B": -23.0, "C": -26.0, "D": -30.0},  # 满足 L3
            index_drop_20d=-12.0,                            # 满足 L2
        )
        self.assertEqual(r["tier"], "L3")
        self.assertEqual(r["floor_pct"], 0.0)

    def test_missing_data_is_conservative(self):
        """数据缺失 → 条件视为未满足（保守，不利动用储备）+ data_ok=False"""
        r = evaluate_tier(sector_rsi=None, sector_dev_ma50=None, index_drop_20d=None)
        self.assertEqual(r["tier"], "L0")
        self.assertEqual(r["floor_pct"], 10.0)
        self.assertFalse(r["data_ok"])

    def test_disabled_falls_back_to_base_floor(self):
        """分层储备关闭 → 固定基础下限"""
        cfg = {"enabled": False, "base_floor_pct": 10.0, "tiers": []}
        r = evaluate_tier(sector_rsi=_sectors(6, 10.0), config=cfg)
        self.assertEqual(r["tier"], "L0")
        self.assertEqual(r["floor_pct"], 10.0)
        self.assertFalse(r["deployment_allowed"])

    def test_resolve_floor_pct_shortcut(self):
        self.assertEqual(resolve_floor_pct(sector_rsi=_sectors(4, 18.0)), 7.0)
        self.assertEqual(resolve_floor_pct(sector_rsi=_sectors(0, 0, 5, 60.0)), 10.0)


class TestNextTierHint(unittest.TestCase):
    def test_hint_from_l0_points_to_l1(self):
        result = evaluate_tier(sector_rsi=_sectors(1, 18.0, 5, 50.0), index_drop_20d=-1.0)
        hint = next_tier_hint(result, sector_rsi=_sectors(1, 18.0, 5, 50.0), index_drop_20d=-1.0)
        self.assertIsNotNone(hint)
        self.assertIn("L1", hint)
        self.assertIn("7.0", hint)
        self.assertIn("现 1 个", hint)

    def test_no_hint_at_top_tier(self):
        r = evaluate_tier(sector_dev_ma50={"A": -21.0, "B": -22.0, "C": -23.0, "D": -24.0})
        self.assertEqual(r["tier"], "L3")
        self.assertIsNone(next_tier_hint(r))


class TestReturnRules(unittest.TestCase):
    def test_start_deployment_records_state(self):
        st = start_deployment("L1", 3000, today=date(2026, 9, 14))
        self.assertEqual(st["tier"], "L1")
        self.assertEqual(st["floor_pct"], 7.0)
        self.assertEqual(st["deployed_amount"], 3000)
        self.assertFalse(st["returned"])
        self.assertIn("deadline_date", st)

    def test_return_needed_after_exit_condition(self):
        """退出触发区间 → 需要归还（不看盈亏）"""
        st = start_deployment("L1", 3000, today=date(2026, 9, 1))
        now = date(2026, 9, 10)
        # 当前已回落到 L0（退出 L1 区间）
        result = evaluate_tier(sector_rsi=_sectors(0, 0, 5, 60.0), index_drop_20d=0.0)
        r = check_return(st, result, today=now)
        self.assertTrue(r["needed"])
        self.assertEqual(r["reason"], "exit-condition")
        self.assertEqual(r["outstanding"], 3000)

    def test_return_not_needed_while_still_in_range(self):
        st = start_deployment("L1", 3000, today=date(2026, 9, 1))
        result = evaluate_tier(sector_rsi=_sectors(4, 18.0, 2, 50.0))
        r = check_return(st, result, today=date(2026, 9, 5))
        self.assertFalse(r["needed"])

    def test_return_forced_after_deadline(self):
        """超过期限 → 强制归还 + 止损提醒"""
        st = start_deployment("L1", 3000, today=date(2026, 1, 1))
        result = evaluate_tier(sector_rsi=_sectors(4, 18.0, 2, 50.0))  # 仍在区间内
        r = check_return(st, result, today=date(2026, 3, 1))
        self.assertTrue(r["needed"])
        self.assertEqual(r["reason"], "deadline")
        self.assertIn("止损", r["message"])

    def test_return_not_needed_when_fully_returned(self):
        st = start_deployment("L1", 3000, today=date(2026, 1, 1))
        st["returned_amount"] = 3000
        r = check_return(st, evaluate_tier(), today=date(2026, 3, 1))
        self.assertFalse(r["needed"])

    def test_tier_order_is_monotonic(self):
        self.assertEqual(TIER_ORDER, ["L0", "L1", "L2", "L3"])


if __name__ == "__main__":
    unittest.main()
