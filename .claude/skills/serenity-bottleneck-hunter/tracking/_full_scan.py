#!/usr/bin/env python3
"""完整 9 字段批量 scan(2026-06-02 加,用户抓错 off% 后纪律强化)
   输出 CSV-friendly 完整字段,严禁手填任何数字。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from price import analyze, fetch_history

def full_scan(sym):
    r = analyze(sym)
    if r.get("error"):
        return {"sym": sym, "error": r["error"][:80]}
    # 补 6m high/low 显式字段(用户算术 verify 用)
    data, _ = fetch_history(sym, days=400)
    if data:
        w6 = data[-126:] if len(data) >= 126 else data
        hi6 = max(x["high"] for x in w6)
        lo6 = min(x["low"] for x in w6)
        r["high_6mo"] = round(hi6, 2)
        r["low_6mo"] = round(lo6, 2)
        r["cur_div_high_pct"] = round(r["last"] / hi6 * 100, 1)  # 用户直觉:现价/高点
    return r

# Topic: 自动驾驶 L4 — 22 只 (复用 v1 候选清单)
AUTODRIVE = [
    "HSAI.US","LAZR.US","INVZ.US","AEVA.US","OUST.US","INDI.US","603501.SHG",
    "TRMB.US","HXGBY.US","MBLY.US","AMBA.US","NXPI.US","688256.SHG","AUR.US","CRNC.US",
    "ARM.US","CDNS.US","SNPS.US","MPWR.US","NVDA.US","TSLA.US","LI.US",
]

# Topic: AMR/无人机/视觉 — 21 只
AMR = [
    "SYM.US","AUTO.OL","CGNX.US","6861.T","002415.SHE","002236.SHE",
    "AVAV.US","JOBY.US","ACHR.US","EHGO.US","KTOS.US",
    "ISRG.US","SYK.US","DE.US","AGCO.US","CAT.US","ABBNY.US","AMZN.US",
    "ARM.US","MPWR.US","AMBA.US",
]

OUT_AUTO = os.path.join(HERE, "_scan_自动驾驶L4_v2.json")
OUT_AMR = os.path.join(HERE, "_scan_AMR_v2.json")

print(f"=== 自动驾驶 L4 完整扫描({len(AUTODRIVE)} 只)===")
auto_results = []
for s in AUTODRIVE:
    r = full_scan(s)
    auto_results.append(r)
    if "error" in r:
        print(f"  {s:<14} ERR: {r['error']}")
    else:
        print(f"  {s:<14} last=${r['last']:>8.2f} hi6=${r['high_6mo']:>8.2f} lo6=${r['low_6mo']:>8.2f} "
              f"rng={r['range_pos_6mo_pct']:>3}% off={r['pct_off_6mo_high']:>6.1f}% cur/hi={r['cur_div_high_pct']:>5.1f}% "
              f"1m={r['ret_1m_pct'] or 0:>6.1f}% 3m={r['ret_3m_pct'] or 0:>6.1f}%")
with open(OUT_AUTO, "w", encoding="utf-8") as f:
    json.dump(auto_results, f, ensure_ascii=False, indent=2)

print(f"\n=== AMR/无人机/视觉 完整扫描({len(AMR)} 只)===")
amr_results = []
for s in AMR:
    r = full_scan(s)
    amr_results.append(r)
    if "error" in r:
        print(f"  {s:<14} ERR: {r['error']}")
    else:
        print(f"  {s:<14} last=${r['last']:>8.2f} hi6=${r['high_6mo']:>8.2f} lo6=${r['low_6mo']:>8.2f} "
              f"rng={r['range_pos_6mo_pct']:>3}% off={r['pct_off_6mo_high']:>6.1f}% cur/hi={r['cur_div_high_pct']:>5.1f}% "
              f"1m={r['ret_1m_pct'] or 0:>6.1f}% 3m={r['ret_3m_pct'] or 0:>6.1f}%")
with open(OUT_AMR, "w", encoding="utf-8") as f:
    json.dump(amr_results, f, ensure_ascii=False, indent=2)

print(f"\n输出: {OUT_AUTO}")
print(f"     {OUT_AMR}")
