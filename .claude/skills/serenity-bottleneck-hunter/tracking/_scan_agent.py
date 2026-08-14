#!/usr/bin/env python3
"""AI Agent 经济主题广扫(穷尽性 — 已知玩家全集,2026-06-02 跑)"""
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

# 6 层广扫 — 已知玩家全集(2026-06-02)
SYMBOLS = [
    # Layer 6 IP/EDA(必扫跨主题)
    ("ARM.US", "ARM IP - 跨主题"),
    ("CDNS.US", "Cadence EDA - 跨主题"),
    ("SNPS.US", "Synopsys EDA - 跨主题"),
    # Layer 5 下游对照(LLM 巨头/超大规模厂商,跳过)
    ("MSFT.US", "Microsoft Copilot Studio/Foundry"),
    ("GOOGL.US", "Google Gemini Agents"),
    ("META.US", "Meta Llama"),
    ("AMZN.US", "AWS Bedrock Agents"),
    ("NVDA.US", "NVIDIA NIM/AI Workbench"),
    # Layer 4 中游系统 - Agent 软件平台/应用层
    ("CRM.US", "Salesforce Agentforce"),
    ("PLTR.US", "Palantir AIP"),
    ("NOW.US", "ServiceNow Now Assist"),
    ("HUBS.US", "HubSpot AI agents"),
    ("MNDY.US", "monday.com AI workflow"),
    ("NICE.US", "NICE 客服 AI"),
    ("PATH.US", "UiPath RPA+AI"),
    ("APPN.US", "Appian"),
    ("ZI.US", "ZoomInfo 销售 AI"),
    ("BILL.US", "BILL Holdings 财务 AI"),
    # Layer 3 中游器件 - Agent infrastructure(observability/gateway/向量库/RAG/搜索)
    ("DDOG.US", "Datadog LLM observability"),
    ("MDB.US", "MongoDB Atlas Vector - RAG"),
    ("NET.US", "Cloudflare AI Gateway + Workers AI"),
    ("FSLY.US", "Fastly edge"),
    ("ESTC.US", "Elastic search + vector"),
    ("CFLT.US", "Confluent streaming"),
    ("SNOW.US", "Snowflake Cortex AI"),
    ("DBX.US", "Dropbox AI - 文档 Agent"),
    ("ZS.US", "Zscaler AI 安全"),
    ("S.US", "SentinelOne AI 安全"),
    # Layer 2-1 LLM-related 应用 / 数据
    ("AI.US", "C3.ai 企业 AI"),
    ("SOUN.US", "SoundHound 语音 AI"),
    ("APP.US", "AppLovin AI 广告"),
    ("GTLB.US", "GitLab Duo 开发者"),
    ("FROG.US", "JFrog Software Supply"),
    # 跨主题 (复用)
    ("MPWR.US", "MPWR PMIC 跨多主题"),
    # 已识别但跳过 / 私有
    # OpenAI / Anthropic / xAI - 全部私有
    # LangChain / LlamaIndex / Pinecone / Weaviate - 全部私有
    # Cursor / Replit Agent / Devin - 私有
    # Braintrust / LangSmith / Patronus - 私有
]

print(f"扫描 {len(SYMBOLS)} 只 — AI Agent 经济主题")
print(f"{'SYMBOL':<12} {'PROV':<10} {'LAST':>9} {'HI6':>9} {'LO6':>9} {'RNG':>4} {'OFF':>7} {'C/H':>6} {'1M':>7} {'3M':>7} STAGE NAME")
print("-" * 165)

results = []
for sym, name in SYMBOLS:
    r = full(sym)
    results.append(r)
    if "error" in r:
        print(f"  {sym:<12} ERR: {r['error']}")
        continue
    s = r["stage"]
    short = "ext" if "extend" in s else ("early" if "early" in s else ("range" if "range" in s or "basing" in s else "down"))
    print(f"  {sym:<12} {r['provider']:<10} {r['last']:>9.2f} {r['high_6mo']:>9.2f} {r['low_6mo']:>9.2f} "
          f"{r['range_pos_6mo_pct']:>4} {r['pct_off_6mo_high']:>7.1f}% {r['cur_div_high_pct']:>5.1f}% "
          f"{r['ret_1m_pct'] or 0:>7.1f} {r['ret_3m_pct'] or 0:>7.1f} {short:<6} {name}")

out = os.path.join(HERE, "_scan_AIAgent_v1.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n输出: {out}")
