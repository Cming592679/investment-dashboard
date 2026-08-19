"""卖出监控：把"何时该卖"的规则状态聚合为每只持仓的可读清单。

四轨逻辑（与 trading_rules / v1.1 规则书一致）：
- A 目标止盈：持有收益 vs 周期档位（early 25/40/60、mid 20/30/45 等），基准=单只基金累计成本；
- B 技术过热：RSI+KDJ 双热（来自 evaluate_daily_actions 的 sell_profit）；
- D 逻辑止损：领先指标 down / 瓶颈破坏（来自 sell_stop，不看成本）；
- 再平衡：实际仓位 vs 板块/主题/档位上限参考线。

纯函数：不访问网络/文件，输入 portfolio + action_result + exposure，便于单测。
"""

from datetime import datetime

from config import CYCLE_ASSESSMENTS, TRADING_CONFIG
from rules import load_rules


def _distances_to_tiers(return_pct, tiers):
    """从当前持有收益到各止盈档还需上涨的百分比（相对当前市值）。"""
    ratio = 1 + return_pct / 100
    if ratio <= 0:
        return [None] * len(tiers)
    return [round(((1 + t / 100) / ratio - 1) * 100, 1) for t in tiers]


def _hit_tier(return_pct, tiers):
    """命中的最高止盈档索引；未命中返回 -1。"""
    hit = -1
    for i, t in enumerate(tiers):
        if return_pct >= t:
            hit = i
    return hit


def _find_entry(entries, fund_id, prefix=None):
    for e in entries or []:
        if e.get("fund_id") != fund_id:
            continue
        track = str(e.get("track", ""))
        if prefix is None or track.startswith(prefix):
            return e
    return None


def build_sell_monitor(pf, action_result=None, exposure=None):
    """生成每只活跃持仓的卖出逻辑状态清单。返回 dict（可直接 JSON 序列化）。"""
    total = pf.get("total_assets", 0) or 0
    rules_tiers = load_rules().get("position_tiers", {})
    holdings_out = []

    for h in pf.get("holdings", []) or []:
        if h.get("status") in ("sold", "non_investment") or (h.get("amount") or 0) <= 0:
            continue

        fid = h.get("dashboard_id")
        ret = h.get("holding_return_pct")
        if ret is None:
            ret = 0.0
        amount = h.get("amount") or 0
        pct = round(amount / total * 100, 1) if total else 0.0
        stage = (CYCLE_ASSESSMENTS.get(fid) or {}).get("stage", "mid")
        tiers = TRADING_CONFIG["profit_tiers"].get(stage, [20, 30, 45])
        sell_pcts = TRADING_CONFIG["profit_sell_pct"]
        distances = _distances_to_tiers(ret, tiers)
        hit = _hit_tier(ret, tiers)

        # ── A 目标止盈 ──
        if hit >= 0:
            a_active = True
            a_status = f"已触发 A-止盈{'一二三'[hit]}档（卖 {sell_pcts[hit]:.0f}%）"
        else:
            a_active = False
            d0 = distances[0]
            a_status = (
                f"距一档(+{tiers[0]}%)还需 +{d0:.1f}%" if d0 is not None
                else "A轨不可达"
            )

        # ── B 技术过热 / D 逻辑止损（直接引用规则引擎输出，避免逻辑漂移） ──
        b_entry = _find_entry((action_result or {}).get("sell_profit", []), fid, "B-")
        d_entry = _find_entry((action_result or {}).get("sell_stop", []), fid, "D-")
        b_active = b_entry is not None
        d_active = d_entry is not None
        b_status = str(b_entry.get("track", "")) if b_entry else "未触发"
        d_status = f"{d_entry.get('track')}（{d_entry.get('reason', '')}）" if d_entry else "未触发"

        # ── 参考线：板块 / 主题 / 档位上限 ──
        over_lines = []
        sector = h.get("sector")
        for s in (exposure or {}).get("sectors", []):
            if s.get("name") == sector and s.get("pct", 0) > s.get("limit", 20):
                over_lines.append(f"板块 {s['name']} {s['pct']}% > 参考 {s['limit']}%")
        theme = h.get("theme")
        for t in (exposure or {}).get("themes", []):
            if theme and t.get("name") == theme and t.get("pct", 0) > t.get("limit", 30):
                over_lines.append(f"主题 {t['name']} {t['pct']}% > 参考 {t['limit']}%")
        cap = (rules_tiers.get(h.get("evidence_stage")) or 0) * 100
        if cap and pct > cap:
            over_lines.append(f"档位上限 {h.get('evidence_stage')}({cap:.0f}%) 实际 {pct:.1f}%")
        over_reference = bool(over_lines)

        # ── 退出路径 ──
        exit_paths = []
        if d_active:
            exit_paths.append("D-逻辑止损")
        if a_active:
            exit_paths.append("A-止盈")
        if b_active:
            exit_paths.append("B-技术过热")
        if over_reference:
            exit_paths.append("再平衡(超参考线)")
        if not exit_paths:
            exit_paths.append("未触发，继续持有")

        note = ""
        if d_active:
            note = "D 优先于 A/B 止盈"
        elif hit < 0 and ret < 0 and (distances[0] is None or distances[0] > 20):
            note = "A轨够不着 → 退出依赖 D-逻辑止损 / 再平衡"

        holdings_out.append({
            "fund_code": h.get("fund_code"),
            "fund_name": h.get("fund_name", ""),
            "sector": sector,
            "amount": amount,
            "pct": pct,
            "stage": stage,
            "tiers": tiers,
            "sell_pcts": sell_pcts,
            "holding_return_pct": round(ret, 2),
            "distances": distances,
            "tier_hit": hit,
            "a_active": a_active,
            "a_status": a_status,
            "b_active": b_active,
            "b_status": b_status,
            "d_active": d_active,
            "d_status": d_status,
            "over_reference": over_reference,
            "over_lines": over_lines,
            "exit_paths": exit_paths,
            "note": note,
        })

    summary = {
        "a_triggered": sum(1 for h in holdings_out if h["a_active"]),
        "b_triggered": sum(1 for h in holdings_out if h["b_active"]),
        "d_triggered": sum(1 for h in holdings_out if h["d_active"]),
        "over_reference": sum(1 for h in holdings_out if h["over_reference"]),
        "near_first_tier": sum(
            1 for h in holdings_out
            if not h["a_active"] and h["distances"][0] is not None and 0 < h["distances"][0] <= 15
        ),
        "unreachable_a": sum(1 for h in holdings_out if "A轨够不着" in h["note"]),
    }
    cluster_over = [
        c for c in (exposure or {}).get("clusters", [])
        if c.get("pct", 0) > c.get("limit", 30)
    ]
    return {
        "holdings": holdings_out,
        "summary": summary,
        "cluster_over": cluster_over,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
