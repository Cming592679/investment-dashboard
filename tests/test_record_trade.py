"""record_trade 回归测试：卖出必须按剩余份额折算 cost_basis。"""

import unittest

from record_trade import record_trade


def _pf():
    return {
        "cash": 5000.0,
        "total_assets": 20000.0,
        "holdings": [
            {
                "fund_code": "020608",
                "fund_name": "南方中证机器人ETF联接 C",
                "sector": "机器人",
                "dashboard_id": "020608",
                "amount": 1381.89,      # 973.16 × 1.42
                "shares": 973.16,
                "cost_basis": 1702.16,
                "status": "active",
            }
        ],
        "action_log": [],
        "pending_plans": [],
    }


class TestRecordTradeSell(unittest.TestCase):
    def test_sell_by_shares_reduces_cost_basis(self):
        pf = _pf()
        pf = record_trade(pf, "sell", "020608", 965.7, "机器人减仓", unit="shares", nav=1.42)
        h = pf["holdings"][0]
        self.assertAlmostEqual(h["shares"], 7.46, places=2)
        # 剩余成本 = 剩余份额 × (原成本/原份额) ≈ 13.05，而不是保留全仓成本 1702.16
        self.assertAlmostEqual(h["cost_basis"], 7.46 * (1702.16 / 973.16), places=2)
        self.assertLess(h["cost_basis"], 20.0)
        # 现金收到卖出款
        self.assertAlmostEqual(pf["cash"], 5000.0 + 965.7 * 1.42, places=2)

    def test_sell_all_shares_leaves_zero_cost(self):
        pf = _pf()
        pf = record_trade(pf, "sell", "020608", 973.16, "清仓", unit="shares", nav=1.42)
        h = pf["holdings"][0]
        self.assertAlmostEqual(h["shares"], 0.0, places=2)
        self.assertAlmostEqual(h["cost_basis"], 0.0, places=2)


if __name__ == "__main__":
    unittest.main()
