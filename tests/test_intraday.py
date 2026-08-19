"""intraday_check 计划检查测试：事件过期后应引用 KEY_DATES 结果而非永远提示跟进。"""

import unittest
from datetime import date
from unittest.mock import patch

import config
from intraday_check import check_plan


SMIC_PLAN = {
    "module": "半导体设备",
    "direction": "buy",
    "action_if_triggered": "中芯国际Q2 超预期，可考虑加仓",
    "action_if_not": "等确认",
    "note": "SMIC Q2 8/15",
}


class TestSmicPlanAfterEvent(unittest.TestCase):
    def test_smic_plan_shows_followed_up_when_result_exists(self):
        with patch("intraday_check.get_dashboard_data", return_value={}):
            status = check_plan(SMIC_PLAN, {"holdings": []})
        self.assertIn("已跟进", status)
        self.assertNotIn("请跟进结果", status)

    def test_smic_plan_reminds_when_no_result_yet(self):
        no_result_events = [
            {"date": date(2026, 8, 15), "event": "中芯国际 Q2 财报 ⚠", "importance": "critical"},
        ]
        with patch.dict(config.KEY_DATES, {"019633": no_result_events}), \
             patch("intraday_check.get_dashboard_data", return_value={}):
            status = check_plan(SMIC_PLAN, {"holdings": []})
        self.assertIn("请跟进结果", status)


if __name__ == "__main__":
    unittest.main()
