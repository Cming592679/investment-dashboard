"""MarketDataService — 统一基金行情数据层（P0-0 修复）

目标：让系统明确知道一个收益数字：
  - 是什么（官方净值收益 / 盘中估算 / 不可用）
  - 对应哪一天 / 哪个时间点
  - 来自哪里（source）
  - 属于哪一类（Official / Estimated）
  - 是否已过期（freshness）

禁止行为（Rulebook + 本专项约束）：
  - 禁止 intraday 不可用时 fallback 到 nav_return
  - 禁止把 estimated 标成 official
  - 禁止静默使用过期数据
  - 数据不存在时显式 UNAVAILABLE / ERROR
"""

import json
import re
import time as _time
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from typing import Callable, Dict, List, Optional, Tuple
from logging_utils import get_logger


logger = get_logger("market_data")


# ══════════════════════════════════════════════════════════
# 状态常量
# ══════════════════════════════════════════════════════════

STATUS_OFFICIAL = "official"          # 最新正式净值
STATUS_ESTIMATED = "estimated"        # 当前盘中估算
STATUS_STALE = "stale"                # 有数据但超过新鲜度
STATUS_UNAVAILABLE = "unavailable"    # 当前无可靠数据
STATUS_ERROR = "error"                # 数据源请求失败


# ══════════════════════════════════════════════════════════
# 数据模型
# ══════════════════════════════════════════════════════════

@dataclass
class OfficialNAV:
    """基金最近一个正式公布的官方净值及其正式收益。"""
    nav: Optional[float] = None
    nav_date: Optional[str] = None          # YYYY-MM-DD
    nav_return: Optional[float] = None      # 百分数（如 4.86 表示 +4.86%）
    source: str = ""
    fetched_at: str = ""
    method: str = "official_nav"
    status: str = STATUS_UNAVAILABLE        # official | unavailable | error
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IntradayQuote:
    """独立的盘中数据模型，与 Official NAV 完全分离。"""
    intraday_change_pct: Optional[float] = None  # 百分数
    estimated_nav: Optional[float] = None
    quote_time: Optional[str] = None             # 行情/估值时间 ISO
    source: str = ""
    fetched_at: str = ""
    method: str = "intraday_estimate"            # apizero | proxy_index
    status: str = STATUS_UNAVAILABLE             # estimated | unavailable | error
    freshness: str = "unknown"                   # fresh | stale
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════
# 基础 HTTP 与解析
# ══════════════════════════════════════════════════════════

def _default_http_get(url: str, headers: Optional[dict] = None,
                      decode: str = "utf-8", timeout: float = 10.0) -> Tuple[bool, Optional[str]]:
    try:
        req = urllib.request.Request(
            url,
            headers=headers or {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://finance.sina.com.cn",
            },
        )
        body = urllib.request.urlopen(req, timeout=timeout).read().decode(decode, errors="replace")
        return True, body
    except Exception:
        return False, None


def _iso_now(now: Optional[datetime] = None) -> str:
    return (now or datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")


def _sina_symbol(symbol: str) -> Optional[str]:
    """把 159995.SZ / 000688.SS 转成新浪行情代码 sz159995 / sh000688。"""
    code, _, suffix = symbol.partition(".")
    if not code or not suffix:
        return None
    if suffix.upper() in ("SZ", "SS", "SH"):
        prefix = "sz" if suffix.upper() == "SZ" else "sh"
        return prefix + code
    return None


def _parse_sina_fund_nav(code: str, body: str) -> Optional[dict]:
    m = re.search(r'f_\w+="(.*)"', body)
    if not m:
        return None
    parts = m.group(1).split(",")
    if len(parts) < 5:
        return None
    return {
        "code": code,
        "name": parts[0],
        "nav": float(parts[1]) if parts[1] else None,
        "prev_nav": float(parts[3]) if len(parts) > 3 and parts[3] else None,
        "date": parts[4] if len(parts) > 4 else None,
        "acc_nav": float(parts[5]) if len(parts) > 5 and parts[5] else None,
    }


def _parse_sina_quote(body: str) -> Optional[dict]:
    """解析新浪实时行情（A股指数/ETF）。字段：name/open/prev/current/.../date/time。"""
    m = re.search(r'="(.*)"', body)
    if not m:
        return None
    parts = m.group(1).split(",")
    if len(parts) < 32:
        return None
    try:
        current = float(parts[3])
        prev = float(parts[2])
    except (ValueError, TypeError):
        return None
    if prev <= 0:
        return None
    return {
        "name": parts[0],
        "current": current,
        "prev": prev,
        "date": parts[30],
        "time": parts[31],
    }


# ══════════════════════════════════════════════════════════
# 基金类型（用于盘中数据按类型处理）
# ══════════════════════════════════════════════════════════

# QDII / 海外资产基金：无官方盘中估值，A股交易时段内底层海外市场已收盘
QDII_FUND_CODES = {
    "100055",  # 富国全球科技互联网(QDII)C
    "006479",  # 广发纳斯达克100ETF联接(QDII)C
    "016665",  # 天弘全球高端制造(QDII)C
}

APIZERO_DAILY_LIMIT = 50  # apizero 免费匿名额度（次/天）


def is_qdii(code: str) -> bool:
    return code in QDII_FUND_CODES


# ══════════════════════════════════════════════════════════
# 盘中代理：板块 → 新浪实时行情代码
# ══════════════════════════════════════════════════════════

# 显式代理表（method=proxy_index）。优先使用板块自身基准，缺失时用行业ETF/指数。
INTRADAY_PROXY_MAP = {
    "019633": "sh512760",   # 半导体设备ETF（基金自身基准）
    "CPO": "sz159997",      # 电子ETF
    "021528": "sz159997",   # 电子ETF
    "015789": "sh512660",   # 军工ETF
    "025856": "sz159611",   # 电力ETF
    "020608": "sh000688",   # 科创50（机器人暂无专属ETF，用科创50代理）
    "STORAGE": "sz159995",  # 芯片ETF（A股存储代理；海外部分不可用）
}


class MarketDataService:
    """统一行情数据服务：官方净值 + 盘中数据 + 状态 + freshness + 缓存。"""

    def __init__(
        self,
        http_get: Optional[Callable] = None,
        now: Optional[Callable[[], datetime]] = None,
        intraday_ttl: float = 300.0,
        nav_ttl: float = 1800.0,
    ):
        self._http = http_get or _default_http_get
        self._now = now or (lambda: datetime.now())
        self._intraday_cache: Dict[str, Tuple[IntradayQuote, float]] = {}
        self._nav_cache: Dict[str, Tuple[OfficialNAV, float]] = {}
        self._apizero_usage_date: Optional[str] = None
        self._apizero_used = 0
        self._intraday_ttl = intraday_ttl
        self._nav_ttl = nav_ttl

    # ─────────────────────────────
    # Official NAV
    # ─────────────────────────────

    def fetch_official_sina(self, code: str) -> OfficialNAV:
        ok, body = self._http(
            f"https://hq.sinajs.cn/list=f_{code}",
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"},
            decode="gbk",
        )
        now_iso = _iso_now(self._now())
        if not ok or body is None:
            return OfficialNAV(source="sina", fetched_at=now_iso, status=STATUS_ERROR, message="sina 请求失败")
        d = _parse_sina_fund_nav(code, body)
        if not d or not d.get("nav") or not d.get("date"):
            return OfficialNAV(source="sina", fetched_at=now_iso, status=STATUS_UNAVAILABLE, message="sina 无有效净值")
        nav_return = None
        if d.get("prev_nav") and d["prev_nav"] > 0:
            nav_return = round((d["nav"] - d["prev_nav"]) / d["prev_nav"] * 100, 2)
        return OfficialNAV(
            nav=d["nav"],
            nav_date=d["date"],
            nav_return=nav_return,
            source="sina",
            fetched_at=now_iso,
            method="official_nav",
            status=STATUS_OFFICIAL,
        )

    def fetch_official_sina_batch(self, codes: List[str]) -> Dict[str, OfficialNAV]:
        """新浪批量净值（一次请求多只基金）。"""
        now_iso = _iso_now(self._now())
        if not codes:
            return {}
        ok, body = self._http(
            "https://hq.sinajs.cn/list=" + ",".join(f"f_{c}" for c in codes),
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"},
            decode="gbk",
        )
        if not ok or body is None:
            return {}
        result: Dict[str, OfficialNAV] = {}
        for line in body.strip().split("\n"):
            m = re.search(r'f_(\w+)="(.*)"', line)
            if not m:
                continue
            code = m.group(1)
            d = _parse_sina_fund_nav(code, line)
            if not d or not d.get("nav") or not d.get("date"):
                result[code] = OfficialNAV(source="sina", fetched_at=now_iso,
                                           status=STATUS_UNAVAILABLE, message="sina 无有效净值")
                continue
            nav_return = None
            if d.get("prev_nav") and d["prev_nav"] > 0:
                nav_return = round((d["nav"] - d["prev_nav"]) / d["prev_nav"] * 100, 2)
            result[code] = OfficialNAV(
                nav=d["nav"], nav_date=d["date"], nav_return=nav_return,
                source="sina", fetched_at=now_iso, method="official_nav",
                status=STATUS_OFFICIAL,
            )
        return result

    def get_official_navs(self, codes: List[str], force: bool = True) -> Dict[str, OfficialNAV]:
        """批量官方净值：新浪批量主源 → 东财单只 fallback。"""
        result: Dict[str, OfficialNAV] = {}
        missing: List[str] = []
        batch = self.fetch_official_sina_batch(codes)
        for code in codes:
            nav = batch.get(code)
            if nav and nav.status == STATUS_OFFICIAL:
                result[code] = nav
            else:
                missing.append(code)
        for code in missing:
            nav = self.get_official_nav(code, force=force)
            result[code] = nav
        return result

    def fetch_official_eastmoney(self, code: str) -> OfficialNAV:
        url = (
            "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNFInfo"
            f"?pageIndex=1&pageSize=1&plat=Android&appType=ttjj&product=EFund"
            f"&Version=1&deviceid=test&Fcodes={code}"
        )
        ok, body = self._http(url, headers={"User-Agent": "Mozilla/5.0"})
        now_iso = _iso_now(self._now())
        if not ok or body is None:
            return OfficialNAV(source="eastmoney", fetched_at=now_iso, status=STATUS_ERROR, message="eastmoney 请求失败")
        try:
            data = json.loads(body)
            row = (data.get("Datas") or [{}])[0]
            nav = row.get("NAV")
            nav_date = row.get("PDATE")
            nav_return = row.get("NAVCHGRT")
            if nav is None or not nav_date:
                return OfficialNAV(source="eastmoney", fetched_at=now_iso, status=STATUS_UNAVAILABLE, message="eastmoney 无有效净值")
            return OfficialNAV(
                nav=float(nav),
                nav_date=nav_date,
                nav_return=float(nav_return) if nav_return not in (None, "") else None,
                source="eastmoney",
                fetched_at=now_iso,
                method="official_nav",
                status=STATUS_OFFICIAL,
            )
        except Exception as e:
            return OfficialNAV(source="eastmoney", fetched_at=now_iso, status=STATUS_ERROR, message=f"eastmoney 解析失败: {e}")

    def get_official_nav(self, code: str, force: bool = False) -> OfficialNAV:
        """Primary=新浪，Fallback=东财。均失败 → UNAVAILABLE/ERROR，不伪造。"""
        cached = self._nav_cache.get(code)
        if cached and not force and (self._now().timestamp() - cached[1]) < self._nav_ttl:
            return cached[0]

        nav = self.fetch_official_sina(code)
        if nav.status == STATUS_OFFICIAL:
            self._nav_cache[code] = (nav, self._now().timestamp())
            return nav
        # fallback
        nav2 = self.fetch_official_eastmoney(code)
        if nav2.status == STATUS_OFFICIAL:
            self._nav_cache[code] = (nav2, self._now().timestamp())
            return nav2
        # 两者都失败：返回错误信息（不以旧缓存冒充新鲜；旧缓存仅在调用方显式降级时使用）
        status = STATUS_ERROR if nav.status == STATUS_ERROR or nav2.status == STATUS_ERROR else STATUS_UNAVAILABLE
        result = OfficialNAV(
            source=f"sina:{nav.status}|eastmoney:{nav2.status}",
            fetched_at=_iso_now(self._now()),
            status=status,
            message=nav.message or nav2.message or "无可用官方净值",
        )
        logger.warning("官方净值不可用 code=%s status=%s msg=%s", code, status, result.message)
        self._nav_cache[code] = (result, self._now().timestamp())
        return result

    def invalidate_nav(self, code: str) -> None:
        self._nav_cache.pop(code, None)

    # ─────────────────────────────
    # Intraday
    # ─────────────────────────────

    def fetch_intraday_apizero(self, code: str) -> IntradayQuote:
        today = self._now().date().isoformat()
        if self._apizero_usage_date != today:
            self._apizero_usage_date = today
            self._apizero_used = 0
        self._apizero_used += 1

        url = f"https://v1.apizero.cn/api/fund?action=estimate&code={code}"
        ok, body = self._http(url, headers={"User-Agent": "Mozilla/5.0"})
        now_iso = _iso_now(self._now())
        if not ok or body is None:
            return IntradayQuote(source="apizero", fetched_at=now_iso, method="apizero",
                                 status=STATUS_ERROR, message="apizero 请求失败")
        try:
            data = json.loads(body)
            if data.get("code") != 0:
                return IntradayQuote(source="apizero", fetched_at=now_iso, method="apizero",
                                     status=STATUS_UNAVAILABLE, message=f"apizero 返回错误: {data.get('code')}")
            d = data.get("data") or {}
            chg = d.get("change_rate")
            quote_time = d.get("update_time") or d.get("nav_date") or ""
            return IntradayQuote(
                intraday_change_pct=float(chg) if chg not in (None, "") else None,
                estimated_nav=float(d["estimate"]) if d.get("estimate") not in (None, "") else None,
                quote_time=quote_time,
                source="apizero",
                fetched_at=now_iso,
                method="apizero",
                status=STATUS_ESTIMATED,
                freshness="fresh",
            )
        except Exception as e:
            return IntradayQuote(source="apizero", fetched_at=now_iso, method="apizero",
                                 status=STATUS_ERROR, message=f"apizero 解析失败: {e}")

    def fetch_intraday_proxy(self, sina_symbol: str) -> IntradayQuote:
        """新浪实时指数/ETF 行情代理。method=proxy_index，明确非官方。"""
        ok, body = self._http(
            f"https://hq.sinajs.cn/list={sina_symbol}",
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"},
            decode="gbk",
        )
        now_iso = _iso_now(self._now())
        if not ok or body is None:
            return IntradayQuote(source=f"sina:{sina_symbol}", fetched_at=now_iso,
                                 method="proxy_index", status=STATUS_ERROR, message="sina 行情请求失败")
        q = _parse_sina_quote(body)
        if not q:
            return IntradayQuote(source=f"sina:{sina_symbol}", fetched_at=now_iso,
                                 method="proxy_index", status=STATUS_UNAVAILABLE, message="sina 行情无有效数据")
        chg = round((q["current"] - q["prev"]) / q["prev"] * 100, 2)
        quote_time = f"{q['date']}T{q['time']}"
        return IntradayQuote(
            intraday_change_pct=chg,
            estimated_nav=q["current"],
            quote_time=quote_time,
            source=f"sina:{sina_symbol}",
            fetched_at=now_iso,
            method="proxy_index",
            status=STATUS_ESTIMATED,
            freshness="fresh",
        )

    def get_intraday(self, fund_id: str, market: str = "a",
                     proxy_symbol: Optional[str] = None, force: bool = False) -> IntradayQuote:
        """按基金类型获取盘中数据。

        - A股基金：apizero 真实估值（如可用）→ 新浪指数/ETF 代理
        - QDII/海外：A股交易时段内无可靠盘中数据 → UNAVAILABLE
        - 两者都失败：UNAVAILABLE/ERROR，绝不回退官方净值
        """
        cache_key = f"{fund_id}|{market}"
        cached = self._intraday_cache.get(cache_key)
        if cached and not force and (self._now().timestamp() - cached[1]) < self._intraday_ttl:
            return cached[0]

        result: Optional[IntradayQuote] = None
        if market not in ("a", "mixed"):
            result = IntradayQuote(
                source="none", fetched_at=_iso_now(self._now()),
                method="intraday_estimate", status=STATUS_UNAVAILABLE,
                message="非A股基金（QDII/海外）在A股交易时段无可靠盘中数据",
            )
        else:
            # 一级：apizero 真实估值（若恢复）
            apz = self.fetch_intraday_apizero(fund_id)
            if apz.status == STATUS_ESTIMATED and apz.intraday_change_pct is not None:
                result = apz
            elif proxy_symbol:
                # 二级：新浪指数/ETF 实时代理
                prox = self.fetch_intraday_proxy(proxy_symbol)
                if prox.status == STATUS_ESTIMATED:
                    result = prox
            if result is None:
                result = IntradayQuote(
                    source="none", fetched_at=_iso_now(self._now()),
                    method="intraday_estimate", status=STATUS_UNAVAILABLE,
                    message="盘中数据不可用（无估值源）",
                )

        self._intraday_cache[cache_key] = (result, self._now().timestamp())
        if market in ("a", "mixed") and result.status in (STATUS_UNAVAILABLE, STATUS_ERROR):
            logger.warning("盘中数据不可用 fund_id=%s status=%s msg=%s",
                           fund_id, result.status, result.message)
        return result

    def apizero_usage(self) -> Dict[str, object]:
        """当日 apizero 配额使用情况（used / limit / date）。"""
        today = self._now().date().isoformat()
        if self._apizero_usage_date != today:
            return {"date": today, "used": 0, "limit": APIZERO_DAILY_LIMIT}
        return {
            "date": self._apizero_usage_date,
            "used": self._apizero_used,
            "limit": APIZERO_DAILY_LIMIT,
        }

    def refresh_intraday(
        self,
        fund_ids: List[str],
        fund_market: Optional[Dict[str, str]] = None,
        proxy_map: Optional[Dict[str, str]] = None,
    ) -> None:
        for fid in fund_ids:
            market = (fund_market or {}).get(fid, "a")
            proxy = (proxy_map or {}).get(fid)
            self.get_intraday(fid, market=market, proxy_symbol=proxy, force=True)

    # ─────────────────────────────
    # Freshness
    # ─────────────────────────────

    @staticmethod
    def intraday_freshness(quote: IntradayQuote, max_age_seconds: int = 900) -> str:
        """盘中数据新鲜度：quote_time 距今超过 max_age 视为 stale。"""
        if quote.status != STATUS_ESTIMATED or not quote.quote_time:
            return "unknown"
        try:
            t = datetime.fromisoformat(quote.quote_time)
            age = (datetime.now() - t).total_seconds()
        except Exception:
            return "unknown"
        return "fresh" if age <= max_age_seconds else "stale"

    @staticmethod
    def expected_trading_date(today: Optional[date] = None) -> date:
        """粗略最近交易日（跳过周末；法定节假日由数据源实际 nav_date 校准）。"""
        d = today or date.today()
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        return d

    def official_nav_freshness(self, nav: OfficialNAV) -> str:
        """官方净值新鲜度：A股允许 T+1；QDII 允许 T+2。"""
        if nav.status != STATUS_OFFICIAL or not nav.nav_date:
            return "unknown"
        try:
            nav_d = datetime.strptime(nav.nav_date, "%Y-%m-%d").date()
        except ValueError:
            return "unknown"
        expected = self.expected_trading_date(self._now().date())
        lag = (expected - nav_d).days
        return "fresh" if lag <= 1 else "stale"


# 全局单例（app 使用）
market_data = MarketDataService()
