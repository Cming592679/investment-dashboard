"""决策树分支测试：用合成行情数据验证各分支结论（P0-2 漏判修复回归）。"""

import unittest
from unittest.mock import patch

import app


def _stock(name="X", rsi=50.0, above_ma50=True, chg=0.0):
    return {"name": name, "rsi": rsi, "above_ma50": above_ma50, "day_change_pct": chg}


def _three_stocks(rsi=50.0, above=True, chg=0.0):
    return {f"S{i}": _stock(f"S{i}", rsi=rsi, above_ma50=above, chg=chg) for i in range(3)}


class TestDecisionTree(unittest.TestCase):
    def setUp(self):
        self.fund = app.FUNDS["019633"]

    def _assess(self, leading, stage, stocks, indices=None, specials=None):
        with patch.dict(app.LEADING_INDICATORS, {"TEST": leading}), \
             patch.dict(app.CYCLE_ASSESSMENTS, {"TEST": {"stage": stage}}):
            return app.compute_assessment(
                self.fund, stocks, indices or {}, specials or {}, fund_id="TEST"
            )

    def test_branch2_fundamental_and_technical_kill(self):
        """领先转空 + 暴跌 + MA50 破位 → 考虑跑路"""
        a = self._assess(
            leading={},
            stage="mid",
            stocks=_three_stocks(above=False, chg=-9.0),
            indices={"I1": {"above_ma50": False}},
        )
        self.assertEqual(a["conclusion"], "考虑跑路")
        self.assertEqual(a["emoji"], "🔴")

    def test_branch35_mid_late_crash_with_broken_trend_is_observe(self):
        """非早期暴跌 + 破位但基本面完好 → 忍着不动（P0-2 回归：不得落到安心持有）"""
        a = self._assess(
            leading={"A": {"trend": "up"}},
            stage="mid",
            stocks=_three_stocks(above=False, chg=-9.0),
            indices={"I1": {"above_ma50": False}},
        )
        self.assertEqual(a["conclusion"], "忍着不动")
        self.assertEqual(a["emoji"], "🟡")
        self.assertNotEqual(a["conclusion"], "安心持有")

    def test_branch4_early_deep_oversold_is_add_candidate(self):
        """周期早期 + 基本面完好 + 深度超卖 → 关注加仓"""
        a = self._assess(
            leading={"A": {"trend": "up"}},
            stage="early",
            stocks=_three_stocks(rsi=20.0),
        )
        self.assertEqual(a["conclusion"], "关注加仓")
        self.assertEqual(a["emoji"], "🟢")

    def test_branch5_early_healthy_is_hold(self):
        """周期早期 + 基本面完好 + 趋势完好 → 安心持有"""
        a = self._assess(
            leading={"A": {"trend": "up"}},
            stage="early",
            stocks=_three_stocks(rsi=50.0),
            indices={"I1": {"above_ma50": True}},
        )
        self.assertEqual(a["conclusion"], "安心持有")

    def test_branch6_late_broad_overbought_is_warning(self):
        """中后期 + RSI 极端超买 → 高位警惕"""
        stocks = {f"S{i}": _stock(f"S{i}", rsi=80.0) for i in range(5)}
        a = self._assess(leading={}, stage="late", stocks=stocks)
        self.assertEqual(a["conclusion"], "高位警惕")
        self.assertEqual(a["emoji"], "🔴")

    def test_branch8_neutral_is_hold(self):
        """无明确信号 → 忍着不动"""
        a = self._assess(
            leading={},
            stage="",
            stocks=_three_stocks(rsi=50.0),
            indices={"I1": {"above_ma50": True}},
        )
        self.assertEqual(a["conclusion"], "忍着不动")


class TestActionPlanBuild(unittest.TestCase):
    """回归：_build_action_plan 必须产出完整字段（防止 fundamental_state 字段改名后漏改）。"""

    def test_build_action_plan_has_all_fields(self):
        pf = {
            "total_assets": 100000,
            "holdings": [
                {
                    "fund_code": "019633",
                    "dashboard_id": "019633",
                    "fund_name": "国泰半导体设备ETF联接C",
                    "sector": "半导体",
                    "amount": 10000,
                    "evidence_stage": "verify",
                }
            ],
        }
        dash_cache = {
            "019633": {
                "data": {
                    "assessment": {"conclusion": "安心持有", "emoji": "🟢"},
                    "leading_indicators": {},
                    "fund_return_pct": 0.5,
                }
            }
        }
        action_result = {
            "buy_signals": [],
            "sell_profit": [],
            "sell_stop": [],
            "conflicts_resolved": [],
        }
        plan = app._build_action_plan(pf, dash_cache, action_result)
        self.assertEqual(len(plan), 1)
        p = plan[0]
        for key in (
            "fund_id",
            "fundamental",
            "fundamental_msg",
            "action",
            "divergence",
            "tier_cap_pct",
            "needs_confirm",
        ):
            self.assertIn(key, p)
        self.assertEqual(p["action"], "hold")
        self.assertEqual(p["fundamental"], "ok")
        self.assertEqual(p["divergence"], "—")


if __name__ == "__main__":
    unittest.main()
