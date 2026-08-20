"""基金净值抓取模块 — 新浪财经 API（收盘净值）+ 东方财富 API（历史净值）

数据源:
  新浪财经: https://hq.sinajs.cn/list=f_{code}  → 最新收盘净值（A股当晚~20:00可用）
  东方财富: https://api.fund.eastmoney.com/f10/lsjz  → 历史净值（任意日期回溯）

用法:
  from fund_nav_fetcher import get_fund_nav, get_fund_nav_history, update_portfolio_nav
"""

import json
import os
import re
import time as _time
import urllib.request
from datetime import date, datetime, timedelta
from typing import Optional
from storage import write_json


# ══════════════════════════════════════════════════════════
# 新浪财经 — 最新收盘净值
# ══════════════════════════════════════════════════════════

def get_fund_nav(code: str) -> Optional[dict]:
    """获取单只基金的最新收盘净值。

    Returns:
        {"code": "019633", "name": "国泰...", "nav": 2.5511, "date": "2026-08-04", "acc_nav": 6.3154}
        或 None（抓取失败）
    """
    try:
        url = f"https://hq.sinajs.cn/list=f_{code}"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        resp = urllib.request.urlopen(req, timeout=10).read().decode("gbk")

        match = re.search(r'f_\w+="(.*)"', resp)
        if not match:
            return None

        parts = match.group(1).split(",")
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
    except Exception as e:
        print(f"  ⚠ 新浪抓取 {code} 失败: {e}")
        return None


def get_all_fund_navs(codes: list) -> dict:
    """批量获取多只基金净值（一次请求）。"""
    try:
        url = "https://hq.sinajs.cn/list=" + ",".join(f"f_{c}" for c in codes)
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        resp = urllib.request.urlopen(req, timeout=15).read().decode("gbk")

        results = {}
        for line in resp.strip().split("\n"):
            if not line.strip():
                continue
            match = re.search(r'f_(\w+)="(.*)"', line)
            if not match:
                continue
            code = match.group(1)
            parts = match.group(2).split(",")
            if len(parts) < 5:
                continue
            results[code] = {
                "code": code,
                "name": parts[0],
                "nav": float(parts[1]) if parts[1] else None,
                "prev_nav": float(parts[3]) if len(parts) > 3 and parts[3] else None,
                "date": parts[4],
                "acc_nav": float(parts[5]) if len(parts) > 5 and parts[5] else None,
            }
        return results
    except Exception as e:
        print(f"  ⚠ 批量抓取失败: {e}")
        return {}


# ══════════════════════════════════════════════════════════
# 极数本源 API — 盘中实时估值（免费，匿名50次/天）
# ══════════════════════════════════════════════════════════

_apizero_cache = {}  # {code: {data, ts}}

def get_fund_estimate_apizero(code: str) -> Optional[dict]:
    """获取基金盘中实时估值。免费API，匿名50次/天，登录200次/天。
    返回: {net_value, estimate, change_rate, nav_date, update_time} 或 None
    缓存60秒，盘中每分钟自动更新。
    """
    import time as _t
    now = _t.time()
    cached = _apizero_cache.get(code)
    if cached and now - cached.get('ts', 0) < 60:
        return cached['data']

    try:
        url = f"https://v1.apizero.cn/api/fund?action=estimate&code={code}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')
        data = json.loads(resp)
        if data.get('code') == 0:
            result = data['data']
            _apizero_cache[code] = {'data': result, 'ts': now}
            return result
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════
# 东方财富 — 历史净值
# ══════════════════════════════════════════════════════════

def get_fund_nav_history(code: str, pages: int = 5) -> list:
    """获取基金历史净值记录。

    Returns:
        [{"date": "2026-08-04", "nav": 2.5511, "change_pct": "4.93%"}, ...]
    """
    results = []
    try:
        for page in range(1, pages + 1):
            url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex={page}&pageSize=20"
            req = urllib.request.Request(url, headers={
                "Referer": "https://fund.eastmoney.com/",
                "User-Agent": "Mozilla/5.0",
            })
            resp = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
            data = json.loads(resp)

            for item in data.get("Data", {}).get("LSJZList", []):
                results.append({
                    "date": item.get("FSRQ", ""),
                    "nav": float(item.get("DWJZ", 0)) if item.get("DWJZ") else None,
                    "acc_nav": float(item.get("LJJZ", 0)) if item.get("LJJZ") else None,
                    "change_pct": item.get("JZZZL", ""),
                })

            if len(data.get("Data", {}).get("LSJZList", [])) < 20:
                break  # 最后一页

            _time.sleep(0.3)  # 礼貌延迟

    except Exception as e:
        print(f"  ⚠ 历史净值抓取 {code} 失败: {e}")

    return results


# ══════════════════════════════════════════════════════════
# 持仓净值更新
# ══════════════════════════════════════════════════════════

def get_portfolio_codes(portfolio: dict) -> list:
    """从 portfolio.json 提取需要抓取净值的基金代码列表。
    sell_pending 的持仓也纳入（份额仍在账户产生收益），仅跳过 sold 和 non_investment。"""
    codes = []
    for h in portfolio.get("holdings", []):
        code = h.get("fund_code", "")
        status = h.get("status", "")
        if code and status not in ("non_investment", "sold") and h.get("amount", 0) > 0:
            codes.append(code)
    return codes


def compute_shares(amount: float, nav: float) -> Optional[float]:
    """根据金额和净值反推份额。"""
    if not nav or nav <= 0:
        return None
    return round(amount / nav, 2)


def update_portfolio_nav(portfolio: dict, nav_service=None) -> dict:
    """更新持仓官方净值（统一走 MarketDataService，P0-0 修复）。

    数据语义：
    - 每只基金保存 nav / nav_date / nav_return / nav_source / nav_fetched_at / nav_status；
    - daily_return = amount × nav_return/100，日期语义为「该基金自己的 nav_date」；
    - 组合官方收益只对同一 nav_date 的持仓合计（official_return），禁止混合不同日期；
    - 抓取失败的持仓保留旧值但显式标记 nav_status=stale，不静默冒充新鲜。
    """
    from market_data import market_data as default_md

    md = nav_service or default_md
    codes = get_portfolio_codes(portfolio)
    if not codes:
        return portfolio

    navs = md.get_official_navs(codes, force=True)
    if not navs:
        print("  ⚠ 未获取到任何净值数据")
        return portfolio

    updated_count = 0
    stale_codes = []
    unavailable_codes = []
    for h in portfolio.get("holdings", []):
        code = h.get("fund_code", "")
        status = h.get("status", "")
        if status == "sold" or h.get("amount", 0) <= 0:
            continue

        nav_data = navs.get(code)
        if not nav_data or nav_data.status != "official" or not nav_data.nav:
            # 失败：保留旧值，显式标记 stale（有旧数据）或 unavailable（无旧数据）
            has_old = h.get("nav_date") and h.get("nav")
            h["nav_status"] = "stale" if has_old else "unavailable"
            if not has_old:
                unavailable_codes.append(code)
            else:
                stale_codes.append(code)
            continue

        # 官方净值成功
        prev_amount = h.get("amount", 0)
        h["nav"] = nav_data.nav
        h["nav_date"] = nav_data.nav_date
        h["nav_return"] = nav_data.nav_return
        h["day_return_pct"] = nav_data.nav_return  # 兼容旧字段，语义=官方净值收益率
        h["nav_source"] = nav_data.source
        h["nav_fetched_at"] = nav_data.fetched_at
        h["nav_status"] = "official"
        updated_count += 1
        if nav_data.nav_return is not None:
            # 当日收益 = 旧金额 × 收益率（= 份额 × 净值差，口径正确）
            h["daily_return"] = round(prev_amount * nav_data.nav_return / 100, 2)
        else:
            h["daily_return"] = None

        # 金额按 份额 × 新净值 重算（shares 是源头真相）；无份额时按收益率外推
        shares = h.get("shares")
        if shares:
            h["amount"] = round(shares * nav_data.nav, 2)
        elif nav_data.nav_return is not None and prev_amount:
            h["amount"] = round(prev_amount * (1 + nav_data.nav_return / 100), 2)

        # holding_return 从 amount - cost_basis 重算（此时 amount 已按新净值更新）
        cost = h.get("cost_basis", 0)
        amt = h.get("amount", 0)
        if cost > 0:
            h["holding_return"] = round(amt - cost, 2)
            h["holding_return_pct"] = round((amt - cost) / cost * 100, 2)

    # ── 组合官方收益：只对同一 nav_date 合计（禁止混合不同日期） ──
    total_amount = 0
    total_holding_return = 0
    official_active = []
    for h in portfolio.get("holdings", []):
        cost = h.get("cost_basis", 0)
        amt = h.get("amount", 0)
        if cost > 0:
            h["holding_return"] = round(amt - cost, 2)
            h["holding_return_pct"] = round((amt - cost) / cost * 100, 2)
        # sell_pending 的金额也计入汇总（份额还在账户）
        if h.get("status") != "sold":
            total_amount += amt
            total_holding_return += h.get("holding_return", 0)
        if (h.get("status") != "sold" and amt > 0
                and h.get("nav_status") == "official" and h.get("nav_date")):
            official_active.append(h)

    latest_nav_date = None
    same_date_holdings = []
    if official_active:
        latest_nav_date = max(h["nav_date"] for h in official_active)
        same_date_holdings = [h for h in official_active if h["nav_date"] == latest_nav_date]
        # 已成功抓取但净值日期早于最新日期 → stale（不算失败，但不可同日合计）
        for h in official_active:
            if h["nav_date"] != latest_nav_date and h.get("fund_code") not in stale_codes:
                stale_codes.append(h.get("fund_code"))

    same_date_amt = 0.0
    same_date_return_pct = None
    if same_date_holdings:
        same_date_amt = round(sum(h.get("daily_return") or 0 for h in same_date_holdings), 2)
        denom = sum(h.get("amount", 0) for h in same_date_holdings)
        if denom > 0:
            weighted = sum((h.get("amount", 0) * (h.get("nav_return") or 0)) for h in same_date_holdings)
            same_date_return_pct = round(weighted / denom, 2)

    portfolio["daily_return"] = same_date_amt  # 仅同一 nav_date 的官方收益合计
    portfolio["official_return"] = {
        "nav_date": latest_nav_date,
        "return_pct": same_date_return_pct,
        "coverage": f"{len(same_date_holdings)}/{len(official_active) or 0}" if official_active else "0/0",
        "covered_codes": [h.get("fund_code") for h in same_date_holdings],
        "stale_holdings": stale_codes,
        "unavailable_holdings": unavailable_codes,
    }

    portfolio["total_assets"] = round(portfolio.get("cash", 0) + total_amount, 2)
    portfolio["holding_return"] = round(total_holding_return, 2)

    # ── 重算板块分配 ──
    sectors = {}
    for h in portfolio.get("holdings", []):
        if h.get("status") == "sold" or h.get("amount", 0) <= 0:
            continue
        sector = h.get("sector") or "其他"
        if sector not in sectors:
            sectors[sector] = {"funds": [], "total_amount": 0}
        did = h.get("dashboard_id", "")
        if did and did not in sectors[sector]["funds"]:
            sectors[sector]["funds"].append(did)
        sectors[sector]["total_amount"] += h.get("amount", 0)
    for name, info in sectors.items():
        info["pct"] = round(info["total_amount"] / portfolio["total_assets"] * 100, 1) if portfolio["total_assets"] > 0 else 0
    portfolio["sector_allocation"] = sectors

    portfolio["nav_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    active_codes = len([h for h in portfolio.get("holdings", []) if h.get("status") != "sold" and h.get("amount", 0) > 0])
    print(f"  ✅ 净值更新: {updated_count}/{len(codes)} 只基金, {active_codes} 只活跃, "
          f"官方收益(NAV {latest_nav_date}) ¥{portfolio['daily_return']:+,.0f}, "
          f"stale={stale_codes}, unavailable={unavailable_codes}")
    portfolio["latest_return"] = summarize_latest_return(portfolio)
    return portfolio


def summarize_latest_return(portfolio: dict) -> dict:
    """全持仓「最新披露净值」日收益合计（按各自 nav_date，混合日期时显式标注）。

    与 official_return（仅同日合计，禁止混日期）互补：
    - official_return：只统计最新净值日当天的持仓，保证口径纯净；
    - latest_return：统计所有活跃持仓按其最新披露净值的日收益，便于与券商/账本对账
      （QDII 等 T+2 基金会用自己较旧的 nav_date，但收益本身是官方值）。
    过滤语义与 official_return 一致：status != sold、amount > 0、nav_status == official。
    """
    active = [
        h for h in portfolio.get("holdings", [])
        if h.get("status") != "sold"
        and (h.get("amount") or 0) > 0
        and h.get("nav_status") == "official"
        and h.get("nav_date")
        and h.get("daily_return") is not None
    ]
    total = round(sum(h.get("daily_return") or 0 for h in active), 2)
    denom = sum(h.get("amount", 0) for h in active)
    pct = None
    if denom > 0:
        weighted = sum((h.get("amount", 0) * (h.get("nav_return") or 0)) for h in active)
        pct = round(weighted / denom, 2)
    dates = sorted({h["nav_date"] for h in active})
    return {
        "return": total,
        "return_pct": pct,
        "nav_dates": dates,
        "mixed_dates": len(dates) > 1,
        "holdings": [
            {
                "fund_code": h.get("fund_code"),
                "fund_name": h.get("fund_name", ""),
                "nav_date": h.get("nav_date"),
                "nav_return": h.get("nav_return"),
                "daily_return": h.get("daily_return"),
            }
            for h in sorted(active, key=lambda x: x.get("fund_code") or "")
        ],
    }


# ══════════════════════════════════════════════════════════
# 历史回填
# ══════════════════════════════════════════════════════════

def backfill_portfolio_history(portfolio: dict, history_dir: str, days: int = 30):
    """回填 portfolio_history/ 目录下的每日快照。

    使用东方财富历史净值 API 拉取每只基金的每日净值，
    结合持仓份额计算每日金额变化。
    """
    os.makedirs(history_dir, exist_ok=True)
    today = date.today()

    holdings = [h for h in portfolio.get("holdings", [])
                if h.get("status") not in ("non_investment", "exit_pending")]

    # 为每只基金拉历史净值
    fund_histories = {}
    for h in holdings:
        code = h.get("fund_code", "")
        if not code:
            continue
        shares = h.get("shares")
        if not shares:
            # 反推份额
            nav_data = get_fund_nav(code)
            if nav_data and nav_data.get("nav"):
                shares = compute_shares(h["amount"], nav_data["nav"])
                h["shares"] = shares
        if not shares:
            continue

        print(f"  拉取 {code} {h.get('fund_name','')[:15]}...")
        hist = get_fund_nav_history(code, pages=max(1, days // 20 + 1))
        fund_histories[code] = {"shares": shares, "history": hist}
        _time.sleep(0.2)

    # 生成每日快照
    index_entries = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        d_str = d.strftime("%Y-%m-%d")
        daily = {"date": d_str, "funds": {}}
        total_value = 0
        total_daily_return = 0

        for h in holdings:
            code = h.get("fund_code", "")
            fh = fund_histories.get(code, {})
            shares = fh.get("shares", 0)
            hist = fh.get("history", [])

            # 找到该日期的净值记录
            nav_entry = next((e for e in hist if e["date"] == d_str), None)
            if not nav_entry or not nav_entry.get("nav"):
                continue

            amount = round(shares * nav_entry["nav"], 2)
            prev_entry = next((e for e in hist if e["date"] == (d - timedelta(days=1)).strftime("%Y-%m-%d")), None)
            prev_amount = round(shares * prev_entry["nav"], 2) if prev_entry and prev_entry.get("nav") else amount
            day_return = round(amount - prev_amount, 2)

            daily["funds"][code] = {
                "name": h.get("fund_name", ""),
                "nav": nav_entry["nav"],
                "amount": amount,
                "day_return": day_return,
                "day_return_pct": nav_entry.get("change_pct", ""),
                "shares": shares,
            }
            total_value += amount
            total_daily_return += day_return

        if daily["funds"]:
            daily["total_value"] = round(total_value, 2)
            daily["total_daily_return"] = round(total_daily_return, 2)
            daily["fund_count"] = len(daily["funds"])

            snap_path = os.path.join(history_dir, f"{d_str}.json")
            write_json(snap_path, daily)

            index_entries.append({
                "date": d_str,
                "total_value": round(total_value, 2),
                "daily_return": round(total_daily_return, 2),
                "funds_tracked": len(daily["funds"]),
            })

    # 写索引
    index_path = os.path.join(history_dir, "_index.json")
    write_json(index_path, index_entries)

    print(f"  ✅ 回填完成: {len(index_entries)} 天快照 → {history_dir}")
    return index_entries
