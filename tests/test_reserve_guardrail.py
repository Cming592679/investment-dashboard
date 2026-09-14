"""买入校验 + 储备动用登记（record_trade 与 cash_reserve 的集成）。"""

import unittest
from unittest.mock import patch

from record_trade import record_trade


def _pf(cash=8000.0, total=60000.0, amount=4567.32):
    return {
        "cash": cash,
        "total_assets": total,
        "holdings": [
            {
                "fund_code": "025209",
                "fund_name": "永赢先锋半导体智选混 C",
                "sector": "存储芯片(A股)",
                "theme": "半导体",
                "amount": amount,
                "shares": 1970.71,
                "cost_basis": 4456.01,
                "nav": 2.3176,
                "status": "active",
            }
        ],
        "action_log": [],
        "pending_plans": [],
    }


def _tier(tier_id, floor_pct, allowed):
    return {
        "tier": tier_id, "floor_pct": floor_pct, "label": f"{tier_id} 层",
        "matched": [f"{tier_id} 触发条件"], "checks": [], "data_ok": True,
        "deployment_allowed": allowed,
    }


class TestReserveGuardrail(unittest.TestCase):
    def test_l0_blocks_buy_breaking_base_floor(self):
        """L0：买入后现金低于 10% → 拒绝，并提示距下一档还差什么"""
        with patch("record_trade.fetch_reserve_state", return_value=_tier("L0", 10.0, False)):
            with self.assertRaises(ValueError) as ctx:
                # cash 8000 - 2500 = 5500 < 6000（总资产 60000 的 10%）
                record_trade(_pf(), "buy", "025209", 2500, "测试")
        msg = str(ctx.exception)
        self.assertIn("10% 下限", msg)
        self.assertIn("v1.2 分层储备", msg)

    def test_l1_allows_buy_below_base_floor_and_registers_deployment(self):
        """L1：允许现金降至 7%，并在买入后登记储备动用（供归还检查）"""
        pf = _pf()  # cash 8000, total 60000 → 10% = 6000, 7% = 4200
        with patch("record_trade.fetch_reserve_state", return_value=_tier("L1", 7.0, True)):
            record_trade(pf, "buy", "025209", 3000, "L1 动用测试")
        self.assertAlmostEqual(pf["cash"], 5000.0, places=2)   # 5000 < 6000 但 > 4200
        self.assertIn("cash_reserve", pf)
        self.assertEqual(pf["cash_reserve"]["tier"], "L1")
        self.assertEqual(pf["cash_reserve"]["floor_pct"], 7.0)
        self.assertAlmostEqual(pf["cash_reserve"]["deployed_amount"], 3000.0, places=2)
        self.assertFalse(pf["cash_reserve"]["returned"])
        # 动用要留痕（action_log 记录可用层级与归还纪律）
        actions = " ".join(e.get("action", "") for e in pf["action_log"])
        self.assertIn("动用储备", actions)

    def test_l1_still_blocks_buy_breaking_its_own_floor(self):
        """即使 L1 放宽到 7%，跌破 7% 仍拒绝"""
        with patch("record_trade.fetch_reserve_state", return_value=_tier("L1", 7.0, True)):
            with self.assertRaises(ValueError) as ctx:
                record_trade(_pf(), "buy", "025209", 4000, "测试")  # 8000-4000=4000 < 4200
        self.assertIn("7% 下限", str(ctx.exception))

    def test_explicit_floor_override_skips_service(self):
        """显式传入 cash_floor_pct 时不查询服务（便于测试/离线使用）"""
        pf = _pf()
        record_trade(pf, "buy", "025209", 3000, "显式下限", cash_floor_pct=5.0)
        self.assertAlmostEqual(pf["cash"], 5000.0, places=2)

    def test_no_deployment_when_cash_stays_above_base_floor(self):
        """L1 虽放开，但买入后现金仍在 10% 以上 → 不登记动用"""
        pf = _pf(cash=20000.0)
        with patch("record_trade.fetch_reserve_state", return_value=_tier("L1", 7.0, True)):
            record_trade(pf, "buy", "025209", 3000, "未触及基础下限")
        self.assertNotIn("cash_reserve", pf)


if __name__ == "__main__":
    unittest.main()
