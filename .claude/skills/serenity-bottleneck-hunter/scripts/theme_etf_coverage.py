#!/usr/bin/env python3
"""theme_etf_coverage.py — 主题穷尽性 audit 工具(2026-06-02 加)

用途:每个新主题开始 forward_picks 扫描前,必须先跑这个,产出"主题已知玩家全集"。
这是穷尽性纪律 A+ 的工具化兜底,避免凭记忆扫导致 PANW/CRWD 级别的漏标。

方法:
  1. 给定主题 ETF 清单 + 关键词
  2. 走 stockanalysis.com/etf/SYMBOL/holdings/ 拉每个 ETF 的 top 25 持仓
  3. 合并 + dedupe → 主题已知玩家全集
  4. 跟 forward_picks 已覆盖清单做 diff → 输出"漏标候选"

用法:
  python scripts/theme_etf_coverage.py --etfs IGV,CIBR,WCLD,AIQ --theme "AIAgent美国"
  → 打印漏标候选清单,LLM 必须人工分类(产业链层 + Serenity 原型)再决定纳入

注意:
  - stockanalysis.com 免费版只显示 top 25 holdings — 是足够的(主仓占总权重 >70%)
  - ETF 的小权重持仓(<0.5%)即使漏掉,通常是 me-too,不构成 Serenity 候选
  - 反过来:**所有 top 25 持仓必须 100% audit**,这是硬纪律
"""
import os, sys, csv, urllib.request, urllib.error, json, re, argparse
HERE = os.path.dirname(os.path.abspath(__file__))


def fetch_etf_holdings(etf_symbol):
    """从 stockanalysis.com 拉 ETF top 25 持仓。
    返回 [(ticker, name, weight_pct), ...] 列表"""
    url = f"https://stockanalysis.com/etf/{etf_symbol.lower()}/holdings/"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        })
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        print(f"[{etf_symbol}] HTTP {e.code}: {e.reason}")
        return []
    except Exception as e:
        print(f"[{etf_symbol}] error: {e}")
        return []

    # stockanalysis.com 的 holdings table 行结构 (简化版,实际页面用 JSON-LD or table rows)
    # 用 ticker pattern + weight pattern 抓
    rows = []
    # pattern: 行 contains ticker (uppercase 1-5 letters) followed by name + weight%
    # 简单兜底:抓所有 `>TICKER<` 后面跟 % 的项
    pattern = re.compile(r'>\s*([A-Z]{1,5}(?:\.[A-Z])?)\s*<.*?(\d{1,2}\.\d{2})\s*%', re.DOTALL)
    for m in pattern.finditer(html):
        tk = m.group(1)
        wt = float(m.group(2))
        if 0.1 < wt < 50 and len(tk) <= 5:  # filter noise
            rows.append((tk, "", wt))
    # dedupe by ticker, keep highest weight
    seen = {}
    for tk, n, w in rows:
        if tk not in seen or seen[tk][2] < w:
            seen[tk] = (tk, n, w)
    return list(seen.values())[:30]


def load_existing_coverage(forward_picks_path, theme_keyword):
    """读 forward_picks.csv,返回该主题已覆盖的 ticker set"""
    covered = set()
    if not os.path.exists(forward_picks_path):
        return covered
    with open(forward_picks_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3: continue
            if theme_keyword in (row[1] if len(row) > 1 else ""):
                tk = row[2].strip().split(".")[0]  # PANW.US → PANW
                covered.add(tk)
    return covered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--etfs", required=True, help="ETF 主题 ETF 清单(逗号分隔),例如 IGV,CIBR,WCLD,AIQ")
    parser.add_argument("--theme", required=True, help="主题名(用于匹配 forward_picks 行)")
    parser.add_argument("--forward-picks", default=os.path.join(HERE, "..", "tracking", "forward_picks.csv"))
    args = parser.parse_args()

    etfs = [e.strip().upper() for e in args.etfs.split(",")]
    print(f"=== theme_etf_coverage.py — {args.theme} ===")
    print(f"ETFs: {etfs}")
    print()

    # 1. 拉每个 ETF top 25
    all_holdings = {}  # ticker -> {etfs, max_weight}
    for etf in etfs:
        print(f"Fetching {etf} holdings...")
        holdings = fetch_etf_holdings(etf)
        print(f"  got {len(holdings)} holdings")
        for tk, name, wt in holdings:
            if tk not in all_holdings:
                all_holdings[tk] = {"etfs": [], "max_weight": 0}
            all_holdings[tk]["etfs"].append(f"{etf}:{wt:.2f}%")
            all_holdings[tk]["max_weight"] = max(all_holdings[tk]["max_weight"], wt)

    # 2. 读已覆盖
    covered = load_existing_coverage(args.forward_picks, args.theme)
    print(f"\nExisting coverage in forward_picks ({args.theme}): {len(covered)} tickers")
    print(f"  sample: {sorted(list(covered))[:15]}")

    # 3. diff
    new_tickers = sorted(
        [(tk, all_holdings[tk]) for tk in all_holdings if tk not in covered],
        key=lambda x: -x[1]["max_weight"]
    )

    print(f"\n=== gap: {len(new_tickers)} new tickers in ETF top holdings but not in forward_picks ===")
    print(f"{'TICKER':<8} {'MAX_WT':<8} ETFs")
    print("-" * 80)
    for tk, info in new_tickers:
        print(f"{tk:<8} {info['max_weight']:<7.2f}% {', '.join(info['etfs'])}")

    # 4. dump audit log
    log_path = os.path.join(HERE, "..", "tracking", f"_etf_audit_{args.theme.replace('/', '_')}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "theme": args.theme,
            "etfs_used": etfs,
            "etf_holdings": all_holdings,
            "already_covered": sorted(covered),
            "new_candidates": [tk for tk, _ in new_tickers],
        }, f, ensure_ascii=False, indent=2)
    print(f"\nAudit log: {log_path}")
    print(f"\n下一步:LLM 对每只 new candidate 人工判定产业链层 + Serenity 原型 + 是否纳入 forward_picks")


if __name__ == "__main__":
    main()
