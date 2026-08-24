"""fund_nav_fetcher 回归测试：重复更新净值不得重复计算当日收益。"""

import unittest

from fund_nav_fetcher import update_portfolio_nav
from market_data import OfficialNAV


class _FakeNavService:
    def __init__(self, navs):
        self._navs = navs

    def get_official_navs(self, codes, force=True):
        return {c: self._navs.get(c) for c in codes}


def _pf():
    return {
        "cash": 0.0,
        "total_assets": 1000.0,
        "holdings": [
            {
                "fund_code": "019633",
                "fund_name": "测试基金",
                "sector": "半导体设备",
                "dashboard_id": "019633",
                "amount": 1000.0,
                "shares": 100.0,
                "cost_basis": 900.0,
                "nav": 10.0,
                "nav_date": "2026-08-20",
                "status": "active",
            }
        ],
        "action_log": [],
        "pending_plans": [],
    }


class TestUpdatePortfolioNavIdempotent(unittest.TestCase):
    def test_repeat_run_does_not_double_count_daily_return(self):
        svc = _FakeNavService(
            {"019633": OfficialNAV(nav=10.5, nav_date="2026-08-21", nav_return=5.0, status="official")}
        )
        pf = update_portfolio_nav(_pf(), nav_service=svc)
        h = pf["holdings"][0]
        self.assertEqual(h["daily_return"], 50.0)   # 1000 × 5%
        self.assertEqual(h["amount"], 1050.0)        # 100 × 10.5

        # 第二次运行（同一净值日、同一净值）不得再按 1050 计一次收益
        pf2 = update_portfolio_nav(pf, nav_service=svc)
        h2 = pf2["holdings"][0]
        self.assertEqual(h2["daily_return"], 50.0)
        self.assertEqual(h2["amount"], 1050.0)

    def test_new_nav_date_still_updates_daily_return(self):
        svc = _FakeNavService(
            {"019633": OfficialNAV(nav=10.5, nav_date="2026-08-21", nav_return=5.0, status="official")}
        )
        pf = update_portfolio_nav(_pf(), nav_service=svc)
        svc2 = _FakeNavService(
            {"019633": OfficialNAV(nav=11.0, nav_date="2026-08-22", nav_return=4.76, status="official")}
        )
        pf2 = update_portfolio_nav(pf, nav_service=svc2)
        h2 = pf2["holdings"][0]
        self.assertAlmostEqual(h2["daily_return"], 1050.0 * 4.76 / 100, places=2)
        self.assertEqual(h2["nav_date"], "2026-08-22")


if __name__ == "__main__":
    unittest.main()
