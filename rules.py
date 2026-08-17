"""rules.yaml 加载与校验（P1-1a）。

rules.yaml 是 Investment Rulebook v1.0 参数的单一事实源。
本模块提供加载与结构校验；运行时迁移（config/trading_rules 接入）在 P1-1b。
"""

import os
import sys

try:
    import yaml
except ImportError:  # 环境无 PyYAML 时回退到简单 key: value 解析（仅顶层标量）
    yaml = None


RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules.yaml")

REQUIRED_KEYS = [
    "version",
    "position_tiers",
    "risk_limits",
    "trend_gate",
    "rsi",
    "divergence",
    "panic",
    "structural_stop",
    "rebalance",
    "cadence",
]


def load_rules(path=None):
    """加载 rules.yaml 为 dict。"""
    path = path or RULES_PATH
    if yaml is not None:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    # 极简回退：只解析顶层标量（无 PyYAML 时的保底，不用于运行时）
    data = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip().strip("'\"")
    return data


def validate_rules(rules):
    """校验必需结构键是否存在；返回警告列表。"""
    warnings = []
    if not isinstance(rules, dict):
        return ["rules 顶层必须是 mapping"]
    for key in REQUIRED_KEYS:
        if key not in rules:
            warnings.append(f"缺少必需键: {key}")
    tiers = rules.get("position_tiers", {})
    if isinstance(tiers, dict) and not all(k in tiers for k in ("explore", "watch", "verify", "core")):
        warnings.append("position_tiers 需包含 explore/watch/verify/core")
    limits = rules.get("risk_limits", {})
    if isinstance(limits, dict) and not all(k in limits for k in
                                            ("single_fund_max", "sector_max", "theme_cluster_max", "cash_floor")):
        warnings.append("risk_limits 需包含 single_fund_max/sector_max/theme_cluster_max/cash_floor")
    return warnings


if __name__ == "__main__":
    rules = load_rules()
    warnings = validate_rules(rules)
    if warnings:
        print(f"⚠ {len(warnings)} 条规则校验警告:")
        for w in warnings:
            print("  -", w)
        sys.exit(1)
    print(f"✅ rules.yaml 加载成功（version {rules.get('version')}），结构校验通过")
