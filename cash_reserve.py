"""分层现金储备：层级判定 + 归还规则（v1.2，2026-09-14 用户决策 D1）。

把"现金下限"从单向门（只能被动增加、永不可动用）改为可动用的战略储备：

    L0 常规 10%  →  L1 应急 7%  →  L2 深度 4%  →  L3 极深 0%
        —          ≥4板块RSI≤20    ≥4板块RSI≤30      ≥4板块偏离MA50
                                  +大盘20日≤-8%        ≤-20%
    （年均约 0 次）   （2.99 次/年）    （1.04 次/年）     （0.45 次/年）

阈值由 2020-01-02~2026-09-14（6.7 年）历史回测的"独立机会次数"反推，对齐用户要求：
一年 2-3 次的机会 → 允许把现金降到 10% 以下；一年 ≤1 次的机会 → 允许归零。

归还机制：退出触发区间即归还，**不看盈亏**；20 个交易日未退出 → 强制归还 + 止损提醒。

本模块为纯函数（不访问网络/文件），便于单元测试；数据获取由调用方负责。
输入口径：
    sector_rsi      {板块名: 14日RSI}         实盘用板块级加权 RSI
    sector_dev_ma50 {板块名: 相对MA50偏离%}    负值表示低于均线
    index_drop_20d  沪深300 近 20 个交易日涨跌幅 %
"""

from datetime import date, timedelta

try:
    from config import CASH_RESERVE
except ImportError:  # 允许无 config 环境下测试
    CASH_RESERVE = None

# 从松到严的顺序（用于计算"下一档"）
TIER_ORDER = ["L0", "L1", "L2", "L3"]


def _cfg(config=None):
    cfg = config or CASH_RESERVE
    if not cfg:
        # 无配置时的安全回退：只允许常规下限
        return {
            "enabled": False,
            "base_floor_pct": 10.0,
            "tiers": [],
            "return": {"deadline_trading_days": 20},
        }
    return cfg


def _tier_by_id(tier_id, config=None):
    for t in _cfg(config).get("tiers", []):
        if t.get("id") == tier_id:
            return t
    return None


def _eval_condition(cond, sector_rsi, sector_dev_ma50, index_drop_20d):
    """判定单个条件是否满足。返回 (是否满足, 描述, 指标可用)。

    数据缺失时视为"未满足"（保守：不利动用储备），并标记 data_ok=False。
    """
    ctype = cond.get("type")
    thr = cond.get("threshold")

    if ctype == "sector_rsi_count":
        if not sector_rsi:
            return False, f"板块RSI数据缺失（需 ≥{cond['min_count']} 个板块 ≤{thr:g}）", False
        hit = [k for k, v in sector_rsi.items() if v is not None and v <= thr]
        need = cond.get("min_count", 1)
        desc = f"{len(hit)}/{need} 个板块 RSI≤{thr:g}"
        return len(hit) >= need, desc, True

    if ctype == "sector_dev_ma50_count":
        if not sector_dev_ma50:
            return False, f"板块均线偏离数据缺失（需 ≥{cond['min_count']} 个板块 ≤{thr:g}%）", False
        hit = [k for k, v in sector_dev_ma50.items() if v is not None and v <= thr]
        need = cond.get("min_count", 1)
        desc = f"{len(hit)}/{need} 个板块 偏离MA50≤{thr:g}%"
        return len(hit) >= need, desc, True

    if ctype == "index_drop_20d":
        if index_drop_20d is None:
            return False, f"大盘20日跌幅数据缺失（需 ≤{thr:g}%）", False
        desc = f"大盘20日 {index_drop_20d:+.2f}%（需 ≤{thr:g}%）"
        return index_drop_20d <= thr, desc, True

    return False, f"未知条件类型 {ctype}", True


def evaluate_tier(sector_rsi=None, sector_dev_ma50=None, index_drop_20d=None,
                  config=None):
    """判定当前可动用的现金下限层级。

    返回 dict：
        tier        命中的层级 id（未命中任何档 → "L0"）
        floor_pct   该层对应的现金下限（占总资产 %）
        label       人类可读标签
        matched     命中的条件描述列表
        checks      所有档位的判定明细（调试/展示用）
        data_ok     参与判定的数据是否齐全
        deployment_allowed  是否允许动用储备（即 tier != L0）
    """
    cfg = _cfg(config)
    checks = []
    data_ok_all = True

    if not cfg.get("enabled"):
        return {
            "tier": "L0",
            "floor_pct": cfg.get("base_floor_pct", 10.0),
            "label": "分层储备未启用（固定下限）",
            "matched": [],
            "checks": [],
            "data_ok": True,
            "deployment_allowed": False,
        }

    for tier in cfg.get("tiers", []):
        cond_results = []
        all_met = True
        for cond in tier.get("conditions", []):
            met, desc, data_ok = _eval_condition(
                cond, sector_rsi, sector_dev_ma50, index_drop_20d
            )
            cond_results.append({"met": met, "desc": desc, "data_ok": data_ok})
            if not data_ok:
                data_ok_all = False
            if not met:
                all_met = False
        checks.append({
            "tier": tier.get("id"),
            "floor_pct": tier.get("floor_pct"),
            "freq_per_year": tier.get("freq_per_year"),
            "label": tier.get("label"),
            "met": all_met,
            "conditions": cond_results,
        })
        if all_met:
            return {
                "tier": tier.get("id"),
                "floor_pct": tier.get("floor_pct"),
                "label": tier.get("label"),
                "matched": [c["desc"] for c in cond_results],
                "checks": checks,
                "data_ok": True,
                "deployment_allowed": True,
            }

    return {
        "tier": "L0",
        "floor_pct": cfg.get("base_floor_pct", 10.0),
        "label": "常规层：未触发任何储备动用条件",
        "matched": [],
        "checks": checks,
        "data_ok": data_ok_all,
        "deployment_allowed": False,
    }


def next_tier_hint(result, sector_rsi=None, sector_dev_ma50=None,
                   index_drop_20d=None, config=None):
    """生成"距下一档还差什么"的提示文本（用于待办/首页展示）。

    下一档 = 比当前命中档更严的一档；已在最高档则返回 None。
    """
    cfg = _cfg(config)
    current = result.get("tier", "L0")
    if current not in TIER_ORDER:
        return None
    idx = TIER_ORDER.index(current)
    if idx >= len(TIER_ORDER) - 1:
        return None  # 已是 L3

    next_id = TIER_ORDER[idx + 1]
    tier = _tier_by_id(next_id, cfg)
    if not tier:
        return None

    parts = []
    for cond in tier.get("conditions", []):
        ctype = cond.get("type")
        thr = cond.get("threshold")
        if ctype == "sector_rsi_count":
            vals = [v for v in (sector_rsi or {}).values() if v is not None]
            hit = sum(1 for v in vals if v <= thr)
            need = cond.get("min_count", 1)
            parts.append(f"板块RSI≤{thr:g} 需 {need} 个（现 {hit} 个）")
        elif ctype == "sector_dev_ma50_count":
            vals = [v for v in (sector_dev_ma50 or {}).values() if v is not None]
            hit = sum(1 for v in vals if v <= thr)
            need = cond.get("min_count", 1)
            parts.append(f"板块偏离MA50≤{thr:g}% 需 {need} 个（现 {hit} 个）")
        elif ctype == "index_drop_20d":
            cur = index_drop_20d
            cur_s = f"{cur:+.2f}%" if cur is not None else "数据缺失"
            parts.append(f"大盘20日≤{thr:g}%（现 {cur_s}）")

    return f"距 {next_id}（现金下限 {tier.get('floor_pct')}%）还差：" + "；".join(parts)


def resolve_floor_pct(sector_rsi=None, sector_dev_ma50=None, index_drop_20d=None,
                      config=None):
    """便捷函数：直接返回当前允许的现金下限（占总资产 %）。"""
    return evaluate_tier(
        sector_rsi=sector_rsi,
        sector_dev_ma50=sector_dev_ma50,
        index_drop_20d=index_drop_20d,
        config=config,
    )["floor_pct"]


# ══════════════════════════════════════════════════════════
# 归还机制
# ══════════════════════════════════════════════════════════

def start_deployment(tier_id, deployed_amount, today=None, config=None):
    """登记一次储备动用，返回储备状态 dict（写入 portfolio["cash_reserve"]）。"""
    cfg = _cfg(config)
    tier = _tier_by_id(tier_id, cfg)
    if not tier:
        raise ValueError(f"未知层级: {tier_id}")
    d = today or date.today()
    deadline = (d + timedelta(days=int(cfg.get("return", {}).get("deadline_trading_days", 20) * 7 / 5))).isoformat()
    return {
        "tier": tier_id,
        "floor_pct": tier.get("floor_pct"),
        "deployed_at": d.isoformat(),
        "deployed_amount": round(float(deployed_amount), 2),
        "returned_amount": 0.0,
        "deadline_date": deadline,
        "returned": False,
        "return_basis": cfg.get("return", {}).get("basis", "exit-condition-not-pnl"),
    }


def check_return(state, tier_result, today=None, config=None):
    """检查是否需要归还储备。

    归还触发：① 已退出触发区间（当前层级低于动用时的层级）；② 超过期限。

    返回 dict：
        needed        是否需要归还
        reason        exit-condition / deadline / None
        outstanding   尚未归还的金额
        message       人类可读说明
    """
    cfg = _cfg(config)
    if not state or state.get("returned"):
        return {"needed": False, "reason": None, "outstanding": 0.0, "message": ""}

    outstanding = round(
        float(state.get("deployed_amount", 0)) - float(state.get("returned_amount", 0)), 2
    )
    if outstanding <= 0:
        return {"needed": False, "reason": None, "outstanding": 0.0, "message": ""}

    d = today or date.today()
    cur_tier = tier_result.get("tier", "L0")
    used_tier = state.get("tier", "L0")
    deadline_days = int(cfg.get("return", {}).get("deadline_trading_days", 20))

    # ① 退出触发区间：当前层级不再达到动用时的层级
    tier_rank = {t: i for i, t in enumerate(TIER_ORDER)}
    if tier_rank.get(cur_tier, 0) < tier_rank.get(used_tier, 0):
        return {
            "needed": True,
            "reason": "exit-condition",
            "outstanding": outstanding,
            "message": (
                f"已退出 {used_tier} 触发区间（当前 {cur_tier}）→ 按纪律减仓归还 ¥{outstanding:,.0f}"
                f"（不看盈亏）"
            ),
        }

    # ② 期限检查（按自然日近似交易日）
    deadline = state.get("deadline_date")
    if deadline:
        try:
            dl = date.fromisoformat(deadline)
        except ValueError:
            dl = None
        if dl and d >= dl:
            return {
                "needed": True,
                "reason": "deadline",
                "outstanding": outstanding,
                "message": (
                    f"{used_tier} 动用已超 {deadline_days} 个交易日仍未退出区间"
                    f" → 强制归还 ¥{outstanding:,.0f} 并复核是否需要止损"
                ),
            }

    return {
        "needed": False,
        "reason": None,
        "outstanding": outstanding,
        "message": f"{used_tier} 储备在场（¥{outstanding:,.0f}），未到归还条件",
    }
