"""E08c — 用净值把台账换算成份额，FIFO 精算赎回费，并与 portfolio.json 对账。

输入：ledger/trades.json, ledger/fund_resolution.json, ledger/fund_navs_ledger.json,
      PERSONAL_DATA_DIR/portfolio.json, experiments/market_data/fund_navs.json
输出：ledger/reconcile.json, ledger/reconcile.md
"""
import json
import os
import re
from collections import defaultdict
from datetime import date as _date

PD = os.environ.get("PERSONAL_DATA_DIR",
                    "/home/cc/Acai-Knowledge/workspace/personal-investment-data")
LEDGER = os.path.join(PD, "experiments", "ledger")
CUR = os.path.join(PD, "portfolio.json")
E01_NAVS = os.path.join(PD, "experiments", "market_data", "fund_navs.json")


def clean(name):
    return re.sub(r"[\s|·•]", "", name or "").replace("（", "(").replace("）", ")")


def build_nav_lookup(navs_map):
    out = {}
    for code, rows in navs_map.items():
        if isinstance(rows, dict):
            rows = rows.get("rows", [])
        m = {}
        for r in rows:
            if isinstance(r, dict) and "d" in r and "nav" in r:
                m[r["d"]] = r["nav"]
        out[code] = m
    return out


def nav_on(lookup, code, d):
    m = lookup.get(code)
    if not m or not d:
        return None
    if d in m:
        return m[d]
    cands = [k for k in m if k <= d]
    if not cands:
        return None
    k = max(cands)
    if (_date.fromisoformat(d) - _date.fromisoformat(k)).days > 10:
        return None
    return m[k]


def main():
    trades = json.load(open(os.path.join(LEDGER, "trades.json"), encoding="utf-8"))
    resolution = json.load(open(os.path.join(LEDGER, "fund_resolution.json"), encoding="utf-8"))
    navs = json.load(open(os.path.join(LEDGER, "fund_navs_ledger.json"), encoding="utf-8"))
    try:
        navs.update(json.load(open(E01_NAVS, encoding="utf-8")))
    except Exception:
        pass
    navs["006479"] = navs.get("006479", [])
    lookup = build_nav_lookup(navs)
    pf = json.load(open(CUR, encoding="utf-8"))
    held = {h.get("fund_code"): h for h in pf.get("holdings", [])}

    for t in trades:
        code = t.get("fund_code")
        if not code:
            nm = clean(t.get("name_raw") or "")
            r = resolution.get(nm)
            if r and r.get("code"):
                code = r["code"]
            elif "广发纳斯达克" in nm:
                code = "006479"
        t["code"] = code

    lots = defaultdict(list)
    fee_by_month = defaultdict(float)
    flags = []
    buys = defaultdict(float)
    sells = defaultdict(float)
    for t in trades:
        code, d, unit, amt = t["code"], t["date"], t["unit"], t["amount"]
        if not code or not d or amt is None:
            flags.append({"reason": "missing_code_or_date", "t": t})
            continue
        nav = nav_on(lookup, code, d)
        if nav is None:
            flags.append({"reason": "missing_nav", "t": t})
            continue
        if t["direction"] in ("买入", "定投"):
            shares = amt / nav
            lots[code].append({"date": d, "shares": shares, "nav": nav})
            buys[code] += shares
        elif t["direction"] == "卖出":
            shares = amt if unit == "份" else amt / nav
            sells[code] += shares
            remaining = shares
            fee = 0.0
            for lot in lots[code]:
                if remaining <= 1e-9:
                    break
                take = min(lot["shares"], remaining)
                days = (_date.fromisoformat(d) - _date.fromisoformat(lot["date"])).days
                rate = 0.015 if days < 7 else (0.005 if days < 30 else 0.0)
                fee += take * nav * rate
                lot["shares"] -= take
                remaining -= take
            fee_by_month[d[:7]] += fee
            if remaining > 1e-6:
                flags.append({"reason": "sell_exceeds_lots", "code": code, "date": d,
                              "unmatched_shares": round(remaining, 2)})

    rows = []
    for code in sorted(set(list(buys) + list(sells) + list(held))):
        net = buys.get(code, 0.0) - sells.get(code, 0.0)
        h = held.get(code)
        rows.append({
            "code": code,
            "name": (h or {}).get("fund_name") or (resolution.get(code) or {}).get("name"),
            "ledger_buy_shares": round(buys.get(code, 0.0), 2),
            "ledger_sell_shares": round(sells.get(code, 0.0), 2),
            "ledger_net_shares": round(net, 2),
            "portfolio_shares": round(h.get("shares", 0.0), 2) if h else None,
            "diff": round(net - h.get("shares", 0.0), 2) if h else None,
            "status": (h or {}).get("status"),
        })
    rows.sort(key=lambda r: -abs(r["diff"] or 0))

    out = {
        "entries": len(trades),
        "flagged": len(flags),
        "fee_by_month": {k: round(v, 2) for k, v in sorted(fee_by_month.items())},
        "fee_total": round(sum(fee_by_month.values()), 2),
        "rows": rows,
        "flags": [{"reason": f["reason"],
                   "date": f.get("t", {}).get("date") or f.get("date"),
                   "name": f.get("t", {}).get("name_raw") or (f.get("code") or ""),
                   "amount": f.get("t", {}).get("amount") if f.get("t") else f.get("unmatched_shares"),
                   "code": f.get("code") or f.get("t", {}).get("code")} for f in flags],
    }
    json.dump(out, open(os.path.join(LEDGER, "reconcile.json"), "w"), ensure_ascii=False, indent=1)

    with open(os.path.join(LEDGER, "reconcile.md"), "w", encoding="utf-8") as fh:
        fh.write("# 台账 vs 持仓 对账\n\n")
        fh.write(f"- 条目 {out['entries']}，无法计算 {out['flagged']}\n")
        fh.write(f"- FIFO 赎回费合计（2026-05~09，按当日净值）≈ ¥{out['fee_total']:.2f}\n\n")
        fh.write("## 费用按月\n\n")
        for k, v in out["fee_by_month"].items():
            fh.write(f"- {k}: ¥{v:.2f}\n")
        fh.write("\n## 份额对账（差额 = 台账净份额 − 当前持仓份额）\n\n")
        fh.write("| 代码 | 名称 | 台账净份额 | 当前持仓 | 差额 | 状态 |\n|---|---|---|---|---|---|\n")
        for r in rows:
            fh.write(f"| {r['code']} | {r['name']} | {r['ledger_net_shares']} | "
                     f"{r['portfolio_shares']} | {r['diff']} | {r['status']} |\n")
        fh.write("\n## 需确认项\n\n")
        for f in out["flags"]:
            fh.write(f"- {f['reason']}: {f['date']} {f['name']} {f['amount']}\n")

    print(json.dumps({k: out[k] for k in ("entries", "flagged", "fee_total", "fee_by_month")},
                     ensure_ascii=False, indent=1))
    print("top diffs:")
    for r in rows[:12]:
        print("  ", r["code"], (r["name"] or "")[:18], "ledger", r["ledger_net_shares"],
              "vs pf", r["portfolio_shares"], "diff", r["diff"])
    print("flags:", len(out["flags"]))


if __name__ == "__main__":
    main()
