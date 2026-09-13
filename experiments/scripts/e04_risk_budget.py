"""E04/E06 v0.1 — Risk Budget 回测（波动率 → 总暴露）。

模型：
  BH100            满仓持有
  CONST80          恒定 80% 暴露
  DISC_basketvol   篮子波动率 252D 分位 → 离散档位（100/85/70/50）
  CONT_basketvol   篮子波动率分位 → 连续线性降暴露
  VOLTARGET        目标波动率（暴露 = target/current，封顶 1、下限 floor）
  DISC+TREND       离散档位 × 趋势修饰（组合广度 >MA50 <50% 时再 ×0.85）
费用：赎回侧按 |Δexp| 收费（申购费 0，符合 C 类）；场景 0% / 0.5% / 1.5%。
执行：exp[t] 用 t-1 及之前的指标决定，在 t 收盘调仓，承担 t→t+1 的收益（无未来数据）。
窗口：2023-01-03 → 2026-09-07；标尺：8 只代理等权篮子；另有 2026-07-31→09-07 子区间。
输出：PERSONAL_DATA_DIR/experiments/results/E04_E06_v0.1_results.json
"""
import json
import math
import os
import statistics
from datetime import date

DATA = os.path.join(os.environ.get(
    "PERSONAL_DATA_DIR",
    "/home/cc/Acai-Knowledge/workspace/personal-investment-data"),
    "experiments", "market_data")
OUT_DIR = os.path.join(os.path.dirname(DATA), "results")

BASKET = ["sh512760", "sz159995", "sz159997", "sh512660",
          "sz159611", "sh000688", "sh513100", "sh513180"]
BROAD = "sh000300"


def ma(v, n, i):
    return None if i + 1 < n else sum(v[i - n + 1:i + 1]) / n


def vol20(v, i):
    if i < 20:
        return None
    seg = [v[j] for j in range(i - 20, i + 1)]
    r = [math.log(seg[j] / seg[j - 1]) for j in range(1, len(seg))]
    return statistics.pstdev(r) * math.sqrt(252) * 100


def pct_rank_hist(series, i, lookback=252, min_obs=60):
    cur = series[i]
    if cur is None:
        return None
    hist = [series[j] for j in range(max(0, i - lookback), i) if series[j] is not None]
    if len(hist) < min_obs:
        return None
    return 100 * sum(1 for x in hist if x <= cur) / len(hist)


def load():
    k = json.load(open(os.path.join(DATA, "klines.json")))
    days = set()
    for s in BASKET + [BROAD]:
        days.update(r["d"] for r in k[s]["rows"])
    days = sorted(d for d in days if d <= "2026-09-07")
    px = {s: {r["d"]: r["c"] for r in k[s]["rows"] if r["d"] <= "2026-09-07"}
          for s in BASKET + [BROAD]}
    C = {s: [px[s].get(d) for d in days] for s in BASKET + [BROAD]}
    return days, C


def build_indicators(C, N):
    bret = []
    for i in range(N):
        rs = [C[s][i] / C[s][i - 1] - 1 for s in BASKET if i > 0 and C[s][i - 1]]
        bret.append(sum(rs) / len(rs) if rs else None)
    bvol = []
    for i in range(N):
        vals = [vol20(C[s], i) for s in BASKET]
        vals = [v for v in vals if v is not None]
        bvol.append(statistics.mean(vals) if len(vals) == len(BASKET) else None)
    bvol_pct = [pct_rank_hist(bvol, i) for i in range(N)]
    abr50 = []
    for i in range(N):
        cnt = tot = 0
        for s in BASKET:
            v = C[s]
            m50 = ma(v, 50, i)
            if m50 is None:
                continue
            tot += 1
            if v[i] >= m50:
                cnt += 1
        abr50.append(100 * cnt / tot if tot else None)
    return bret, bvol, bvol_pct, abr50


def exp_discrete(pct, ladder, thresholds):
    if pct is None:
        return 1.0
    for t, e in zip(thresholds, ladder):
        if pct < t:
            return e
    return ladder[-1]


def build_exposures(kind, bvol, bvol_pct, abr50, params):
    N = len(bvol)
    exp = [None] * N
    for i in range(N):
        if kind == "BH100":
            e = 1.0
        elif kind == "CONST80":
            e = 0.8
        elif kind == "DISC":
            e = exp_discrete(bvol_pct[i], params["ladder"], params["thresholds"])
        elif kind == "CONT":
            p = bvol_pct[i]
            e = 1.0 if p is None else max(params["floor"], min(1.0, 1.0 - params["k"] * (p - 50) / 50))
        elif kind == "VOLTARGET":
            cur = bvol[i]
            e = 1.0 if cur is None else max(params["floor"], min(1.0, params["target"] / cur))
        elif kind == "DISC_TREND":
            e = exp_discrete(bvol_pct[i], params["ladder"], params["thresholds"])
            if abr50[i] is not None and abr50[i] < 50:
                e = e * params["trend_mult"]
        else:
            raise ValueError(kind)
        exp[i] = e
    # 决策只用到 t-1 及之前：整体后移一天
    return [exp[0]] + exp[:-1]


def simulate(exp, bret, start, end, sell_fee):
    """exp[t] 在 t 收盘后生效，承担 t→t+1 收益；调仓费按 |Δexp|×当前权益（赎回侧）。"""
    eq = [1.0]
    fees = 0.0
    turnover = 0.0
    switches = 0
    strat_ret = []
    for t in range(start + 1, end + 1):
        r = bret[t]
        prev_exp = exp[t - 1]
        eq_after = eq[-1] * (1 + (prev_exp * r if r is not None else 0.0))
        d = exp[t] - exp[t - 1]
        fee = abs(d) * eq_after * sell_fee if d < 0 else 0.0
        turnover += abs(d)
        if abs(d) > 1e-9:
            switches += 1
        eq_after -= fee
        fees += fee
        eq.append(eq_after)
        base = eq[-2] if eq[-2] else 1.0
        strat_ret.append(eq_after / base - 1)
    return eq, fees, turnover, switches, strat_ret


def metrics(eq, strat_ret, exp, days, start, end, sell_fee, bret):
    n = len(eq) - 1
    years = n / 252
    total = eq[-1] - 1
    cagr = eq[-1] ** (1 / years) - 1 if years > 0 and eq[-1] > 0 else None
    peak = -1e18
    mdd = 0.0
    dd_start = dd_end = None
    cur_peak_i = 0
    for i, v in enumerate(eq):
        if v > peak:
            peak = v
            cur_peak_i = i
        dd = v / peak - 1
        if dd < mdd:
            mdd = dd
            dd_start, dd_end = cur_peak_i, i
    vol = statistics.pstdev(strat_ret) * math.sqrt(252) if len(strat_ret) > 1 else None
    calmar = (cagr / abs(mdd)) if (cagr is not None and mdd < 0) else None
    exps = exp[start:end + 1]
    avg_exp = statistics.mean(exps)
    under90 = 100 * sum(1 for e in exps if e < 0.9) / len(exps)

    # 上行/下行捕获、踏空与避险
    up_s = up_b = dn_s = dn_b = 0.0
    missed = saved = 0.0
    for t in range(start + 1, end + 1):
        r = bret[t]
        if r is None:
            continue
        e = exp[t - 1]
        if r > 0:
            up_s += e * r
            up_b += r
            missed += (1 - e) * r
        elif r < 0:
            dn_s += e * r
            dn_b += r
            saved += (1 - e) * (-r)
    return {
        "total_return_pct": round(total * 100, 2),
        "cagr_pct": round(cagr * 100, 2) if cagr is not None else None,
        "max_dd_pct": round(mdd * 100, 2),
        "dd_range": [days[dd_start], days[dd_end]] if dd_start is not None else None,
        "ann_vol_pct": round(vol, 2) if vol else None,
        "calmar": round(calmar, 2) if calmar else None,
        "avg_exposure_pct": round(avg_exp * 100, 1),
        "pct_days_exp_lt_90": round(under90, 1),
        "switches": None,  # 填充于调用方
        "turnover_oneway": None,
        "fee_paid_pct_of_equity": None,
        "upside_capture_pct": round(100 * up_s / up_b, 1) if up_b else None,
        "downside_capture_pct": round(100 * dn_s / dn_b, 1) if dn_b else None,
        "missed_upside_pct": round(missed * 100, 2),
        "avoided_downside_pct": round(saved * 100, 2),
        "sell_fee": sell_fee,
    }


def main():
    days, C = load()
    N = len(days)
    bret, bvol, bvol_pct, abr50 = build_indicators(C, N)
    start = days.index("2023-01-03")
    end = len(days) - 2  # 最后一天无次日收益

    target = statistics.median([v for v in bvol if v is not None][:252])
    models = [
        ("BH100", "BH100", {}),
        ("CONST80", "CONST80", {}),
        ("DISC_basketvol", "DISC", {"ladder": [1.0, 0.85, 0.70, 0.50], "thresholds": [50, 75, 90]}),
        ("CONT_basketvol", "CONT", {"k": 0.5, "floor": 0.5}),
        ("VOLTARGET", "VOLTARGET", {"target": target, "floor": 0.5}),
        ("DISC+TREND", "DISC_TREND", {"ladder": [1.0, 0.85, 0.70, 0.50], "thresholds": [50, 75, 90], "trend_mult": 0.85}),
    ]
    out = {"window": [days[start], days[end]], "n_days": end - start,
           "basket": BASKET, "vol_target_used": round(target, 2), "models": {}}
    for name, kind, params in models:
        exp = build_exposures(kind, bvol, bvol_pct, abr50, params)
        out["models"][name] = {}
        for fee in (0.0, 0.005, 0.015):
            eq, fees, turn, sw, sr = simulate(exp, bret, start, end, fee)
            m = metrics(eq, sr, exp, days, start, end, fee, bret)
            m["switches"] = sw
            m["turnover_oneway_per_year"] = round(turn / (end - start) * 252, 1)
            m["fee_paid_pct_of_equity"] = round(fees * 100, 2)
            out["models"][name][f"fee_{fee}"] = m

    # 子区间：2026-07-31 → 2026-09-07
    s2 = days.index("2026-07-31")
    e2 = end
    sub = {}
    for name, kind, params in models:
        exp = build_exposures(kind, bvol, bvol_pct, abr50, params)
        eq, fees, turn, sw, sr = simulate(exp, bret, s2, e2, 0.005)
        m = metrics(eq, sr, exp, days, s2, e2, 0.005, bret)
        sub[name] = {"total_return_pct": m["total_return_pct"], "max_dd_pct": m["max_dd_pct"],
                     "avg_exposure_pct": m["avg_exposure_pct"], "switches": sw}
    out["sub_window_2026H2_fee0.5"] = sub

    # E06 参数敏感性：离散档位 × 阈值
    grid = []
    ladders = {
        "A_100_85_70_50": [1.0, 0.85, 0.70, 0.50],
        "B_100_80_60_40": [1.0, 0.80, 0.60, 0.40],
        "C_100_90_75_55": [1.0, 0.90, 0.75, 0.55],
    }
    ths = {"T50_75_90": [50, 75, 90], "T60_80_90": [60, 80, 90], "T40_70_90": [40, 70, 90]}
    for ln, ladder in ladders.items():
        for tn, thr in ths.items():
            exp = build_exposures("DISC", bvol, bvol_pct, abr50,
                                  {"ladder": ladder, "thresholds": thr})
            eq, fees, turn, sw, sr = simulate(exp, bret, start, end, 0.005)
            m = metrics(eq, sr, exp, days, start, end, 0.005, bret)
            grid.append({"ladder": ln, "thresholds": tn,
                         "return_pct": m["total_return_pct"], "max_dd_pct": m["max_dd_pct"],
                         "calmar": m["calmar"], "ann_vol_pct": m["ann_vol_pct"],
                         "turnover_per_year": round(turn / (end - start) * 252, 1)})
    out["e06_grid"] = grid

    # ── E06b：换手控制（滞后阈值 / 周频 / 月频）与恒定暴露前沿 ──
    disc_exp = build_exposures("DISC", bvol, bvol_pct, abr50,
                               {"ladder": [1.0, 0.85, 0.70, 0.50],
                                "thresholds": [50, 75, 90]})

    def throttle(exp, min_change):
        res = [exp[0]]
        cur = exp[0]
        for i in range(1, len(exp)):
            if abs(exp[i] - cur) >= min_change:
                cur = exp[i]
            res.append(cur)
        return res

    def step_hold(exp, freq):
        res = [exp[0]]
        cur = exp[0]
        for i in range(1, len(exp)):
            d = days[i]
            upd = False
            if freq == "W" and date.fromisoformat(d).weekday() == 4:
                upd = True
            if freq == "M" and d[8:10] <= "03":
                upd = True
            if upd:
                cur = exp[i]
            res.append(cur)
        return res

    variants = {
        "DISC_throttle10pp": throttle(disc_exp, 0.10),
        "DISC_throttle20pp": throttle(disc_exp, 0.20),
        "DISC_weekly": step_hold(disc_exp, "W"),
        "DISC_monthly": step_hold(disc_exp, "M"),
    }
    out["e06b_turnover_control"] = {}
    for vname, vexp in variants.items():
        row = {}
        for fee in (0.0, 0.005, 0.015):
            eq, fees, turn, sw, sr = simulate(vexp, bret, start, end, fee)
            m = metrics(eq, sr, vexp, days, start, end, fee, bret)
            m["switches"] = sw
            m["turnover_oneway_per_year"] = round(turn / (end - start) * 252, 1)
            row[f"fee_{fee}"] = m
        out["e06b_turnover_control"][vname] = row

    out["const_frontier_fee0.5"] = []
    for e_target in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]:
        cexp = [e_target] * N
        eq, fees, turn, sw, sr = simulate(cexp, bret, start, end, 0.005)
        m = metrics(eq, sr, cexp, days, start, end, 0.005, bret)
        out["const_frontier_fee0.5"].append(
            {"exposure": e_target, "total_return_pct": m["total_return_pct"],
             "max_dd_pct": m["max_dd_pct"], "calmar": m["calmar"],
             "ann_vol_pct": m["ann_vol_pct"]})

    # ── 分年度 ──
    out["yearly_fee0.5"] = {}
    for year in ["2023", "2024", "2025", "2026"]:
        di = [i for i, d in enumerate(days) if d.startswith(year) and start <= i <= end]
        if len(di) < 20:
            continue
        s_y, e_y = di[0], di[-1]
        row = {}
        for name, kind, params in models:
            exp = build_exposures(kind, bvol, bvol_pct, abr50, params)
            eq, fees, turn, sw, sr = simulate(exp, bret, s_y, e_y, 0.005)
            m = metrics(eq, sr, exp, days, s_y, e_y, 0.005, bret)
            row[name] = {"ret": m["total_return_pct"], "dd": m["max_dd_pct"],
                         "calmar": m["calmar"], "switches": sw}
        out["yearly_fee0.5"][year] = row

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "E04_E06_v0.1_results.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    print("saved", path)
    for name in out["models"]:
        m0 = out["models"][name]["fee_0.0"]
        m5 = out["models"][name]["fee_0.005"]
        m15 = out["models"][name]["fee_0.015"]
        print(f'{name:16s} ret(0/0.5/1.5%)={m0["total_return_pct"]:7.2f}/{m5["total_return_pct"]:7.2f}/{m15["total_return_pct"]:7.2f} '
              f'DD={m5["max_dd_pct"]:7.2f} Calmar={m5["calmar"]} vol={m5["ann_vol_pct"]} avgExp={m5["avg_exposure_pct"]} turn/y={m5["turnover_oneway_per_year"]}')
    print("sub-window 2026H2 (fee0.5):", json.dumps(sub, ensure_ascii=False))
    for vname, row in out["e06b_turnover_control"].items():
        m = row["fee_0.005"]
        print(f'{vname:20s} ret(0.5%)={m["total_return_pct"]:7.2f} DD={m["max_dd_pct"]:7.2f} '
              f'Calmar={m["calmar"]} turn/y={m["turnover_oneway_per_year"]} switches={m["switches"]}')
    print("const frontier:", json.dumps(out["const_frontier_fee0.5"], ensure_ascii=False))
    print("yearly:", json.dumps(out["yearly_fee0.5"], ensure_ascii=False))


if __name__ == "__main__":
    main()
