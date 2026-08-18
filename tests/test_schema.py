"""portfolio.json schema 校验测试（v1.1：status=生命周期，evidence_stage=档位）。"""

import unittest

from portfolio_schema import validate_portfolio


def _pf(**overrides):
    pf = {
        "holdings": [
            {
                "fund_code": "019633",
                "amount": 10000,
                "status": "active",
                "tier": "verify",
                "evidence_stage": "verify",
            }
        ],
        "cash": 5000,
        "total_assets": 15000,
    }
    pf.update(overrides)
    return pf


class TestPortfolioSchema(unittest.TestCase):
    def test_normalized_portfolio_passes(self):
        self.assertEqual(validate_portfolio(_pf()), [])

    def test_legacy_status_core_is_flagged(self):
        w = validate_portfolio(_pf(holdings=[{
            "fund_code": "019633",
            "amount": 10000,
            "status": "core",  # 旧生命周期混档位值，迁移后应报错
        }]))
        self.assertTrue(any("status" in x and "允许集合" in x for x in w), w)

    def test_legacy_tier_overweight_is_flagged(self):
        w = validate_portfolio(_pf(holdings=[{
            "fund_code": "019633",
            "amount": 10000,
            "status": "active",
            "tier": "overweight",  # 旧超限标记，迁移后应报错
            "evidence_stage": "core",
        }]))
        self.assertTrue(any("tier" in x and "允许集合" in x for x in w), w)

    def test_observe_status_allowed(self):
        pf = _pf(holdings=[{
            "fund_code": "019633",
            "amount": 0,
            "status": "observe",  # v1.1：证伪 Exit 后观察期
            "tier": "",
            "evidence_stage": "",
        }])
        self.assertEqual(validate_portfolio(pf), [])


if __name__ == "__main__":
    unittest.main()
