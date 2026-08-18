"""portfolio.json 结构校验（P0-1d）。

目标：
- 必填字段 / 类型检查 / 重复项检查；
- 未知字段一律允许（为 v1.0 预留 evidence_stage / divergence / override 等扩展空间，
  避免下一次再做结构迁移）；
- 校验只产出警告，不修改任何数据；
- v1.1 语义：status = 生命周期，evidence_stage = 证据成熟度档位（tier 保留兼容读取）。

当前允许/保留字段清单（避免误报）：
top: updated, total_assets, cash, daily_return, holding_return, cumulative_return,
     holdings, sector_allocation, action_log, pending_plans, trade_rules,
     position_config, nav_updated, sector_allocation_live
holding: fund_name, fund_code, dashboard_id, sector, amount, daily_return,
     holding_return, holding_return_pct, nav, nav_date, status, day_return_pct,
     notes, shares, cost_basis, tier, base, max, theme, sell_shares,
     sell_settle_dates, live_conclusion, live_emoji, live_return_pct,
     live_return_date, live_prediction, evidence_stage
action: date, action, fund, reason, amount
plan: module, fund, direction, target, executed, remaining, status, trigger,
     action_if_triggered, action_if_not, note, created, fund_code, fund_name, condition
"""

import json
import os
import sys


TOP_LEVEL_REQUIRED = [
    ("holdings", list),
    ("cash", (int, float)),
]
TOP_LEVEL_NUMERIC = [
    "total_assets",
    "daily_return",
    "holding_return",
    "cumulative_return",
]

HOLDING_REQUIRED = [
    ("fund_code", str),
    ("amount", (int, float)),
    ("status", str),
]
HOLDING_NUMERIC = [
    "daily_return",
    "holding_return",
    "holding_return_pct",
    "nav",
    "day_return_pct",
    "shares",
    "cost_basis",
    "base",
    "max",
]

HOLDING_ENUM = {
    "evidence_stage": {"explore", "watch", "verify", "core", ""},
    "status": {"active", "sell_pending", "sold", "non_investment", "observe", ""},
    "tier": {"explore", "watch", "verify", "core", "sold", "non_investment", ""},
}


def _type_name(v):
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "dict"
    return type(v).__name__


def _expected_name(typ):
    if isinstance(typ, tuple):
        return "/".join(t.__name__ for t in typ)
    return typ.__name__


def validate_portfolio(pf):
    """返回警告列表；不修改数据。未知字段不做报错（预留兼容）。"""
    warnings = []
    if not isinstance(pf, dict):
        return ["portfolio 顶层必须是 object"]

    for key, typ in TOP_LEVEL_REQUIRED:
        if key not in pf:
            warnings.append(f"缺少必填字段: {key}")
        elif not isinstance(pf[key], typ):
            warnings.append(
                f"字段类型错误: {key} 期望 {_expected_name(typ)}，实际 {_type_name(pf[key])}"
            )
    for key in TOP_LEVEL_NUMERIC:
        if key in pf and pf[key] is not None and not isinstance(pf[key], (int, float)):
            warnings.append(f"字段类型错误: {key} 期望 number，实际 {_type_name(pf[key])}")

    holdings = pf.get("holdings")
    if isinstance(holdings, list):
        for i, h in enumerate(holdings):
            if not isinstance(h, dict):
                warnings.append(f"holdings[{i}] 不是 object")
                continue
            for key, typ in HOLDING_REQUIRED:
                if key not in h:
                    warnings.append(f"holdings[{i}] 缺少必填字段: {key}")
                elif not isinstance(h[key], typ):
                    warnings.append(
                        f"holdings[{i}].{key} 类型错误: 期望 {_expected_name(typ)}，实际 {_type_name(h[key])}"
                    )
            for key in HOLDING_NUMERIC:
                if key in h and h[key] is not None and not isinstance(h[key], (int, float)):
                    warnings.append(
                        f"holdings[{i}].{key} 类型错误: 期望 number，实际 {_type_name(h[key])}"
                    )
            for key, allowed in HOLDING_ENUM.items():
                if key in h and h[key] not in allowed and h[key] is not None:
                    warnings.append(
                        f"holdings[{i}].{key} 取值不在允许集合 {sorted(allowed)}: {h[key]!r}"
                    )

    # 重复项检查（只报告，不自动删除）
    seen = set()
    for i, a in enumerate(pf.get("action_log") or []):
        if not isinstance(a, dict):
            continue
        sig = (a.get("date"), a.get("action"), a.get("fund"), a.get("reason"))
        if sig in seen:
            warnings.append(f"action_log[{i}] 疑似重复条目: {sig}")
        seen.add(sig)

    seen_plans = set()
    for i, p in enumerate(pf.get("pending_plans") or []):
        if not isinstance(p, dict):
            continue
        sig = (p.get("module"), p.get("created"), p.get("direction"), p.get("target"))
        if sig in seen_plans:
            warnings.append(
                f"pending_plans[{i}] 疑似重复条目: module={p.get('module')} created={p.get('created')}"
            )
        seen_plans.add(sig)

    return warnings


def validate_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            pf = json.load(f)
    except Exception as e:
        return [f"文件读取/解析失败: {e}"]
    return validate_portfolio(pf)


if __name__ == "__main__":
    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(os.environ.get("PERSONAL_DATA_DIR", "."), "portfolio.json")
    )
    warnings = validate_file(path)
    if warnings:
        print(f"⚠ {len(warnings)} 条结构警告:")
        for w in warnings:
            print("  -", w)
    else:
        print("✅ portfolio.json 结构校验通过（无警告）")
