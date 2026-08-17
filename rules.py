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


def _scalar(val):
    """解析标量：null/bool/int/float/内联列表/字符串。"""
    val = val.strip()
    if not val:
        return ""
    if val.lower() == "null":
        return None
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        return [x.strip().strip("'\"").strip() for x in inner.split(",") if x.strip()] if inner else []
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    try:
        if val.replace("-", "", 1).isdigit():
            return int(val)
        if val.replace(".", "", 1).replace("-", "", 1).isdigit():
            return float(val)
    except ValueError:
        pass
    return val


def _parse_simple_yaml(text):
    """零依赖 YAML 子集解析（覆盖 rules.yaml 实际结构）：
    顶层标量、两级嵌套 dict（含 mode/entry_bands）、dash 列表、内联列表、行内注释。"""
    lines = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].rstrip()
            stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped.startswith("- "):
            lines.append((indent, None, stripped[2:].strip(), True))
        elif ":" in stripped:
            k, _, v = stripped.partition(":")
            lines.append((indent, k.strip().strip("'\""), v.strip(), False))

    def build(idx, indent):
        node = {}
        i = idx
        while i < len(lines):
            ind, key, val, is_list = lines[i]
            if ind < indent:
                break
            if is_list:
                i += 1
                continue
            if val == "":
                if i + 1 < len(lines) and lines[i + 1][3] and lines[i + 1][0] > ind:
                    lst = []
                    i += 1
                    while i < len(lines) and lines[i][3] and lines[i][0] > ind:
                        lst.append(_scalar(lines[i][2]))
                        i += 1
                    node[key] = lst
                    continue
                child, i = build(i + 1, ind + 1)
                node[key] = child
                continue
            node[key] = _scalar(val)
            i += 1
        return node, i

    data, _ = build(0, 0)
    return data


def load_rules(path=None):
    """加载 rules.yaml 为 dict（有 PyYAML 用之，否则用内置子集解析器）。"""
    path = path or RULES_PATH
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if yaml is not None:
        return yaml.safe_load(text) or {}
    return _parse_simple_yaml(text)


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
