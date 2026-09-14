"""E08 v0.1 — 从交易截图 OCR 文本构建结构化台账 + FIFO 费用。

输入：PERSONAL_DATA_DIR/experiments/ledger/ocr/*.txt（tesseract chi_sim 输出）
      PERSONAL_DATA_DIR/portfolio.json（基金名对照 + 一致性检查）
输出：experiments/ledger/trades.json, trades.csv, mismatches.md, fee_summary.json

规则：
- 用户 2026-05 起开始交易 → OCR 的 2020/2025/其他年份一律按 2026 处理，原始年份保留在 ocr_year_raw；
  月份 <5 记为 month_suspect（待人工确认）。
- 同一条目在多张截图重复出现 → 按 (日期,时间,方向,基金,金额) 去重。
- FIFO：卖出按最早买入批次扣减；C 类赎回费 <7天 1.5% / 7-30天 0.5% / ≥30天 0。
"""
import csv
import difflib
import json
import os
import re

PD = os.environ.get("PERSONAL_DATA_DIR",
                    "/home/cc/Acai-Knowledge/workspace/personal-investment-data")
OCR = os.path.join(PD, "experiments", "ledger", "ocr")
OUT = os.path.join(PD, "experiments", "ledger")
PF = os.path.join(PD, "portfolio.json")

TRADE_RE = re.compile(r"^(买入|卖出|定投|转换)")
TS_RE = re.compile(r"(\d{4})[-–—.](\d{1,2})[-–—.](\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})")
AMT_RE = re.compile(r"([0-9][0-9.,]*)\s*(元|份)")


def clean_amount(raw):
    s = raw.replace(",", "")
    if s.count(".") > 1:
        # 形如 1.000.00（千分位 + 小数）→ 去掉除最后一个点以外的所有点
        s = s.replace(".", "", s.count(".") - 1)
    elif s.count(".") == 1:
        head, tail = s.split(".")
        if len(tail) == 3:
            s = head + tail
    try:
        return float(s)
    except ValueError:
        return None


def norm_name(name):
    n = re.sub(r"[\s|·•]", "", name)
    n = n.replace("（", "(").replace("）", ")")
    return n


def load_funds():
    pf = json.load(open(PF, encoding="utf-8"))
    funds = {}
    for h in pf.get("holdings", []):
        funds[h.get("fund_code") or h.get("fund_name")] = h.get("fund_name", "")
    return pf, funds


def parse_blocks():
    blocks = []
    files = sorted(f for f in os.listdir(OCR) if f.endswith(".txt") and not f.startswith("_"))
    for f in files:
        lines = [l.strip() for l in open(os.path.join(OCR, f), encoding="utf-8")]
        for i, line in enumerate(lines):
            if not TRADE_RE.match(line):
                continue
            ctx = lines[i:i + 4]
            ts = None
            for c in ctx:
                m = TS_RE.search(c)
                if m:
                    ts = m
                    break
            body = " ".join(ctx)
            am = None
            for c in ctx:
                found = AMT_RE.search(c)
                if found:
                    am = found
                    break
            if am is None:
                found = AMT_RE.search(body)
                am = found
            name = ""
            m2 = re.search(r"基金\s*[|｜]?\s*([^0-9]{2,30})", body)
            if m2:
                name = m2.group(1).strip()
            blocks.append({
                "file": f,
                "direction": TRADE_RE.match(line).group(1),
                "name_raw": name,
                "line": line,
                "amount_raw": (am.group(1) + am.group(2)) if am else None,
                "amount": clean_amount(am.group(1)) if am else None,
                "unit": am.group(2) if am else None,
                "date": f"2026-{int(ts.group(2)):02d}-{int(ts.group(3)):02d}" if ts else None,
                "time": f"{int(ts.group(4)):02d}:{ts.group(5)}:{ts.group(6)}" if ts else None,
                "ocr_year_raw": ts.group(1) if ts else None,
                "month_suspect": bool(ts and int(ts.group(2)) < 5),
            })
    return blocks


def main():
    pf, funds = load_funds()
    codes = list(funds.keys())
    names = [norm_name(v) for v in funds.values()]
    blocks = parse_blocks()

    for b in blocks:
        n = norm_name(b["name_raw"])
        best, score = None, 0.0
        for code, nm in zip(codes, names):
            s = difflib.SequenceMatcher(None, n, nm).ratio()
            if s > score:
                best, score = code, s
        b["fund_code"] = best if score >= 0.55 else None
        b["match_score"] = round(score, 2)
        b["fund_name"] = funds.get(best, "") if b["fund_code"] else None

    # 去重（跨截图重叠）
    seen = set()
    uniq = []
    for b in blocks:
        key = (b["date"], b["time"], b["direction"], b["fund_code"], b["amount"], b["unit"])
        if all(key):
            if key in seen:
                continue
            seen.add(key)
        uniq.append(b)

    uniq.sort(key=lambda x: ((x["date"] or "9999"), (x["time"] or "99")))

    # FIFO 费用
    lots = {}
    fee_rows = []
    total_fee = 0.0
    for b in uniq:
        if not b["fund_code"] or b["amount"] is None or not b["date"]:
            continue
        code = b["fund_code"]
        if b["direction"] in ("买入", "定投"):
            lots.setdefault(code, []).append({"date": b["date"], "shares": b["amount"], "price": None})
            continue
        if b["direction"] != "卖出":
            continue
        remaining = b["amount"]
        fee = 0.0
        from datetime import date as _d
        for lot in lots.get(code, []):
            if remaining <= 0:
                break
            take = min(lot["shares"], remaining)
            days = (_d.fromisoformat(b["date"]) - _d.fromisoformat(lot["date"])).days
            rate = 0.015 if days < 7 else (0.005 if days < 30 else 0.0)
            fee += take * rate  # 份额口径，按 1 元/份近似（真实金额=份额×净值，后续用净值精算）
            lot["shares"] -= take
            remaining -= take
        fee_rows.append({"date": b["date"], "fund_code": code, "sold_shares": b["amount"],
                         "unmatched_shares": round(max(0.0, remaining), 2), "fee_approx": round(fee, 2)})
        total_fee += fee

    os.makedirs(OUT, exist_ok=True)
    json.dump(uniq, open(os.path.join(OUT, "trades.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "trades.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "time", "direction", "fund_code", "fund_name",
                                           "amount", "unit", "amount_raw", "name_raw", "match_score",
                                           "month_suspect", "file"])
        w.writeheader()
        for b in uniq:
            w.writerow({k: b.get(k) for k in w.fieldnames})

    # 交叉检查：与 portfolio/action_log 已知交易
    known = []
    for e in pf.get("action_log", []):
        known.append({"date": e.get("date"), "action": e.get("action"), "fund": e.get("fund"),
                      "reason": e.get("reason")})
    ledger_dates = {}
    for b in uniq:
        if b["date"]:
            ledger_dates.setdefault(b["date"], 0)
            ledger_dates[b["date"]] += 1
    unmatched = [b for b in uniq if not b["fund_code"]]
    month_suspect = [b for b in uniq if b["month_suspect"]]
    no_date = [b for b in uniq if not b["date"]]

    summary = {
        "raw_blocks": len(blocks),
        "unique_entries": len(uniq),
        "unmatched_fund_entries": len(unmatched),
        "month_suspect_entries": len(month_suspect),
        "no_date_entries": len(no_date),
        "date_min": min(ledger_dates) if ledger_dates else None,
        "date_max": max(ledger_dates) if ledger_dates else None,
        "entries_by_month": {m: sum(v for d, v in ledger_dates.items() if d[5:7] == m)
                             for m in sorted({d[5:7] for d in ledger_dates})},
        "sell_fee_approx_total": round(total_fee, 2),
        "note": "fee_approx 以 1 元/份近似；真实费用需用当日净值重算",
    }
    json.dump({"summary": summary, "fee_rows": fee_rows}, open(
        os.path.join(OUT, "fee_summary.json"), "w"), ensure_ascii=False, indent=1)

    with open(os.path.join(OUT, "mismatches.md"), "w", encoding="utf-8") as fh:
        fh.write("# 台账待确认项\n\n")
        fh.write(f"- 原始条目 {len(blocks)}，去重后 {len(uniq)}（重叠截图重复 {len(blocks)-len(uniq)}）\n")
        fh.write(f"- 基金名未匹配：{len(unmatched)}\n\n")
        for b in unmatched[:40]:
            fh.write(f"  - {b['date']} {b['time']} {b['direction']} {b['name_raw']!r} {b['amount']}{b['unit'] or ''}\n")
        fh.write(f"\n- 月份 <5 可疑（可能 OCR 误读）：{len(month_suspect)}\n\n")
        for b in month_suspect[:40]:
            fh.write(f"  - {b['date']} {b['time']} {b['direction']} {b['fund_name'] or b['name_raw']} {b['amount']}{b['unit'] or ''}\n")
        fh.write(f"\n- 无日期条目：{len(no_date)}\n")

    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("unmatched:", [(b["date"], b["name_raw"][:20], b["amount"]) for b in unmatched[:15]])
    print("month_suspect:", [(b["date"], (b["fund_name"] or b["name_raw"])[:16], b["amount"]) for b in month_suspect[:15]])
    print("saved to", OUT)


if __name__ == "__main__":
    main()
