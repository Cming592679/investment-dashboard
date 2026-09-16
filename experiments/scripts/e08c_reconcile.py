"""E08c v0.3 — 台账对账：全局/单基金页 + 清仓明细页 统一换算份额，FIFO 费用。

输入：ledger/trades.json, ledger/closed_txns.json, ledger/fund_resolution.json,
      ledger/fund_navs_ledger.json, experiments/market_data/fund_navs.json, portfolio.json
输出：ledger/reconcile.json, ledger/reconcile.md

规则：
- 清仓明细页（closed_txns）自带「份额」，对已清仓基金以其为准；
- 全局/单基金页按 金额÷净值 换算份额（卖出为「份」时直接用份额）；
- 目标：active 基金对齐 portfolio.json 份额；sold 基金对齐 0。
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
    closed_txns = json.load(open(os.path.join(LEDGER, "closed_txns.json"), encoding="utf-8"))
    resolution = json.load(open(os.path.join(LEDGER, "fund_resolution.json"), encoding="utf-8"))
    navs = json.load(open(os.path.join(LEDGER, "fund_navs_ledger.json"), encoding="utf-8"))
    try:
        navs.update(json.load(open(E01_NAVS, encoding="utf-8")))
    except Exception:
        pass
    navs["006479"] = navs.get("006479", [])
    lookup = build_nav_lookup(navs)
    pf = json.load(open(CUR, encoding="utf-8"))
    held = {h.get("fund_code"): h for h in pf.get("holdings", []) if h.get("fund_code")}

    # name → code（基金解析 + 持仓）
    # 优先用持仓正确名称（避免 OCR 名模糊匹配到同类基金的错误份额/变体，如 021608 vs 021169）
    held_name2code = {}
    for code, h in held.items():
        held_name2code[clean(h.get("fund_name") or "")] = code
    name2code = {}
    for k, v in resolution.items():
        if v.get("code"):
            name2code[clean(k)] = v["code"]
            name2code[clean(v.get("name") or "")] = v["code"]

    def resolve_code(name):
        c = clean(name)
        if c in held_name2code:
            return held_name2code[c]
        # 优先对持仓名称做模糊（difflib），避免同族基金误配
        import difflib
        best, best_s = None, 0.0
        for k, code in held_name2code.items():
            s = difflib.SequenceMatcher(None, c, k).ratio()
            if len(c) >= 4 and (k.startswith(c) or c in k or k in c):
                s = max(s, 0.9)
            if s > best_s:
                best, best_s = code, s
        if best and best_s >= 0.55:
            return best
        if c in name2code:
            return name2code[c]
        for k, code in name2code.items():
            if len(c) >= 4 and (k.startswith(c) or c in k or k in c):
                return code
        return None

    # 持仓基金代码集合 + 清仓页涉及基金
    closed_funds = set()
    for t in closed_txns:
        code = resolve_code(t.get("name_raw") or "")
        if code:
            t["code"] = code
            closed_funds.add(code)

    buys = defaultdict(float)
    sells = defaultdict(float)
    conversions_out = defaultdict(float)
    conversions_in = defaultdict(float)

    # 清仓明细页（买入用 金额÷净值 重算；卖出用『份』）
    # 注意：转换只从全局列表统计（13 笔），此处不处理，避免与全局列表重复计数。
    for t in closed_txns:
        code = t.get("code")
        if not code:
            continue
        if t["direction"] == "买入":
            nav, amt = t.get("nav"), t.get("amount")
            buys[code] += (amt / nav) if (nav and amt) else (t.get("shares") or 0)
        elif t["direction"] == "卖出":
            sells[code] += (t.get("shares") or 0)

    # 全局/单基金页（仅对非清仓基金用金额÷净值；清仓基金跳过，避免重复计数）
    for t in trades:
        code = t.get("fund_code")
        if not code:
            code = resolve_code(t.get("name_raw") or "")
        # 全局列表里的『转换 A -> B』：转出 A 减份额，转入 B 加份额（近似 1:1）
        if t["direction"] == "转换":
            raw = t.get("name_raw") or ""
            parts = re.split(r"->|→|—>|–>|—|–", raw)
            out_code = resolve_code(parts[0]) if parts else None
            in_code = resolve_code(parts[1]) if len(parts) > 1 else None
            sh = t.get("amount") or 0
            d = t.get("date")
            if out_code:
                conversions_out[out_code] += sh
            if in_code:
                # 转入份额按价值换算：sh × 转出净值 ÷ 转入净值
                out_nav = nav_on(lookup, out_code, d) if out_code else None
                in_nav = nav_on(lookup, in_code, d)
                in_sh = sh
                if out_nav and in_nav:
                    in_sh = sh * out_nav / in_nav
                conversions_in[in_code] += in_sh
            continue
        if not code or code in closed_funds:
            continue
        d, amt, unit = t.get("date"), t.get("amount"), t.get("unit")
        if not d or amt is None:
            continue
        nav = nav_on(lookup, code, d)
        if t["direction"] in ("买入", "定投"):
            if nav:
                buys[code] += amt / nav
        elif t["direction"] == "卖出":
            if unit == "份":
                sells[code] += amt
            elif nav:
                sells[code] += amt / nav

    rows = []
    all_codes = set(buys) | set(sells) | set(held) | set(conversions_out) | set(conversions_in)
    for code in sorted(all_codes):
        net = buys.get(code, 0) - sells.get(code, 0) - conversions_out.get(code, 0) + conversions_in.get(code, 0)
        h = held.get(code)
        target = h.get("shares", 0.0) if h else 0.0
        status = (h or {}).get("status", "sold")
        rows.append({
            "code": code,
            "name": (h or {}).get("fund_name") or "",
            "ledger_net": round(net, 2),
            "target": round(target, 2),
            "diff": round(net - target, 2),
            "status": status,
            "conversions_out": round(conversions_out.get(code, 0), 2),
            "conversions_in": round(conversions_in.get(code, 0), 2),
        })
    rows.sort(key=lambda r: -abs(r["diff"]))

    # FIFO 费用（用统一份额口径；清仓基金用其份额，active 用金额/净值）
    lots = defaultdict(list)
    fee_total = 0.0
    fee_by_month = defaultdict(float)

    def add_lot(code, d, sh):
        lots[code].append({"date": d, "shares": sh})

    def settle(code, d, sh):
        nonlocal fee_total
        remaining = sh
        fee = 0.0
        for lot in lots[code]:
            if remaining <= 1e-9:
                break
            take = min(lot["shares"], remaining)
            days = (_date.fromisoformat(d) - _date.fromisoformat(lot["date"])).days
            rate = 0.015 if days < 7 else (0.005 if days < 30 else 0.0)
            fee += take * rate
            lot["shares"] -= take
            remaining -= take
        fee_total += fee
        fee_by_month[d[:7]] += fee
        return fee

    # 按时间排序处理（closed 优先按日期）
    events = []
    for t in closed_txns:
        if t.get("code") and t.get("date"):
            events.append((t["date"], t["direction"], t["code"],
                           t.get("shares") or 0, "closed"))
    for t in trades:
        code = t.get("fund_code") or resolve_code(t.get("name_raw") or "")
        if code and code not in closed_funds and t.get("date") and t.get("amount") is not None:
            nav = nav_on(lookup, code, t["date"])
            sh = (t["amount"] / nav) if nav else 0
            if t["unit"] == "份":
                sh = t["amount"]
            events.append((t["date"], t["direction"], code, sh, "global"))
    events.sort(key=lambda e: e[0])
    for d, direction, code, sh, src in events:
        if direction in ("买入", "定投"):
            add_lot(code, d, sh)
        elif direction == "卖出":
            settle(code, d, sh)
        # 转换暂不计费（份额迁移）

    out = {
        "entries": len(trades),
        "closed_txns": len(closed_txns),
        "fee_total": round(fee_total, 2),
        "fee_by_month": {k: round(v, 2) for k, v in sorted(fee_by_month.items())},
        "rows": rows,
    }
    json.dump(out, open(os.path.join(LEDGER, "reconcile.json"), "w"), ensure_ascii=False, indent=1)

    print(f"fee_total={out['fee_total']} {out['fee_by_month']}")
    for r in rows[:18]:
        print(f"  {r['code']} {(r['name'] or '')[:20]:22s} ledger={r['ledger_net']:>10.2f} "
              f"target={r['target']:>10.2f} diff={r['diff']:>+10.2f} [{r['status']}]"
              f" conv_out={r['conversions_out']} conv_in={r['conversions_in']}")


if __name__ == "__main__":
    main()
