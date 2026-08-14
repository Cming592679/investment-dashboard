#!/usr/bin/env python3
"""检查 company_desc.md 里 business 描述的 freshness(2026-06-02 加,用户挑战 driven)

纪律:business 描述也不是真正永久 — 公司战略每 2-3 年会调整(如 Salesforce 从纯 CRM → 加 Slack → Agentforce)。
所以每条 entry 带 [YYYY-MM-DD] last_updated 时间戳,**超过 90 天必须重新评估**。

用法:
  python tracking/check_desc_freshness.py
  → 列出所有 > 90 天的过期 entry,提示 LLM 在下次报告生成前 update。
"""
import os, re
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DESC_FILE = os.path.join(HERE, "..", "reference", "company_desc.md")
STALE_THRESHOLD_DAYS = 90

def main():
    if not os.path.exists(DESC_FILE):
        print(f"❌ {DESC_FILE} 不存在")
        return 1

    with open(DESC_FILE, encoding="utf-8") as f:
        content = f.read()

    # 匹配格式:- **SYMBOL** [YYYY-MM-DD] = description
    pattern = re.compile(r'- \*\*([\w\.\-]+)\*\* \[(\d{4}-\d{2}-\d{2})\] = (.+)')
    entries = pattern.findall(content)

    today = datetime.now()
    stale = []
    fresh = []
    very_stale = []

    for sym, date_str, desc in entries:
        last_updated = datetime.strptime(date_str, "%Y-%m-%d")
        age_days = (today - last_updated).days
        item = (sym, date_str, age_days, desc[:60])
        if age_days > STALE_THRESHOLD_DAYS * 2:  # > 180 天
            very_stale.append(item)
        elif age_days > STALE_THRESHOLD_DAYS:  # 90-180 天
            stale.append(item)
        else:
            fresh.append(item)

    print("=" * 80)
    print(f"Company Desc Freshness Check ({today.strftime('%Y-%m-%d')})")
    print(f"  · 阈值:{STALE_THRESHOLD_DAYS} 天")
    print(f"  · 总 entry:{len(entries)}")
    print("=" * 80)
    print()

    print(f"✅ FRESH(≤ {STALE_THRESHOLD_DAYS} 天):{len(fresh)} 条 — 可直接复用")
    print(f"⚠️  STALE({STALE_THRESHOLD_DAYS}-{STALE_THRESHOLD_DAYS*2} 天):{len(stale)} 条 — 建议 update")
    print(f"🚨 VERY STALE(> {STALE_THRESHOLD_DAYS*2} 天):{len(very_stale)} 条 — 必须 update + 重检战略")
    print()

    if very_stale:
        print("🚨 VERY STALE entries — 必须 update:")
        print("-" * 80)
        for sym, date, age, desc in very_stale:
            print(f"  {sym:<14} [{date}] ({age:>4} 天) — {desc}...")
        print()

    if stale:
        print("⚠️  STALE entries — 建议 update:")
        print("-" * 80)
        for sym, date, age, desc in stale:
            print(f"  {sym:<14} [{date}] ({age:>4} 天) — {desc}...")
        print()

    if not stale and not very_stale:
        print("✓ 所有 entry 都在 fresh 区间(≤ 90 天)。无需 update。")
    else:
        print(f"\n建议:LLM 在下次报告生成前,对 {len(stale)+len(very_stale)} 条 STALE entry:")
        print(f"  1. 查最新公司战略 / 财报 / 业务调整")
        print(f"  2. 若 business 有重大变化 → update 描述 + bump 时间戳")
        print(f"  3. 若无变化 → 只 bump 时间戳到当前 {today.strftime('%Y-%m-%d')}")

    return 0

if __name__ == "__main__":
    exit(main())
