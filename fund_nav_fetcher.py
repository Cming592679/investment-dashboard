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


def update_portfolio_nav(portfolio: dict) -> dict:
    """更新持仓净值和日收益。返回更新后的 portfolio dict。

    原则（修复双写冲突）：
    - amount/cost_basis 不做任何计算——截图是唯一 ground truth
    - 只更新 nav、nav_date、day_return_pct、daily_return
    - holding_return = amount - cost_basis（amount已由截图更新）
    - daily_return = amount × day_return_pct / 100（估算）
    """
    codes = get_portfolio_codes(portfolio)
    if not codes:
        return portfolio

    navs = get_all_fund_navs(codes)
    if not navs:
        print("  ⚠ 未获取到任何净值数据")
        return portfolio

    updated_count = 0
    for h in portfolio.get("holdings", []):
        code = h.get("fund_code", "")
        if code not in navs:
            continue

        status = h.get("status", "")
        if status == "sold" or h.get("amount", 0) <= 0:
            continue

        nav_data = navs[code]
        new_nav = nav_data.get("nav")
        prev_nav = nav_data.get("prev_nav")
        nav_date = nav_data.get("date")

        if not new_nav:
            continue

        # 只更新净值相关字段，不动 amount/cost_basis
        h["nav"] = new_nav
        h["nav_date"] = nav_date

        if prev_nav and prev_nav > 0:
            day_return_pct = round((new_nav - prev_nav) / prev_nav * 100, 2)
            h["day_return_pct"] = day_return_pct
            # 估算日收益
            h["daily_return"] = round(h.get("amount", 0) * day_return_pct / 100, 2)

        # holding_return 从 amount - cost_basis 重算
        cost = h.get("cost_basis", 0)
        amt = h.get("amount", 0)
        if cost > 0:
            h["holding_return"] = round(amt - cost, 2)
            h["holding_return_pct"] = round((amt - cost) / cost * 100, 2)

        updated_count += 1

    # ── 重算持仓级别汇总 ──
    total_amount = 0
    total_daily_return = 0
    total_holding_return = 0
    for h in portfolio.get("holdings", []):
        cost = h.get("cost_basis", 0)
        amt = h.get("amount", 0)
        if cost > 0:
            h["holding_return"] = round(amt - cost, 2)
            h["holding_return_pct"] = round((amt - cost) / cost * 100, 2)
        # sell_pending 的金额也计入汇总（份额还在账户）
        if h.get("status") != "sold":
            total_amount += amt
            total_daily_return += h.get("daily_return", 0)
            total_holding_return += h.get("holding_return", 0)

    portfolio["total_assets"] = round(portfolio.get("cash", 0) + total_amount, 2)
    portfolio["daily_return"] = round(total_daily_return, 2)
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
    print(f"  ✅ 净值更新: {updated_count}/{len(codes)} 只基金, {active_codes} 只活跃, 总资产 ¥{portfolio['total_assets']:,.0f}, 日收益 ¥{portfolio['daily_return']:+,.0f}")
    return portfolio


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
