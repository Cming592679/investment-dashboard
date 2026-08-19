"""MarketDataService 测试（P0-0 修复专项，13 项验收场景）。"""

import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch

from market_data import (
    MarketDataService,
    IntradayQuote,
    STATUS_ESTIMATED,
    STATUS_OFFICIAL,
    STATUS_UNAVAILABLE,
    STATUS_ERROR,
)
from fund_nav_fetcher import update_portfolio_nav


def sina_fund_body(code="019633", nav="3.0815", prev="2.9386", nav_date="2026-08-17"):
    return f'var hq_str_f_{code}="国泰,{nav},0,{prev},{nav_date},6.3154";'


def sina_batch_body(codes_navs):
    return "\n".join(
        f'var hq_str_f_{c}="X,{n},0,{p},{d},6.0";'
        for c, n, p, d in codes_navs
    )


def em_nav_body(nav="3.0815", nav_date="2026-08-17", chg="4.86"):
    return (
        '{"Datas":[{"FCODE":"019633","PDATE":"%s","NAV":"%s","NAVCHGRT":"%s"}],'
        '"ErrCode":0,"Success":true}' % (nav_date, nav, chg)
    )


def apizero_ok_body(chg="1.20", est="3.0"):
    return json.dumps({
        "code": 0,
        "data": {"change_rate": chg, "estimate": est, "update_time": "2026-08-18T10:00:00"},
    })


def sina_quote_body(cur="1.262", prev="1.263", quote_date="2026-08-18", quote_time="10:15:00"):
    parts = ["芯片ETF", "1.25", prev, cur, "1.27", "1.24"] + [""] * 24 + [quote_date, quote_time, "00"]
    return 'var hq_str_sz159995="' + ",".join(parts) + '";'


def fake_http(responder):
    """responder(url) -> (ok, body)"""
    def http_get(url, headers=None, decode="utf-8", timeout=10.0):
        return responder(url)
    return http_get


class TestOfficialNAV(unittest.TestCase):
    def test_1_official_nav_normal_update(self):
        svc = MarketDataService(
            http_get=fake_http(lambda u: (True, sina_fund_body()) if "hq.sinajs.cn" in u else (False, None)),
            now=lambda: datetime(2026, 8, 18, 10, 0, 0),
        )
        nav = svc.get_official_nav("019633", force=True)
        self.assertEqual(nav.status, STATUS_OFFICIAL)
        self.assertEqual(nav.nav, 3.0815)
        self.assertEqual(nav.nav_date, "2026-08-17")
        self.assertEqual(nav.nav_return, 4.86)
        self.assertEqual(nav.source, "sina")

    def test_2_late_disclosure_retry(self):
        """晚披露：第一次拿到旧日期，重试后拿到新日期 → nav_date 推进。"""
        calls = {"n": 0}
        def responder(url):
            if "hq.sinajs.cn" in url:
                if "list=f_" in url or "list=f" in url:
                    calls["n"] += 1
                    if calls["n"] == 1:
                        return True, sina_batch_body([("019633", "2.9386", "2.8511", "2026-08-14")])
                    return True, sina_batch_body([("019633", "3.0815", "2.9386", "2026-08-17")])
            return False, None

        svc = MarketDataService(http_get=fake_http(responder))
        pf = {"cash": 10000, "holdings": [
            {"fund_code": "019633", "fund_name": "X", "amount": 10000, "status": "active", "sector": "S"},
        ]}
        pf = update_portfolio_nav(pf, nav_service=svc)
        self.assertEqual(pf["holdings"][0]["nav_date"], "2026-08-14")
        self.assertEqual(pf["holdings"][0]["nav_status"], "official")
        pf = update_portfolio_nav(pf, nav_service=svc)
        self.assertEqual(pf["holdings"][0]["nav_date"], "2026-08-17")
        self.assertEqual(pf["holdings"][0]["nav"], 3.0815)
        self.assertEqual(pf["holdings"][0]["nav_return"], 4.86)

    def test_3_primary_fails_fallback_succeeds(self):
        def responder(url):
            if "fundmobapi.eastmoney.com" in url:
                return True, em_nav_body()
            return False, None  # 新浪失败
        svc = MarketDataService(http_get=fake_http(responder))
        nav = svc.get_official_nav("019633", force=True)
        self.assertEqual(nav.status, STATUS_OFFICIAL)
        self.assertEqual(nav.source, "eastmoney")
        self.assertEqual(nav.nav_date, "2026-08-17")

    def test_4_both_fail_no_fabrication(self):
        svc = MarketDataService(http_get=fake_http(lambda u: (False, None)))
        nav = svc.get_official_nav("019633", force=True)
        self.assertIn(nav.status, (STATUS_UNAVAILABLE, STATUS_ERROR))
        self.assertIsNone(nav.nav)
        self.assertIsNone(nav.nav_date)


class TestIntraday(unittest.TestCase):
    def test_5_intraday_normal_proxy(self):
        svc = MarketDataService(
            http_get=fake_http(lambda u: (True, sina_quote_body()) if "hq.sinajs.cn" in u else (False, None)),
            now=lambda: datetime(2026, 8, 18, 10, 16, 0),
        )
        q = svc.get_intraday("019633", market="a", proxy_symbol="sz159995", force=True)
        self.assertEqual(q.status, STATUS_ESTIMATED)
        self.assertEqual(q.method, "proxy_index")
        self.assertAlmostEqual(q.intraday_change_pct, round((1.262 - 1.263) / 1.263 * 100, 2))
        self.assertIn("2026-08-18T10:15", q.quote_time)

    def test_6_intraday_source_down_no_fallback_to_nav(self):
        svc = MarketDataService(http_get=fake_http(lambda u: (False, None)), now=lambda: datetime(2026, 8, 18, 10, 16, 0))
        q = svc.get_intraday("019633", market="a", proxy_symbol="sz159995", force=True)
        self.assertEqual(q.status, STATUS_UNAVAILABLE)
        self.assertIsNone(q.intraday_change_pct)
        # 绝不回退到官方净值收益
        self.assertNotEqual(q.intraday_change_pct, 4.86)

    def test_7_cache_stale(self):
        q = IntradayQuote(
            intraday_change_pct=1.0, quote_time="2026-08-18T10:00:00",
            status=STATUS_ESTIMATED,
        )
        self.assertEqual(MarketDataService.intraday_freshness(q, max_age_seconds=900), "stale")
        fresh_q = IntradayQuote(
            intraday_change_pct=1.0,
            quote_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            status=STATUS_ESTIMATED,
        )
        self.assertEqual(MarketDataService.intraday_freshness(fresh_q, max_age_seconds=900), "fresh")

    def test_9_qdii_unavailable(self):
        svc = MarketDataService(http_get=fake_http(lambda u: (True, sina_quote_body())))
        q = svc.get_intraday("100055", market="us", force=True)
        self.assertEqual(q.status, STATUS_UNAVAILABLE)
        self.assertIn("QDII", q.message)


class TestPortfolioReturn(unittest.TestCase):
    def test_8_no_mixing_different_nav_dates(self):
        def responder(url):
            if "hq.sinajs.cn" in url:
                return True, sina_batch_body([
                    ("019633", "3.0815", "2.9386", "2026-08-17"),   # 新
                    ("100055", "5.4292", "5.37", "2026-08-14"),     # 旧（QDII 延迟）
                ])
            return False, None
        svc = MarketDataService(http_get=fake_http(responder))
        pf = {"cash": 10000, "holdings": [
            {"fund_code": "019633", "amount": 10000, "status": "active", "sector": "S"},
            {"fund_code": "100055", "amount": 10000, "status": "active", "sector": "S"},
        ]}
        pf = update_portfolio_nav(pf, nav_service=svc)
        self.assertEqual(pf["official_return"]["nav_date"], "2026-08-17")
        self.assertEqual(pf["official_return"]["coverage"], "1/2")
        self.assertIn("100055", pf["official_return"]["stale_holdings"])
        # 组合日收益只含 8/17 那一只：10000 × 4.86%
        self.assertAlmostEqual(pf["daily_return"], 486.0, places=1)

    def test_13_latest_return_includes_all_active_with_own_dates(self):
        """最新披露合计按各自净值日加总（QDII 延迟不影响对账），同日合计保持不变。"""
        def responder(url):
            if "hq.sinajs.cn" in url:
                return True, sina_batch_body([
                    ("019633", "3.0815", "2.9386", "2026-08-17"),
                    ("100055", "5.4292", "5.37", "2026-08-14"),
                ])
            return False, None
        svc = MarketDataService(http_get=fake_http(responder))
        pf = {"cash": 10000, "holdings": [
            {"fund_code": "019633", "amount": 10000, "status": "active", "sector": "S"},
            {"fund_code": "100055", "amount": 10000, "status": "active", "sector": "S"},
        ]}
        pf = update_portfolio_nav(pf, nav_service=svc)

        lr = pf["latest_return"]
        # 8/17 +486.0，8/14 +110.0（10000 × 1.10%）
        self.assertAlmostEqual(lr["return"], 596.0, places=1)
        self.assertTrue(lr["mixed_dates"])
        self.assertEqual(lr["nav_dates"], ["2026-08-14", "2026-08-17"])
        self.assertEqual({h["fund_code"] for h in lr["holdings"]}, {"019633", "100055"})
        # 同日合计不受影响
        self.assertAlmostEqual(pf["daily_return"], 486.0, places=1)


class TestDataIntegrityGate(unittest.TestCase):
    def _plan(self, intraday_q):
        import app as app_module
        pf = {"total_assets": 100000, "holdings": [
            {"fund_code": "019633", "dashboard_id": "019633", "fund_name": "X",
             "sector": "半导体设备", "amount": 10000, "evidence_stage": "verify"},
        ]}
        dash_cache = {"019633": {"data": {
            "assessment": {"conclusion": "安心持有", "emoji": "🟢"},
            "leading_indicators": {},
            "fund_return_pct": 4.86,
            "fund_nav_date": "2026-08-17",
        }}}
        action_result = {
            "buy_signals": [{"fund_id": "019633", "reason": "技术买入"}],
            "sell_profit": [], "sell_stop": [], "conflicts_resolved": [],
        }
        with patch.object(app_module.md_service, "get_intraday", return_value=intraday_q):
            return app_module._build_action_plan(pf, dash_cache, action_result)

    def test_10_unavailable_blocks_divergence(self):
        plan = self._plan(IntradayQuote(status=STATUS_UNAVAILABLE, message="盘中数据不可用"))
        p = plan[0]
        self.assertTrue(p["price_signal_blocked"])
        self.assertIn("盘中市场数据不可用", p["divergence"])
        self.assertEqual(p["action"], "hold")  # buy 候选被阻断

    def test_11_recovery_restores_signal(self):
        plan = self._plan(IntradayQuote(
            intraday_change_pct=-4.0,
            quote_time=(datetime.now() - timedelta(seconds=30)).isoformat(timespec="seconds"),
            status=STATUS_ESTIMATED, freshness="fresh",
        ))
        p = plan[0]
        self.assertFalse(p["price_signal_blocked"])
        self.assertEqual(p["action"], "buy")
        self.assertIn("逆向吸入候选", p["divergence"])


class TestRestart(unittest.TestCase):
    def test_12_restart_re_fetches_fresh(self):
        svc1 = MarketDataService(http_get=fake_http(lambda u: (True, sina_quote_body())),
                                 now=lambda: datetime(2026, 8, 18, 10, 16, 0))
        q1 = svc1.get_intraday("019633", market="a", proxy_symbol="sz159995", force=True)
        # 模拟重启：新实例不继承旧缓存
        svc2 = MarketDataService(http_get=fake_http(lambda u: (True, sina_quote_body())),
                                 now=lambda: datetime(2026, 8, 18, 10, 17, 0))
        q2 = svc2.get_intraday("019633", market="a", proxy_symbol="sz159995", force=True)
        self.assertEqual(q2.status, STATUS_ESTIMATED)
        self.assertIsNotNone(q2.quote_time)
        self.assertEqual(q1.quote_time, q2.quote_time)


class TestApizeroQuota(unittest.TestCase):
    def test_usage_increments_and_rolls_over_by_day(self):
        current = datetime(2026, 8, 18, 10, 0, 0)
        svc = MarketDataService(
            http_get=fake_http(lambda u: (True, apizero_ok_body())),
            now=lambda: current,
            intraday_ttl=0.0,
        )
        svc.get_intraday("019633", market="a", force=True)
        svc.get_intraday("019633", market="a", force=True)
        usage = svc.apizero_usage()
        self.assertEqual(usage["used"], 2)
        self.assertEqual(usage["limit"], 50)
        self.assertEqual(usage["date"], "2026-08-18")

        current = datetime(2026, 8, 19, 10, 0, 0)
        svc.get_intraday("019633", market="a", force=True)
        usage2 = svc.apizero_usage()
        self.assertEqual(usage2["used"], 1)
        self.assertEqual(usage2["date"], "2026-08-19")

if __name__ == "__main__":
    unittest.main()
