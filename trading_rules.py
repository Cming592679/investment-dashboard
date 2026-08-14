"""叠层信号交易系统 — 规则引擎

Regime判定 → 叠层评分(L1-L4) → 止盈/止损触发 → 冲突消解 → 操作建议

架构:
  evaluate_daily_actions()              主入口
    ├─ _determine_regime()              板块级体制判定
    ├─ _calc_L1_technical()             激活的死信号层
    ├─ _calc_L2_bottleneck()            瓶颈加权层
    ├─ _calc_L3_cycle()                 周期层
    ├─ _calc_L4_event()                 事件层
    ├─ _check_buy_signals()             买入触发
    ├─ _check_sell_profit()             止盈 A/B/C 轨道
    ├─ _check_sell_stop()               止损 D 轨道
    ├─ _resolve_conflicts()             冲突消解
    └─ _apply_position_constraints()    硬约束
"""

from datetime import date, datetime, timedelta
from typing import Optional
from config import (
    FUNDS, LEADING_INDICATORS, CYCLE_ASSESSMENTS, KEY_DATES,
    BOTTLENECK_DISRUPTION, SHARED_INDICATORS, TRADING_CONFIG,
)


# ══════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════

def evaluate_daily_actions(portfolio: dict, dashboard_cache: dict) -> dict:
    """主入口：评估所有板块，返回今日操作建议。

    Args:
        portfolio: portfolio.json 数据
        dashboard_cache: {fund_id: {"data": {...}, "fetched_at": datetime}}

    Returns:
        {
            "date": "2026-08-03",
            "regimes": {fund_id: "Normal"|"Panic"|"Structural"|"Pre-Event", ...},
            "buy_signals": [...],
            "sell_profit": [...],       # 止盈轨道 A/B/C
            "sell_stop": [...],          # 止损轨道 D
            "conflicts_resolved": [...], # 被否决的信号
            "portfolio_health": {...},   # 仓位健康
            "no_action": bool,
        }
    """
    today = date.today()
    total_assets = portfolio.get("total_assets", 0)
    cash = portfolio.get("cash", 0)
    holdings = portfolio.get("holdings", [])
    cfg = TRADING_CONFIG

    result = {
        "date": today.strftime("%Y-%m-%d"),
        "regimes": {},
        "buy_signals": [],
        "sell_profit": [],
        "sell_stop": [],
        "conflicts_resolved": [],
        "portfolio_health": _check_portfolio_health(portfolio, cfg),
        "no_action": True,
    }

    # 对每个持仓板块评估
    # 按板块分组（多个持仓可能映射到同一板块 → 合并评估）
    sectors_seen = set()
    for h in holdings:
        fid = h.get("dashboard_id", "")
        if not fid or fid not in FUNDS:
            continue
        sector = h.get("sector", fid)
        if sector in sectors_seen:
            continue  # 同一板块只评估一次
        sectors_seen.add(sector)

        # 合并该板块所有持仓的金额
        sector_holdings = [hh for hh in holdings if hh.get("sector") == sector]
        sector_amount = sum(hh.get("amount", 0) for hh in sector_holdings)
        sector_return_pct = (
            sum(hh.get("holding_return", 0) for hh in sector_holdings)
            / sum(hh.get("cost_basis", hh.get("amount", 1) - hh.get("holding_return", 0))
                  for hh in sector_holdings) * 100
            if sector_amount > 0 else 0
        )
        # 构建合并后的持仓快照
        merged_holding = {
            "dashboard_id": fid,
            "sector": sector,
            "amount": sector_amount,
            "holding_return_pct": round(sector_return_pct, 2),
            "fund_name": sector,
            "fund_code": ", ".join(hh.get("fund_code", "") for hh in sector_holdings),
            "cost_basis": sum(hh.get("cost_basis", 0) for hh in sector_holdings),
            "holding_return": sum(hh.get("holding_return", 0) for hh in sector_holdings),
        }

        fund = FUNDS[fid]
        cache_entry = dashboard_cache.get(fid, {})
        dash_data = cache_entry.get("data", {}) if cache_entry else {}

        # 1. 体制判定
        regime = _determine_regime(fid, dash_data, today, cfg)
        result["regimes"][fid] = regime

        # 2. 叠层评分
        scores = _calc_all_layers(fid, dash_data, today, cfg)

        # 3. 检查买入信号
        buy = _check_buy_signals(fid, merged_holding, scores, regime, dash_data, total_assets, cash, cfg)
        if buy:
            if buy.get("_rejected"):
                result["conflicts_resolved"].append(buy)
            else:
                result["buy_signals"].append(buy)
                result["no_action"] = False

        # 4. 检查止盈 (轨道 A/B/C)
        profit_sells = _check_sell_profit(fid, merged_holding, scores, regime, dash_data, cfg)
        for ps in profit_sells:
            if ps.get("_rejected"):
                result["conflicts_resolved"].append(ps)
            else:
                result["sell_profit"].append(ps)
                result["no_action"] = False

        # 5. 检查止损 (轨道 D)
        stop_sells = _check_sell_stop(fid, merged_holding, scores, regime, dash_data, cfg)
        for ss in stop_sells:
            if ss.get("_rejected"):
                result["conflicts_resolved"].append(ss)
            else:
                result["sell_stop"].append(ss)
                result["no_action"] = False

    # 6. 冲突消解
    result = _resolve_conflicts(result)

    # 7. 应用硬约束
    result = _apply_position_constraints(result, total_assets, cash, cfg)

    # 重算 no_action
    result["no_action"] = (
        len(result["buy_signals"]) == 0
        and len(result["sell_profit"]) == 0
        and len(result["sell_stop"]) == 0
    )

    return result


# ══════════════════════════════════════════════════════════
# Regime 判定（板块级）
# ══════════════════════════════════════════════════════════

def _determine_regime(fid: str, dash_data: dict, today: date, cfg: dict) -> str:
    """判定板块当前体制。返回 Normal / Panic / Structural / Pre-Event"""

    # ── Structural: L2 瓶颈破坏 ──
    disruption_negative, _ = _check_disruption_for_fund(fid)
    if disruption_negative:
        return "Structural"

    # ── Pre-Event: 48h内有critical事件 ──
    key_dates = KEY_DATES.get(fid, [])
    for kd in key_dates:
        if kd.get("importance") != "critical":
            continue
        hours_left = (kd["date"] - today).total_seconds() / 3600
        if 0 < hours_left <= cfg["regime"]["pre_event_hours"]:
            return "Pre-Event"

    # ── Panic: 单日暴跌或大面积RSI超卖 ──
    stocks = dash_data.get("stocks", {})
    fund_return = dash_data.get("fund_return_pct")
    if fund_return is not None and fund_return <= cfg["regime"]["panic_daily_drop_pct"]:
        return "Panic"

    rsi_low_count = sum(
        1 for s in stocks.values()
        if s.get("rsi") is not None and s["rsi"] <= cfg["regime"]["panic_rsi_threshold"]
    )
    if rsi_low_count >= cfg["regime"]["panic_rsi_count"]:
        return "Panic"

    return "Normal"


# ══════════════════════════════════════════════════════════
# 叠层评分 L1-L4
# ══════════════════════════════════════════════════════════

def _calc_all_layers(fid: str, dash_data: dict, today: date, cfg: dict) -> dict:
    """计算 L1-L4 全部得分"""
    l1 = _calc_L1_technical(fid, dash_data, cfg)
    l2 = _calc_L2_bottleneck(fid, dash_data, cfg)
    l3 = _calc_L3_cycle(fid, cfg)
    l4 = _calc_L4_event(fid, today, cfg)

    w = cfg["signal_weights"]
    total_buy = (
        l1["buy_score"] * w["L1_technical"]
        + l2["buy_score"] * w["L2_bottleneck"]
        + l3["score"] * w["L3_cycle"]
        + l4["score"] * w["L4_event"]
    )
    total_sell = (
        l1["sell_score"] * w["L1_technical"]
        + l2["sell_score"] * w["L2_bottleneck"]
        + (-l3["score"]) * w["L3_cycle"]
        + (-l4["score"]) * w["L4_event"]
    )
    total_sell = min(total_sell, 0)  # 卖出得分 ≤0

    return {
        "L1": l1, "L2": l2, "L3": l3, "L4": l4,
        "buy_score": round(total_buy, 1),
        "sell_score": round(total_sell, 1),
        "weights": w,
    }


def _calc_L1_technical(fid: str, dash_data: dict, cfg: dict) -> dict:
    """L1 技术面：激活 MACD/Bollinger/KDJ/RSI/MA 体系"""
    pts = cfg["signal_points"]["L1"]
    buy = 0
    sell = 0
    details = []

    stocks = dash_data.get("stocks", {})
    indices = dash_data.get("indices", {})

    # 聚合所有成分股的技术指标
    all_assets = {**stocks, **indices}

    # RSI
    oversold_count = 0
    overbought_count = 0
    for tk, s in all_assets.items():
        rsi = s.get("rsi")
        if rsi is not None:
            if rsi <= 30:
                oversold_count += 1
            # 用板块的过热阈值
            cycle = CYCLE_ASSESSMENTS.get(fid, {})
            stage = cycle.get("stage", "mid")
            rsi_overbought = cfg["overheat"]["rsi"].get(stage, 75)
            if rsi >= rsi_overbought:
                overbought_count += 1

    total = len(all_assets)
    if total > 0 and oversold_count / total >= 0.4:
        buy += pts["rsi_oversold"]
        details.append(f"RSI超卖({oversold_count}/{total}只) → +{pts['rsi_oversold']}")
    if total > 0 and overbought_count / total >= 0.4:
        sell += pts["rsi_overbought"]
        details.append(f"RSI过热({overbought_count}/{total}只) → {pts['rsi_overbought']}")

    # MA50 修复/破位检测
    ma_ok = sum(1 for s in all_assets.values() if s.get("above_ma50"))
    ma_total = sum(1 for s in all_assets.values() if s.get("above_ma50") is not None)
    if ma_total > 0:
        ratio = ma_ok / ma_total
        if ratio < 0.3:
            sell += pts["ma50_break"]
            details.append(f"MA50大面积破位({ma_ok}/{ma_total}) → {pts['ma50_break']}")
        elif ratio >= 0.6:
            buy += pts["ma50_repair"]
            details.append(f"MA50修复(≥60%) → +{pts['ma50_repair']}")

    # MACD
    macd_signals = {"golden_cross": 0, "death_cross": 0}
    for tk, s in stocks.items():
        macd = s.get("indicators", {}).get("macd", {})
        sig = macd.get("signal")
        if sig == "golden_cross":
            macd_signals["golden_cross"] += 1
        elif sig == "death_cross":
            macd_signals["death_cross"] += 1
    if macd_signals["golden_cross"] >= 1:
        buy += pts["macd_golden"]
        details.append(f"MACD金叉({macd_signals['golden_cross']}只) → +{pts['macd_golden']}")
    if macd_signals["death_cross"] >= 1:
        sell += pts["macd_death"]
        details.append(f"MACD死叉({macd_signals['death_cross']}只) → {pts['macd_death']}")

    # KDJ
    kdj_overbought = 0
    kdj_oversold = 0
    for tk, s in stocks.items():
        kdj = s.get("indicators", {}).get("kdj", {})
        if kdj.get("status") == "oversold":
            kdj_oversold += 1
        elif kdj.get("status") == "overbought":
            kdj_overbought += 1
    if kdj_oversold >= 2:
        buy += pts["kdj_oversold"]
        details.append(f"KDJ超卖({kdj_oversold}只) → +{pts['kdj_oversold']}")
    if kdj_overbought >= 2:
        sell += pts["kdj_overbought"]
        details.append(f"KDJ过热({kdj_overbought}只) → {pts['kdj_overbought']}")

    # Bollinger
    boll_lower = 0
    boll_upper = 0
    for tk, s in stocks.items():
        boll = s.get("indicators", {}).get("bollinger", {})
        pos = boll.get("position", "")
        if pos == "below_lower":
            boll_lower += 1
        elif pos == "above_upper":
            boll_upper += 1
    if boll_lower >= 2:
        buy += pts["bollinger_lower"]
        details.append(f"Bollinger下轨({boll_lower}只) → +{pts['bollinger_lower']}")
    if boll_upper >= 2:
        sell += pts["bollinger_upper"]
        details.append(f"Bollinger上轨({boll_upper}只) → {pts['bollinger_upper']}")

    # ── 量价关系 ──
    vol_buy, vol_sell, vol_details = _calc_volume_signals(stocks, pts)
    buy += vol_buy
    sell += vol_sell
    details.extend(vol_details)

    return {"buy_score": buy, "sell_score": sell, "details": details,
            "rsi_oversold": oversold_count, "rsi_overbought": overbought_count,
            "volume_buy": vol_buy, "volume_sell": vol_sell}


def _calc_volume_signals(stocks: dict, pts: dict) -> tuple:
    """量价关系评分。返回 (buy_score, sell_score, details)。

    经典量价理论：
    - 上涨+放量(>1.5x) = 真突破，强势 → +2
    - 上涨+缩量(<0.6x) = 无量反弹，死猫跳 → -1
    - 下跌+放量(>1.5x) = 恐慌抛售，接近底部 → +1
    - 下跌+缩量(<0.6x) = 阴跌无人接盘 → -2
    - 暴跌后放量反弹+MACD金叉 = 反转概率升高 → +2
    """
    buy = 0
    sell = 0
    details = []

    vol_up_heavy = 0    # 放量上涨
    vol_up_light = 0    # 缩量上涨
    vol_down_heavy = 0  # 放量下跌
    vol_down_light = 0  # 缩量下跌

    for tk, s in stocks.items():
        vi = s.get("volume_info", {})
        vol_ratio = vi.get("volume_ratio")
        chg_pct = s.get("day_change_pct", 0)
        if vol_ratio is None or chg_pct is None:
            continue

        if chg_pct > 0:
            if vol_ratio >= 1.5:
                vol_up_heavy += 1
            elif vol_ratio <= 0.6:
                vol_up_light += 1
        elif chg_pct < 0:
            if vol_ratio >= 1.5:
                vol_down_heavy += 1
            elif vol_ratio <= 0.6:
                vol_down_light += 1

    total = len([s for s in stocks.values() if s.get("volume_info", {}).get("volume_ratio") is not None])
    if total == 0:
        return 0, 0, []

    # 放量上涨 → 强势
    if vol_up_heavy >= 2:
        buy += pts["volume_up_heavy"]
        details.append(f"放量上涨({vol_up_heavy}/{total}只 vol>1.5x) → +{pts['volume_up_heavy']}")

    # 缩量上涨 → 反弹无力
    if vol_up_light >= 2:
        sell += pts["volume_up_light"]
        details.append(f"缩量上涨({vol_up_light}/{total}只 vol<0.6x) → {pts['volume_up_light']}")

    # 放量下跌 → 恐慌出清（偏多）
    if vol_down_heavy >= 2:
        buy += pts["volume_down_heavy"]
        details.append(f"放量下跌({vol_down_heavy}/{total}只 vol>1.5x) → +{pts['volume_down_heavy']} (恐慌出清)")

    # 缩量下跌 → 阴跌
    if vol_down_light >= 2:
        sell += pts["volume_down_light"]
        details.append(f"缩量下跌({vol_down_light}/{total}只 vol<0.6x) → {pts['volume_down_light']}")

    return buy, sell, details


def _calc_L2_bottleneck(fid: str, dash_data: dict, cfg: dict) -> dict:
    """L2 瓶颈面：领先指标加权 + 破坏条件 + 联动"""
    pts = cfg["signal_points"]["L2"]
    buy = 0
    sell = 0
    details = []

    # 领先指标加权趋势
    indicators = LEADING_INDICATORS.get(fid, {})
    up_weighted = 0
    down_weighted = 0
    flat_count = 0
    for name, info in indicators.items():
        trend = info.get("trend", "flat")
        # 关键瓶颈 (标有【②】【①】等的) 权重更高
        weight = 2 if any(f"【{i}】" in name for i in ["①","②","③","⑥"]) else 1
        if trend == "up":
            up_weighted += weight
        elif trend == "down":
            down_weighted += weight
        else:
            flat_count += 1

    if up_weighted >= 4:
        buy += pts["leading_up"]
        details.append(f"领先指标加权偏多({up_weighted}w↑) → +{pts['leading_up']}")
    if down_weighted >= 2:
        sell += pts["leading_down"]
        details.append(f"领先指标加权偏空({down_weighted}w↓) → {pts['leading_down']}")

    # 瓶颈破坏条件
    disruption_negative, disruption_positive = _check_disruption_for_fund(fid)
    if disruption_negative:
        sell += pts["breakthrough_negative"]
        for d in disruption_negative:
            details.append(f"瓶颈破坏 ⚠ {d['bottleneck']}: {d['condition']} → {pts['breakthrough_negative']}")
    if disruption_positive:
        buy += pts["breakthrough_positive"]
        for d in disruption_positive:
            details.append(f"瓶颈突破 🟢 {d['bottleneck']}: {d['condition']} → +{pts['breakthrough_positive']}")

    # 联动降级/升级
    cascade = _check_cascade(fid)
    if cascade["downgrade"]:
        sell += pts["cascade_downgrade"]
        details.append(f"联动降级({cascade['downgrade_count']}项) → {pts['cascade_downgrade']}")
    if cascade["upgrade"]:
        buy += pts["cascade_upgrade"]
        details.append(f"联动升级({cascade['upgrade_count']}项) → +{pts['cascade_upgrade']}")

    return {"buy_score": buy, "sell_score": sell, "details": details,
            "up_weighted": up_weighted, "down_weighted": down_weighted, "flat": flat_count}


def _calc_L3_cycle(fid: str, cfg: dict) -> dict:
    """L3 周期面"""
    pts = cfg["signal_points"]["L3"]
    cycle = CYCLE_ASSESSMENTS.get(fid, {})
    stage = cycle.get("stage", "mid")
    risk = cycle.get("risk", "green")

    score = pts.get(stage, 1)
    # 红色风险 → 额外 -1
    if risk == "red":
        score -= 1

    return {"score": score, "stage": stage, "risk": risk,
            "label": cycle.get("label", stage),
            "note": cycle.get("note", "")}


def _calc_L4_event(fid: str, today: date, cfg: dict) -> dict:
    """L4 事件面：最近14天内已过期事件的结果。得分上限 ±4。"""
    pts = cfg["signal_points"]["L4"]
    key_dates = KEY_DATES.get(fid, [])
    score = 0
    details = []

    for kd in key_dates:
        days_ago = (today - kd["date"]).days
        if 0 <= days_ago <= 14:
            result = kd.get("result", "")
            if not result:
                continue
            result_lower = result.lower()
            has_positive = any(kw in result_lower for kw in
                ["超预期", "创新高", "加速", "上调", "beat", "record", "raise", "surge", "soar"])
            has_negative = any(kw in result_lower for kw in
                ["不及预期", "低于", "下调", "miss", "下滑", "骤降", "转负", "cut"])

            if has_positive and not has_negative:
                score += pts["beat"]
                details.append(f"{kd['event']}: 利好 → +{pts['beat']}")
            elif has_negative and not has_positive:
                score += pts["miss"]
                details.append(f"{kd['event']}: 利空 → {pts['miss']}")

    # Cap at ±4
    score = max(-4, min(4, score))
    return {"score": score, "details": details}


# ══════════════════════════════════════════════════════════
# 买入信号
# ══════════════════════════════════════════════════════════

def _check_buy_signals(fid: str, holding: dict, scores: dict, regime: str,
                       dash_data: dict, total_assets: float, cash: float, cfg: dict) -> Optional[dict]:
    """检查买入触发条件"""
    buy_threshold = cfg["buy"]["signal_threshold"]
    l2_min = cfg["buy"]["L2_minimum"]
    total_buy = scores["buy_score"]
    l2_buy = scores["L2"]["buy_score"]
    l2_sell = scores["L2"]["sell_score"]

    # 硬条件检查
    if regime == "Structural":
        return _rejected(fid, "买入", "Structural体制 → 禁止买入", scores)
    if regime == "Pre-Event":
        return _rejected(fid, "买入", "Pre-Event体制 → 冻结交易", scores)

    # 趋势过滤器
    if not _trend_filter_pass(dash_data):
        return _rejected(fid, "买入", "MA20<MA60 → 趋势向下，禁止买入", scores)

    # 核心条件：叠层得分 ≥ 阈值 且 L2瓶颈面非负
    if total_buy < buy_threshold:
        return None  # 未触发，不记录（不是被否决）
    if l2_sell < 0:
        return _rejected(fid, "买入", "L2瓶颈面恶化 → 买入信号作废", scores)

    # 计算买入金额
    rsi_coef = _get_rsi_tier_coefficient(dash_data, cfg)
    size_pct = cfg["position"]["standard_size_pct"]
    base_amount = total_assets * (size_pct / 100)

    # 叠层信心系数
    if total_buy >= 8:
        confidence_coef = 1.5
    elif total_buy >= 6:
        confidence_coef = 1.0
    else:
        confidence_coef = 0.5

    buy_coef = min(rsi_coef, confidence_coef)  # 保守取小
    buy_amount = base_amount * buy_coef

    # Panic 体制 → 买入减半
    if regime == "Panic":
        buy_amount *= 0.5

    # 仓位约束
    sector_pct = _get_sector_pct(holding, total_assets)
    max_sector = cfg["position"]["max_sector_pct"]
    if sector_pct + (buy_amount / total_assets * 100) > max_sector:
        buy_amount = max(0, (max_sector / 100 * total_assets) - (sector_pct / 100 * total_assets))

    # 现金约束
    if buy_amount > cash - (total_assets * cfg["position"]["min_cash_pct"] / 100):
        buy_amount = max(0, cash - total_assets * cfg["position"]["min_cash_pct"] / 100)

    if buy_amount < 100:  # 最少¥100
        return _rejected(fid, "买入", f"计算金额 ¥{buy_amount:.0f} < ¥100 最低门槛", scores)

    return {
        "fund_id": fid,
        "fund_name": holding.get("fund_name", ""),
        "fund_code": holding.get("fund_code", ""),
        "sector": holding.get("sector", ""),
        "action": "buy",
        "amount": round(buy_amount, 2),
        "regime": regime,
        "scores": scores,
        "rsi_coefficient": rsi_coef,
        "confidence_coefficient": confidence_coef,
        "reason": f"叠层得分 {total_buy}≥{buy_threshold}，RSI分级{rsi_coef}，信心{confidence_coef}",
    }


def _trend_filter_pass(dash_data: dict) -> bool:
    """MA20 > MA60 趋势过滤器"""
    stocks = dash_data.get("stocks", {})
    if not stocks:
        return True  # 无数据默认通过

    above_count = 0
    total_count = 0
    for tk, s in stocks.items():
        ma20 = s.get("ma20")
        ma60 = s.get("ma60")
        if ma20 is not None and ma60 is not None:
            total_count += 1
            if ma20 > ma60:
                above_count += 1

    if total_count == 0:
        return True
    # ≥50%的成分股 MA20 > MA60 才通过
    return above_count / total_count >= 0.5


def _get_rsi_tier_coefficient(dash_data: dict, cfg: dict) -> float:
    """计算 RSI 分级加仓系数"""
    stocks = dash_data.get("stocks", {})
    if not stocks:
        return 0.5  # 默认中性

    avg_rsi = sum(s.get("rsi", 50) or 50 for s in stocks.values()) / len(stocks)

    for tier in cfg["rsi_tiers"]:
        if tier["rsi_min"] <= avg_rsi < tier["rsi_max"]:
            return tier["coefficient"]

    return 0.5  # RSI >45 时默认半仓


# ══════════════════════════════════════════════════════════
# 止盈卖出 (轨道 A/B/C)
# ══════════════════════════════════════════════════════════

def _check_sell_profit(fid: str, holding: dict, scores: dict, regime: str,
                       dash_data: dict, cfg: dict) -> list:
    """检查止盈触发：轨道A(目标止盈) + 轨道B(技术过热) + 轨道C(时间)"""
    results = []
    return_pct = holding.get("holding_return_pct", 0)
    amount = holding.get("amount", 0)
    cost_basis = holding.get("cost_basis", 0)

    if regime == "Pre-Event":
        return []

    # ── 轨道 A: 目标止盈 ──
    cycle = CYCLE_ASSESSMENTS.get(fid, {})
    stage = cycle.get("stage", "mid")
    tiers = cfg["profit_tiers"].get(stage, [20, 30, 45])
    sell_pcts = cfg["profit_sell_pct"]

    for i, (threshold, sell_pct) in enumerate(zip(tiers, sell_pcts)):
        if return_pct >= threshold:
            # 基本面很强 → 止盈减半
            l2_buy = scores["L2"]["buy_score"]
            effective_sell_pct = sell_pct
            if l2_buy >= 4:  # L2 strongly positive
                effective_sell_pct = sell_pct / 2
            elif scores["L3"]["score"] <= 0:  # cycle late → 止盈加倍
                effective_sell_pct = min(sell_pct * 1.5, 100)

            sell_amount = amount * (effective_sell_pct / 100)
            tier_label = ["一档", "二档", "三档"][i]

            results.append({
                "fund_id": fid,
                "fund_name": holding.get("fund_name", ""),
                "fund_code": holding.get("fund_code", ""),
                "sector": holding.get("sector", ""),
                "action": "sell",
                "amount": round(sell_amount, 2),
                "sell_pct": effective_sell_pct,
                "track": f"A-止盈({tier_label})",
                "regime": regime,
                "scores": scores,
                "reason": f"盈利 {return_pct:+.1f}% ≥ {threshold}% ({stage}周期{tier_label})，卖出{effective_sell_pct:.0f}%",
            })
            break  # 只触发最高档

    # ── 轨道 B: 技术过热 ──
    l1 = scores["L1"]
    cycle = CYCLE_ASSESSMENTS.get(fid, {})
    stage = cycle.get("stage", "mid")
    rsi_threshold = cfg["overheat"]["rsi"].get(stage, 75)

    stocks = dash_data.get("stocks", {})
    rsi_overbought_count = sum(
        1 for s in stocks.values()
        if s.get("rsi") is not None and s["rsi"] >= rsi_threshold
    )
    kdj_overbought_count = sum(
        1 for s in stocks.values()
        if s.get("indicators", {}).get("kdj", {}).get("status") == "overbought"
    )

    # RSI+KDJ 双过热
    if rsi_overbought_count >= 3 and kdj_overbought_count >= 2:
        sell_pct = cfg["overheat"]["sell_pct_rsi_kdj"]
        results.append({
            "fund_id": fid,
            "fund_name": holding.get("fund_name", ""),
            "fund_code": holding.get("fund_code", ""),
            "sector": holding.get("sector", ""),
            "action": "sell",
            "amount": round(amount * sell_pct / 100, 2),
            "sell_pct": sell_pct,
            "track": "B-技术过热(RSI+KDJ)",
            "regime": regime,
            "scores": scores,
            "reason": f"RSI≥{rsi_threshold}({rsi_overbought_count}只) + KDJ超买({kdj_overbought_count}只) → 短期过热",
        })

    # Bollinger上轨 + MACD死叉
    boll_upper = sum(
        1 for s in stocks.values()
        if s.get("indicators", {}).get("bollinger", {}).get("position") == "above_upper"
    )
    macd_death = sum(
        1 for s in stocks.values()
        if s.get("indicators", {}).get("macd", {}).get("signal") == "death_cross"
    )
    if boll_upper >= 2 and macd_death >= 1:
        sell_pct = cfg["overheat"]["sell_pct_bollinger_macd"]
        results.append({
            "fund_id": fid,
            "fund_name": holding.get("fund_name", ""),
            "fund_code": holding.get("fund_code", ""),
            "sector": holding.get("sector", ""),
            "action": "sell",
            "amount": round(amount * sell_pct / 100, 2),
            "sell_pct": sell_pct,
            "track": "B-技术过热(Boll+MACD)",
            "regime": regime,
            "scores": scores,
            "reason": f"Bollinger上轨({boll_upper}只) + MACD死叉({macd_death}只) → 短期见顶",
        })

    # ── 轨道 C: 时间止盈/止损 ──
    # Note: 需要持仓起始日期，暂用 action_log 中的首次记录。如无 → 跳过
    tc = cfg["time_based"]
    # 用 portfolio action_log 中最近的买入记录估算持有时间
    # 简化：用 holding_return 反推（不完美但可用）
    if abs(return_pct) <= tc["idle_return_range"]:
        # 标记无效仓位 — 这在UI层显示，不在此处生成卖出建议
        pass

    return results


# ══════════════════════════════════════════════════════════
# 止损卖出 (轨道 D)
# ══════════════════════════════════════════════════════════

def _check_sell_stop(fid: str, holding: dict, scores: dict, regime: str,
                     dash_data: dict, cfg: dict) -> list:
    """检查基本面止损触发（轨道 D）"""
    results = []
    l2_sell = scores["L2"]["sell_score"]
    amount = holding.get("amount", 0)

    if regime == "Pre-Event":
        return []
    if l2_sell >= 0:
        return []  # 无基本面恶化

    ss = cfg["structural_stop"]
    l2_details = scores["L2"]["details"]

    # 判断恶化程度
    has_breakthrough = any("瓶颈破坏" in d for d in l2_details)
    down_indicator_count = scores["L2"]["down_weighted"]
    # 简化：每个down指标大约贡献2权重
    down_count_est = max(1, down_indicator_count // 2)

    if has_breakthrough and down_count_est >= 2:
        sell_pct = ss["full_liquidation"]
        track = "D-清仓"
        reason = f"≥2个领先指标转down + 瓶颈破坏 → 清仓"
    elif has_breakthrough:
        sell_pct = ss["breakthrough_negative"]
        track = "D-瓶颈破坏"
        reason = f"瓶颈破坏突破(negative) → 减{sell_pct*100:.0f}%"
    elif down_count_est >= 2:
        sell_pct = ss["indicators_down_1_2"]
        track = "D-领先指标恶化"
        reason = f"≥2个领先指标转down → 减{sell_pct*100:.0f}%"
    else:
        return []  # 恶化程度不够

    # Structural 体制 → 卖出加倍
    if regime == "Structural":
        sell_pct = min(sell_pct * 1.5, 1.0)

    sell_amount = amount * sell_pct

    results.append({
        "fund_id": fid,
        "fund_name": holding.get("fund_name", ""),
        "fund_code": holding.get("fund_code", ""),
        "sector": holding.get("sector", ""),
        "action": "sell",
        "amount": round(sell_amount, 2),
        "sell_pct": sell_pct * 100,
        "track": track,
        "regime": regime,
        "scores": scores,
        "reason": reason,
    })

    return results


# ══════════════════════════════════════════════════════════
# 冲突消解
# ══════════════════════════════════════════════════════════

def _resolve_conflicts(result: dict) -> dict:
    """消解买卖冲突。规则：
    1. 卖出优先于买入（同板块）
    2. 结构性卖出优先于止盈卖出
    3. 同向取最大值（不叠加）
    4. Panic 体制压制卖出
    """
    # 收集所有涉及的板块
    all_fids = set()
    for sig in result["buy_signals"] + result["sell_profit"] + result["sell_stop"]:
        all_fids.add(sig["fund_id"])

    for fid in all_fids:
        regime = result["regimes"].get(fid, "Normal")
        buys = [s for s in result["buy_signals"] if s["fund_id"] == fid]
        profit_sells = [s for s in result["sell_profit"] if s["fund_id"] == fid]
        stop_sells = [s for s in result["sell_stop"] if s["fund_id"] == fid]

        # ── Panic 体制：压制所有卖出 ──
        if regime == "Panic" and (profit_sells or stop_sells):
            for s in profit_sells + stop_sells:
                s["_rejected"] = True
                s["_reject_reason"] = "Panic体制 → 卖出记录但不执行"
                result["conflicts_resolved"].append(s)
            result["sell_profit"] = [s for s in result["sell_profit"] if s["fund_id"] != fid]
            result["sell_stop"] = [s for s in result["sell_stop"] if s["fund_id"] != fid]

        # ── 有止损卖出 → 止盈全部作废 ──
        if stop_sells and profit_sells:
            for s in profit_sells:
                s["_rejected"] = True
                s["_reject_reason"] = "基本面止损优先，止盈信号忽略"
                result["conflicts_resolved"].append(s)
            result["sell_profit"] = [s for s in result["sell_profit"] if s["fund_id"] != fid]

        # ── 有卖出 → 买入全部作废 ──
        has_sells = bool(stop_sells or profit_sells)
        if has_sells and buys:
            for s in buys:
                s["_rejected"] = True
                s["_reject_reason"] = "卖出优先于买入（同板块）"
                result["conflicts_resolved"].append(s)
            result["buy_signals"] = [s for s in result["buy_signals"] if s["fund_id"] != fid]

    return result


def _apply_position_constraints(result: dict, total_assets: float, cash: float, cfg: dict) -> dict:
    """应用仓位硬约束"""
    min_cash = total_assets * cfg["position"]["min_cash_pct"] / 100

    # 买入总额不能超过可用现金-最低现金
    total_buy = sum(s["amount"] for s in result["buy_signals"])
    available = max(0, cash - min_cash)

    if total_buy > available and result["buy_signals"]:
        # 按得分从高到低分配资金
        result["buy_signals"].sort(key=lambda s: s["scores"]["buy_score"], reverse=True)
        remaining = available
        for s in result["buy_signals"]:
            if remaining <= 0:
                s["_rejected"] = True
                s["_reject_reason"] = "现金不足（已达最低现金线）"
                result["conflicts_resolved"].append(s)
            elif s["amount"] > remaining:
                s["amount"] = round(remaining, 2)
                remaining = 0
            else:
                remaining -= s["amount"]
        result["buy_signals"] = [s for s in result["buy_signals"] if not s.get("_rejected")]

    return result


# ══════════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════════

def _check_disruption_for_fund(fid: str) -> tuple:
    """检查瓶颈破坏条件。返回 (negative_triggers, positive_triggers)"""
    negative = []
    positive = []
    for tag, info in BOTTLENECK_DISRUPTION.items():
        if fid not in info["affected_funds"]:
            continue
        for cond in info["conditions"]:
            if cond["status"] == "breakthrough":
                entry = {
                    "bottleneck": info["label"],
                    "condition": cond["desc"],
                    "note": cond.get("note", ""),
                }
                if fid in cond.get("positive_for", []):
                    positive.append(entry)
                else:
                    negative.append(entry)
    return negative, positive


def _check_cascade(fid: str) -> dict:
    """检查联动降级/升级"""
    downgrade = []
    upgrade = []
    for indicator_key, config in SHARED_INDICATORS.items():
        if fid not in config["funds"]:
            continue
        for other_fid in config["funds"]:
            if other_fid == fid:
                continue
            other_leading = LEADING_INDICATORS.get(other_fid, {})
            for name, v in other_leading.items():
                if indicator_key in name and v.get("value") != "--":
                    if v.get("trend") in ("flat", "down"):
                        downgrade.append({"indicator": indicator_key, "from": other_fid})
                        break
                    elif v.get("trend") == "up":
                        upgrade.append({"indicator": indicator_key, "from": other_fid})
                        break
    return {
        "downgrade": bool(downgrade),
        "downgrade_count": len(downgrade),
        "upgrade": bool(upgrade),
        "upgrade_count": len(upgrade),
    }


def _get_sector_pct(holding: dict, total_assets: float) -> float:
    """计算板块占比"""
    if total_assets <= 0:
        return 0
    return holding.get("amount", 0) / total_assets * 100


def _rejected(fid: str, action: str, reason: str, scores: dict) -> dict:
    """生成被否决的信号记录"""
    return {
        "fund_id": fid, "action": action, "reason": reason, "scores": scores,
        "sector": "", "fund_name": "", "fund_code": "", "regime": "",
        "amount": 0, "sell_pct": 0, "track": "",
        "_rejected": True, "_reject_reason": reason,
    }


def _check_portfolio_health(portfolio: dict, cfg: dict) -> dict:
    """检查仓位健康状态"""
    warnings = []
    holdings = portfolio.get("holdings", [])
    total = portfolio.get("total_assets", 0)
    if total <= 0:
        return {"warnings": [], "score": 0}

    # 持仓数量
    n = len(holdings)
    max_funds = cfg["position"]["max_position_funds"]
    min_funds = cfg["position"]["min_position_funds"]
    if n > max_funds:
        warnings.append(f"持仓 {n} 只 > {max_funds} 上限，建议合并")
    if n < min_funds:
        warnings.append(f"持仓 {n} 只 < {min_funds} 下限，过于集中")

    # 现金比例
    cash = portfolio.get("cash", 0)
    cash_pct = cash / total * 100
    min_cash = cfg["position"]["min_cash_pct"]
    if cash_pct < min_cash:
        warnings.append(f"现金 {cash_pct:.1f}% < {min_cash}% 下限")

    # 板块超限
    max_sector = cfg["position"]["max_sector_pct"]
    sectors = portfolio.get("sector_allocation", {})
    for name, info in sectors.items():
        if info.get("pct", 0) > max_sector:
            warnings.append(f"{name} 占比 {info['pct']}% > {max_sector}% 上限")

    # 微量仓位
    tiny = [h for h in holdings if h.get("amount", 0) < 2000]
    if tiny:
        warnings.append(f"{len(tiny)} 只 < ¥2,000 微量仓位")

    return {"warnings": warnings, "score": max(0, 100 - len(warnings) * 15)}
