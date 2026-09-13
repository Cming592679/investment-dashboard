"""E07 v0.1 — 主题级 Risk Budget 的样本外 / walk-forward 检验。

候选模型：THEME_VOL + 最短持有（E05 v0.1 最强 CANDIDATE）。
参数网格（27 组）：波动率阈值 3 种 × 暴露阶梯 3 种 × 最短持有 20/30/45 天。

检验方式：
  A. Split-sample：2023-01~2024-12 选参（按 Calmar），2025-01~2026-09 样本外评估；
  B. Rolling：OOS 每 6 个月，用之前 24 个月重新选参，拼接成连续样本外曲线；
  C. 对照：基线（BH100 / CONST80）、固定默认参数、split 选出的固定参数。
费用：0.5% 与 1.5%（赎回侧，简化）；真实 C 类 ≥30 天持有为 0%，故结果为保守上界。
输出：PERSONAL_DATA_DIR/experiments/results/E07_walkforward_v0.1_results.json
"""
import json
import os
import statistics
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e05_global_theme as e05  # noqa: E402

LADDERS = {
    "L_A": [1.0, 0.85, 0.70, 0.50],
    "L_C": [1.0, 0.90, 0.75, 0.55],
    "L_B": [1.0, 0.80, 0.60, 0.40],
}
THRESHOLDS = {
    "T50_75_90": [50, 75, 90],
    "T60_80_90": [60, 80, 90],
    "T40_70_90": [40, 70, 90],
}
HOLDS = [20, 30, 45]
DEFAULT = ("L_A", "T50_75_90", 30)


def build_grid():
    return [(ln, tn, h) for ln in LADDERS for tn in THRESHOLDS for h in HOLDS]


def main():
    days, C = e05.load()
    N = len(days)
    bret = []
    sret = [[None] * N for _ in e05.BASKET]
    for t in range(N):
        rs = []
        for si, s in enumerate(e05.BASKET):
            r = C[s][t] / C[s][t - 1] - 1 if t > 0 and C[s][t - 1] else None
            sret[si][t] = r
            if r is not None:
                rs.append(r)
        bret.append(sum(rs) / len(rs) if len(rs) == len(e05.BASKET) else None)

    s_volpct = []
    for s in e05.BASKET:
        vs = [e05.vol20(C[s], i) for i in range(N)]
        s_volpct.append([e05.pct_rank_hist(vs, i) for i in range(N)])

    def theme_exposures(ladder, thresholds, hold_days):
        exps = []
        for si in range(len(e05.BASKET)):
            raw = []
            for i in range(N):
                p = s_volpct[si][i]
                if p is None:
                    raw.append(1.0)
                    continue
                e = ladder[-1]
                for th, ev in zip(thresholds, ladder):
                    if p < th:
                        e = ev
                        break
                raw.append(e)
            res = []
            cur = raw[0]
            last = -10 ** 9
            for i in range(N):
                di = date.fromisoformat(days[i]).toordinal()
                if abs(raw[i] - cur) > 1e-9 and di - last >= hold_days:
                    cur = raw[i]
                    last = di
                res.append(cur)
            exps.append([res[0]] + res[:-1])  # t-1 决策 → t 生效
        return exps

    def evaluate(combo, s_i, e_i, fee):
        ln, tn, h = combo
        exps = theme_exposures(LADDERS[ln], THRESHOLDS[tn], h)
        eq, rets, turn, sw = e05.simulate_theme(exps, sret, s_i, e_i, fee)
        avg = statistics.mean(
            statistics.mean([exps[si][t] for si in range(len(e05.BASKET))])
            for t in range(s_i, e_i + 1))
        return e05.metrics(eq, rets, avg, turn, sw, days, s_i, e_i, fee, bret), exps

    def baseline(exposure, s_i, e_i, fee=0.005):
        exp = [exposure] * N
        eq, rets, turn, sw = e05.simulate_single(exp, bret, s_i, e_i, fee)
        return e05.metrics(eq, rets, exposure, turn, sw, days, s_i, e_i, fee, bret)

    grid = build_grid()

    def select_best(s_i, e_i, fee=0.005):
        scored = []
        for combo in grid:
            m, _ = evaluate(combo, s_i, e_i, fee)
            scored.append((m["calmar"] or -9, m["total_return_pct"], combo))
        scored.sort(reverse=True)
        return scored

    # ── A. Split-sample ──
    s_tr = days.index("2023-01-03")
    e_tr = max(i for i, d in enumerate(days) if d <= "2024-12-31")
    s_te = min(i for i, d in enumerate(days) if d >= "2025-01-01")
    e_te = N - 2
    ranked = select_best(s_tr, e_tr)
    best_combo = ranked[0][2]
    out = {"split": {"train": [days[s_tr], days[e_tr]], "test": [days[s_te], days[e_te]],
                     "best_on_train": best_combo,
                     "top5_train": [{"combo": c, "calmar": round(r, 2)} for r, _, c in ranked[:5]]}}
    test_rows = {}
    for label, combo in [("best_on_train", best_combo), ("default", DEFAULT)]:
        for fee in (0.005, 0.015):
            m, _ = evaluate(combo, s_te, e_te, fee)
            test_rows[f"{label}_fee{fee}"] = m
    for label, expo in [("BH100", 1.0), ("CONST80", 0.8)]:
        test_rows[f"{label}_fee0.005"] = baseline(expo, s_te, e_te)
    out["split"]["test_results"] = test_rows
    # 训练集前 5 名在测试集的表现（选择稳健性）
    out["split"]["top5_test"] = []
    for r, _, combo in ranked[:5]:
        m, _ = evaluate(combo, s_te, e_te, 0.005)
        out["split"]["top5_test"].append(
            {"combo": combo, "train_calmar": round(r, 2),
             "test_ret": m["total_return_pct"], "test_dd": m["max_dd_pct"],
             "test_calmar": m["calmar"]})

    # ── B. Rolling OOS（每 6 个月重选，前 24 个月训练）──
    windows = []
    for oos_start in ["2025-01-01", "2025-07-01", "2026-01-01", "2026-07-01"]:
        try:
            s_o = min(i for i, d in enumerate(days) if d >= oos_start)
        except ValueError:
            continue
        if s_o >= e_te:
            continue
        next_starts = [d for d in ["2025-07-01", "2026-01-01", "2026-07-01", "2027-01-01"]
                       if d > oos_start]
        e_o = e_te
        for ns in next_starts:
            cands = [i for i, d in enumerate(days) if d >= ns]
            if not cands:
                break
            cand = cands[0]
            if cand > s_o:
                e_o = cand - 1
                break
        s_tr_w = min(i for i, d in enumerate(days)
                     if d >= _minus_months(oos_start, 24))
        windows.append({"oos": [days[s_o], days[e_o]], "train": [days[s_tr_w], days[s_o - 1]],
                        "s_o": s_o, "e_o": e_o, "s_tr": s_tr_w})

    selection_history = []
    combo_windows = []
    for w in windows:
        ranked_w = select_best(w["s_tr"], w["s_o"] - 1)
        combo = ranked_w[0][2]
        selection_history.append({"oos": w["oos"], "chosen": combo,
                                  "train_calmar": round(ranked_w[0][0], 2)})
        combo_windows.append((combo, w["s_o"], w["e_o"]))

    # 拼接 OOS：逐窗口用各自参数
    s_oos = windows[0]["s_o"]
    composed = [[None] * N for _ in range(len(e05.BASKET))]
    for combo, s_o, e_o in combo_windows:
        exps = theme_exposures(LADDERS[combo[0]], THRESHOLDS[combo[1]], combo[2])
        for si in range(len(e05.BASKET)):
            for t in range(s_o, e_o + 1):
                composed[si][t] = exps[si][t]
    for si in range(len(e05.BASKET)):
        for t in range(s_oos):
            composed[si][t] = 1.0
    oos_rows = {}
    for fee in (0.005, 0.015):
        eq, rets, turn, sw = e05.simulate_theme(composed, sret, s_oos, e_te, fee)
        avg = statistics.mean(
            statistics.mean([composed[si][t] for si in range(len(e05.BASKET))])
            for t in range(s_oos, e_te + 1))
        oos_rows[f"rolling_selected_fee{fee}"] = e05.metrics(
            eq, rets, avg, turn, sw, days, s_oos, e_te, fee, bret)
    for label, combo in [("default_fixed", DEFAULT)]:
        for fee in (0.005, 0.015):
            m, _ = evaluate(combo, s_oos, e_te, fee)
            oos_rows[f"{label}_fee{fee}"] = m
    for label, expo in [("BH100", 1.0), ("CONST80", 0.8)]:
        oos_rows[f"{label}_fee0.005"] = baseline(expo, s_oos, e_te)
    out["rolling"] = {"windows": selection_history,
                      "distinct_choices": len({s["chosen"] for s in selection_history}),
                      "oos_period": [days[s_oos], days[e_te]],
                      "oos_results": oos_rows}

    OUT_DIR = os.path.join(os.path.dirname(e05.DATA), "results")
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "E07_walkforward_v0.1_results.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    print("saved", path)
    print("train best:", best_combo)
    for k, v in test_rows.items():
        print(f'  TEST {k:22s} ret={v["total_return_pct"]:7.2f} DD={v["max_dd_pct"]:7.2f} Calmar={v["calmar"]} turn/y={v["turnover_per_year"]}')
    print("top5 on train -> test:")
    for r in out["split"]["top5_test"]:
        print("  ", r)
    print("rolling windows:", json.dumps(selection_history, ensure_ascii=False))
    for k, v in oos_rows.items():
        print(f'  OOS {k:26s} ret={v["total_return_pct"]:7.2f} DD={v["max_dd_pct"]:7.2f} Calmar={v["calmar"]} turn/y={v["turnover_per_year"]}')


def _minus_months(ymd, months):
    y, m, d = (int(x) for x in ymd.split("-"))
    m -= months
    while m <= 0:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}-{d:02d}"


if __name__ == "__main__":
    main()
