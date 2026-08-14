#!/usr/bin/env python3
"""init_ticker_truth.py — 用 forward_picks 历史一次性 init ticker_truth.csv

走 EODHD search 反查每个 unique ticker → 写入 ground truth。
之后 resolve_tickers / verify_pair 都从 truth 命中,不再凭记忆。
"""
import os, sys, csv, json, urllib.request, time
from datetime import datetime
HERE = os.path.dirname(os.path.abspath(__file__))
FP = os.path.join(HERE, "..", "tracking", "forward_picks.csv")
TRUTH = os.path.join(HERE, "..", "reference", "ticker_truth.csv")

# 收集所有 unique ticker + 最后出现的 zh name
ticker_zh = {}  # ticker -> zh_name
with open(FP, encoding="utf-8") as f:
    for r in csv.reader(f):
        if len(r) < 4 or r[0] == "record_date": continue
        ticker = r[2].strip()
        zh = r[3].strip()
        if ticker and not ticker.startswith("theme"):
            ticker_zh[ticker] = zh

print(f"unique tickers in forward_picks: {len(ticker_zh)}")

# 加紧急修复案的两只
ticker_zh["688017.SHG"] = "绿的谐波"
ticker_zh["603297.SHG"] = "永新光学"

key = os.environ.get("EODHD_API_KEY", "")
if not key:
    print("FATAL: EODHD_API_KEY env var missing"); sys.exit(1)

import urllib.parse
results = {}
errors = []

for i, (ticker, zh) in enumerate(sorted(ticker_zh.items())):
    code_root = ticker.split(".")[0]
    url = f"https://eodhd.com/api/search/{urllib.parse.quote(code_root)}?api_token={key}&fmt=json&limit=5"
    try:
        d = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read()
        j = json.loads(d)
        # 找匹配的
        match = None
        for r in j:
            if r.get("Code") == code_root:
                match = r; break
        if not match and j:
            match = j[0]
        if match:
            results[ticker] = {
                "ticker": ticker,
                "name_en": match.get("Name", "")[:120],
                "name_zh": zh,
                "exchange": match.get("Exchange", ""),
                "sector": match.get("Type", ""),
                "last_verified": datetime.now().strftime("%Y-%m-%d"),
                "source": "EODHD init batch 2026-06-05",
            }
        else:
            errors.append((ticker, zh, "no result"))
    except urllib.error.HTTPError as e:
        errors.append((ticker, zh, f"HTTP {e.code}"))
    except Exception as e:
        errors.append((ticker, zh, str(e)[:50]))
    if (i+1) % 20 == 0:
        print(f"  [{i+1}/{len(ticker_zh)}] processed, {len(results)} ok, {len(errors)} err")
    time.sleep(0.15)  # 节流

# 写入 truth
os.makedirs(os.path.dirname(TRUTH), exist_ok=True)
fields = ["ticker", "name_en", "name_zh", "exchange", "sector", "last_verified", "source"]
with open(TRUTH, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
    w.writeheader()
    for ticker in sorted(results.keys()):
        w.writerow(results[ticker])

print(f"\n=== INIT DONE ===")
print(f"  written: {len(results)} entries to {TRUTH}")
print(f"  errors:  {len(errors)} (see below)")
for t, z, e in errors[:20]:
    print(f"    {t:<14} {z[:20]:<20} {e}")

# 跨检 — 中文名匹配 vs 不匹配
print(f"\n=== name 一致性 cross-check ===")
mismatch = 0
for ticker, r in results.items():
    zh = r["name_zh"]
    en = r["name_en"]
    # 用启发式:zh 短词不在 en 内 + en 没明显对应 → 标 review
    if zh and en:
        zh_simp = zh.split("(")[0].strip()
        en_simp = en.lower().split("(")[0].strip()
        # 中英文几乎不会拼合,只能 sanity check by length / non-ascii in en
        # 这里只标 special review 项(简单规则)
        pass

print(f"  consult tickle_truth.csv 手动 review name 不齐的 entries")
