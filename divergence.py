"""Price–Fundamental Divergence 统一层（Rulebook §5.2）

价格是输入，基本面/Thesis 是解释框架；两者之间的背离才可能形成交易机会。
本模块收敛 app.py._fundamental_state_local 与 intraday_check._fundamental_state
为单一实现，并提供六类背离分类，供 信号 / 计划 / 组合 共用。

- 不修改任何投资规则；RSI 等仅作为 Signal 输入（B12）。
- 系统负责发现异常偏离；人负责解释背离是否合理（C19/C20）。
- 自动执行的只有 ⑥ Thesis 证伪 Exit；其余均为观察或候选（需人工确认）。

六类（Rulebook §5.2）：
  ① Price-only           纯价格变动，Thesis/基本面/估值/趋势无变化 → 只能观察/提醒
  ② Price+Thesis         2a 跌+Thesis完好 → 吸入 Add 候选；2b 涨+Thesis完好 → 观察
  ③ Price+Fundamental    3a/3b/3c 基本面恶化（未证伪）→ Reduce 候选
  ④ Price+Valuation      4a 涨幅透支 → Reduce 候选；4b 深度回调（无固定阈值）→ Add 候选
  ⑤ Price+Trend          5a 量能背离；5b 破位但基本面正常 → 谨慎观察；5c 三档分级
  ⑥ Thesis Invalidation  证伪 → 立即 Exit（自动，事件驱动，不等周/月）
"""


WEAK_CONCLUSIONS = ("考虑跑路", "高位警惕")


def fundamental_state(dash_data):
    """基本面解释框架：结论 + 领先指标方向，输出结构化状态。

    Returns:
        dict: level("ok"|"warning"|"weak") / conclusion / ups / downs / flats /
              lead_str / message
    """
    d = dash_data or {}
    a = d.get("assessment") or {}
    conclusion = a.get("conclusion", "")
    leading = d.get("leading_indicators") or {}
    ups = sum(1 for v in leading.values() if v.get("trend") == "up")
    downs = sum(1 for v in leading.values() if v.get("trend") == "down")
    flats = len(leading) - ups - downs
    lead_str = f"，领先 {ups}↑{flats}→{downs}↓" if leading else ""
    if conclusion in WEAK_CONCLUSIONS:
        level = "weak"
        text = f"基本面走弱（结论：{conclusion}{lead_str}）"
    elif downs > 0:
        level = "warning"
        text = f"基本面转弱信号（结论：{conclusion}{lead_str}）"
    else:
        level = "ok"
        text = f"基本面正常（结论：{conclusion}{lead_str}）"
    return {
        "level": level,
        "conclusion": conclusion,
        "ups": ups,
        "downs": downs,
        "flats": flats,
        "lead_str": lead_str,
        "message": text,
    }


def fundamental_context(dash_data):
    """根据基本面状态生成展示上下文（弱 → 离场处理提示）。"""
    st = fundamental_state(dash_data)
    if st["level"] == "weak":
        return f"⚠ {st['message']} → 应按离场计划处理，不应等回调再进；请人工复核该计划"
    if st["level"] == "warning":
        return f"⚠ {st['message']} → 回调再进逻辑需复核，接近离场条件则改为减仓"
    return st["message"]


def classify_divergence(fundamental=None, day_return_pct=None, thesis_invalidated=False):
    """六类 Price–Fundamental Divergence 分类（Rulebook §5.2）。

    Args:
        fundamental: fundamental_state() 的返回值（level 至少为 ok/warning/weak）。
        day_return_pct: 当日涨跌幅（%），None 表示无价格读数。
        thesis_invalidated: 是否命中 Thesis 证伪条件（与价格无关）。

    Returns:
        dict: category / disposition / needs_confirm / auto / label
        disposition ∈ observe | add_candidate | reduce_candidate | exit
        auto 仅 ⑥ 为 True（唯一自动执行路径）。
    """
    fs = fundamental or {"level": "ok"}
    level = fs.get("level")

    if thesis_invalidated:
        return {
            "category": "⑥",
            "disposition": "exit",
            "needs_confirm": False,
            "auto": True,
            "label": "Thesis 证伪 → 立即 Exit（自动）",
        }

    if level == "weak":
        # ③ 基本面恶化（未证伪）：价格方向不改变处置，只影响优先级；
        # 证伪线命中才进入 ⑥（自动 Exit）。
        return {
            "category": "③",
            "disposition": "reduce_candidate",
            "needs_confirm": True,
            "auto": False,
            "label": "基本面走弱 → 离场/减仓优先",
        }

    r = day_return_pct
    if r is not None:
        if r <= -3:
            return {
                "category": "②a",
                "disposition": "add_candidate",
                "needs_confirm": True,
                "auto": False,
                "label": "价格回调+基本面完好 → 逆向吸入候选（人工确认）",
            }
        if r >= 3:
            return {
                "category": "②b",
                "disposition": "observe",
                "needs_confirm": False,
                "auto": False,
                "label": "今日大涨+基本面未变 → 观察不追高",
            }

    return {
        "category": "①",
        "disposition": "observe",
        "needs_confirm": False,
        "auto": False,
        "label": "—",
    }
