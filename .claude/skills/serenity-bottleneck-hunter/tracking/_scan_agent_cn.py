#!/usr/bin/env python3
"""AI Agent 经济(A 股 + 港股)主题广扫 — 2026-06-02 / Dogfood #11
   严格走 price.py 完整 EODHD→yfinance fallback,9 字段输出"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from price import analyze, fetch_history

def full(sym):
    r = analyze(sym)
    if r.get("error"): return {"sym": sym, "error": r["error"][:90]}
    data, _ = fetch_history(sym, days=400)
    if data:
        w6 = data[-126:] if len(data) >= 126 else data
        r["high_6mo"] = round(max(x["high"] for x in w6), 2)
        r["low_6mo"] = round(min(x["low"] for x in w6), 2)
        r["cur_div_high_pct"] = round(r["last"] / r["high_6mo"] * 100, 1)
    return r

# 6 层广扫 — A 股 + 港股 AI Agent 已知玩家全集
SYMBOLS = [
    # 上游 LLM + GPU/AI 芯片
    ("688256.SHG", "寒武纪 AI 芯片(跨自动驾驶)"),
    ("688041.SHG", "海光信息 AI/CPU 芯片国产替代"),
    ("300308.SHE", "中际旭创 光模块龙头"),
    ("000977.SHE", "浪潮信息 AI 服务器+海若大模型"),
    ("603019.SHG", "中科曙光 AI 服务器"),
    ("603296.SHG", "华勤技术 AI 服务器代工"),
    # 中游 infra(云/数据/安全)
    ("688158.SHG", "优刻得 UCloud AI云"),
    ("300229.SHE", "拓尔思 政务/媒体 NLP"),
    ("688787.SHG", "海天瑞声 AI 数据集"),
    ("688561.SHG", "奇安信 网络安全+AI 安全护栏"),
    ("002439.SHE", "启明星辰 网络安全"),
    ("688030.SHG", "山石网科 网络安全"),
    # 中游应用(SaaS + 行业 Agent)
    ("688111.SHG", "金山办公 WPS AI"),
    ("600588.SHG", "用友网络 YonGPT 企业级"),
    ("0268.HK", "金蝶国际 苍穹+AI Agent"),
    ("300033.SHE", "同花顺 i问财 金融 Agent"),
    ("002410.SHE", "广联达 建筑 SaaS+AI"),
    ("603039.SHG", "泛微网络 OA+AI"),
    ("688369.SHG", "致远互联 协同 OA+AI"),
    ("002315.SHE", "焦点科技 跨境电商+AI"),
    ("2013.HK", "微盟集团 营销 SaaS+AI"),
    ("0020.HK", "商汤 商量大模型"),
    ("1357.HK", "美图公司 美图秀秀 AI"),
    # 下游 LLM 巨头(跳过对照)
    ("9988.HK", "阿里巴巴 通义千问+百炼"),
    ("0700.HK", "腾讯 混元大模型"),
    ("9888.HK", "百度 文心一言"),
    ("3690.HK", "美团 LongCat+内部 agents"),
    ("9618.HK", "京东 言犀大模型"),
]

print(f"扫描 {len(SYMBOLS)} 只 — AI Agent 经济(A股+港股)")
print(f"{'SYMBOL':<14} {'PROV':<10} {'LAST':>12} {'HI6':>12} {'LO6':>12} {'RNG':>4} {'OFF':>7} {'C/H':>6} {'1M':>7} {'3M':>7} STAGE NAME")
print("-" * 175)

results = []
for sym, name in SYMBOLS:
    r = full(sym)
    results.append(r)
    if "error" in r:
        print(f"  {sym:<14} ERR: {r['error']}")
        continue
    s = r["stage"]
    short = "ext" if "extend" in s else ("early" if "early" in s else ("range" if "range" in s or "basing" in s else "down"))
    print(f"  {sym:<14} {r['provider']:<10} {r['last']:>12.2f} {r['high_6mo']:>12.2f} {r['low_6mo']:>12.2f} "
          f"{r['range_pos_6mo_pct']:>4} {r['pct_off_6mo_high']:>7.1f}% {r['cur_div_high_pct']:>5.1f}% "
          f"{r['ret_1m_pct'] or 0:>7.1f} {r['ret_3m_pct'] or 0:>7.1f} {short:<6} {name}")

out = os.path.join(HERE, "_scan_AIAgent_CN_v1.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n输出: {out}")
