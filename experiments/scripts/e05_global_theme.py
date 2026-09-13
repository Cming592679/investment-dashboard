"""E05 v0.1 — Global vs Theme Risk Budget + 状态条件化预算。

模型（费用场景 0 / 0.5 / 1.5%，赎回侧计费；t-1 信息 → t 收盘调仓）：
  BH100 / CONST80                 基线
  GLOBAL_DISC                     全局波动率分位离散档（E04 参照）
  COND_AND                        vol_pct>=75 且 广度<50% 时才降至 0.6
  COND_AND_DEEP                   同上条件 → 0.4
  COND_OR                         vol_pct>=75 或 广度<50% → 0.7
  THEME_VOL                       每个主题按自身波动率分位降档（独立 sleeve）
  THEME_TREND                     每个主题跌破自身 MA50 → 暴露 0.5
  THEME_VOLxTREND                 两者取更保守
窗口 2023-01-03 → 2026-09-07；输出 PERSONAL_DATA_DIR/experiments/results/E05_v0.1_results.json
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


def ladder(pct, tiers=((50, 1.0), (75, 0.85), (90, 0.70)), floor=0.50):
    if pct is None:
        return 1.0
    for t, e in tiers:
        if pct < t:
            return e
    return floor


def metrics(eq, rets, exp_avg, turnover, switches, days, start, end, fee, basket_daily):
    n = len(eq) - 1
    years = n / 252
    cagr = eq[-1] ** (1 / years) - 1 if years > 0 and eq[-1] > 0 else None
    peak = -1e18
    mdd = 0.0
    for v in eq:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    vol = statistics.pstdev(rets) * math.sqrt(252) if len(rets) > 1 else None
    return {
        "total_return_pct": round((eq[-1] - 1) * 100, 2),
        "cagr_pct": round(cagr * 100, 2) if cagr else None,
        "max_dd_pct": round(mdd * 100, 2),
        "ann_vol_pct": round(vol, 2) if vol else None,
        "calmar": round(cagr / abs(mdd), 2) if (cagr and mdd < 0) else None,
        "avg_exposure_pct": round(exp_avg * 100, 1),
        "turnover_per_year": round(turnover / (end - start) * 252, 1),
        "switches": switches,
        "sell_fee": fee,
    }


def simulate_single(exp, bret, start, end, fee_rate):
    eq = [1.0]
    fees = 0.0
    turn = 0.0
    sw = 0
    rets = []
    for t in range(start + 1, end + 1):
        r = bret[t] or 0.0
        eq_after = eq[-1] * (1 + exp[t - 1] * r)
        d = exp[t] - exp[t - 1]
        if abs(d) > 1e-9:
            sw += 1
            turn += abs(d)
        if d < 0:
            f = abs(d) * eq_after * fee_rate
            eq_after -= f
            fees += f
        rets.append(eq_after / eq[-1] - 1)
        eq.append(eq_after)
    return eq, rets, turn, sw


def simulate_theme(exp_s, sret, start, end, fee_rate):
    """每个主题独立 sleeve（等权资本 1/8），sleeve 内现金不赚收益。"""
    S = len(BASKET)
    E = [1.0 / S] * S
    eq = [1.0]
    rets = []
    turn = 0.0
    sw = 0
    for t in range(start + 1, end + 1):
        tot = 0.0
        for si in range(S):
            e = exp_s[si][t - 1]
            r = sret[si][t] or 0.0
            E[si] *= (1 + e * r)
            d = exp_s[si][t] - exp_s[si][t - 1]
            if abs(d) > 1e-9:
                sw += 1
                turn += abs(d) / S
            if d < 0:
                E[si] -= abs(d) * E[si] * fee_rate
            tot += E[si]
        rets.append(tot / eq[-1] - 1)
        eq.append(tot)
    return eq, rets, turn, sw


def main():
    days, C = load()
    N = len(days)
    bret = []
    sret = [[None] * N for _ in BASKET]
    for t in range(N):
        rs = []
        for si, s in enumerate(BASKET):
            r = C[s][t] / C[s][t - 1] - 1 if t > 0 and C[s][t - 1] else None
            sret[si][t] = r
            if r is not None:
                rs.append(r)
        bret.append(sum(rs) / len(rs) if len(rs) == len(BASKET) else None)

    bvol = []
    for i in range(N):
        vals = [vol20(C[s], i) for s in BASKET]
        bvol.append(statistics.mean([v for v in vals if v is not None])
                    if all(v is not None for v in vals) else None)
    bvol_pct = [pct_rank_hist(bvol, i) for i in range(N)]
    br50 = []
    for i in range(N):
        cnt = tot = 0
        for s in BASKET:
            m = ma(C[s], 50, i)
            if m is None:
                continue
            tot += 1
            if C[s][i] >= m:
                cnt += 1
        br50.append(100 * cnt / tot if tot else None)
    s_volpct = []
    s_trend = []
    for s in BASKET:
        vs = [vol20(C[s], i) for i in range(N)]
        s_volpct.append([pct_rank_hist(vs, i) for i in range(N)])
        s_trend.append([(C[s][i] >= ma(C[s], 50, i)) if ma(C[s], 50, i) else None
                        for i in range(N)])

    start = days.index("2023-01-03")
    end = N - 2

    def shift(exp):
        return [exp[0]] + exp[:-1]

    exp_global = shift([ladder(p) for p in bvol_pct])
    exp_cond_and = shift([
        0.6 if (bvol_pct[i] is not None and br50[i] is not None
                and bvol_pct[i] >= 75 and br50[i] < 50) else 1.0
        for i in range(N)])
    exp_cond_and_deep = shift([
        0.4 if (bvol_pct[i] is not None and br50[i] is not None
                and bvol_pct[i] >= 75 and br50[i] < 50) else 1.0
        for i in range(N)])
    exp_cond_or = shift([
        0.7 if ((bvol_pct[i] is not None and bvol_pct[i] >= 75)
                or (br50[i] is not None and br50[i] < 50)) else 1.0
        for i in range(N)])
    exp_theme_vol = [shift([ladder(s_volpct[si][i]) for i in range(N)])
                     for si in range(len(BASKET))]
    exp_theme_trend = [shift([(1.0 if s_trend[si][i] else 0.5) if s_trend[si][i] is not None else 1.0
                              for i in range(N)]) for si in range(len(BASKET))]
    exp_theme_mix = [shift([
        min(ladder(s_volpct[si][i]),
            1.0 if s_trend[si][i] else 0.5) if s_trend[si][i] is not None else 1.0
        for i in range(N)]) for si in range(len(BASKET))]

    single_models = {
        "BH100": [1.0] * N,
        "CONST80": [0.8] * N,
        "GLOBAL_DISC": exp_global,
        "COND_AND": exp_cond_and,
        "COND_AND_DEEP": exp_cond_and_deep,
        "COND_OR": exp_cond_or,
    }
    theme_models = {
        "THEME_VOL": exp_theme_vol,
        "THEME_TREND": exp_theme_trend,
        "THEME_VOLxTREND": exp_theme_mix,
    }
    out = {"window": [days[start], days[end]], "basket": BASKET, "models": {}}
    for name, exp in single_models.items():
        out["models"][name] = {}
        for fee in (0.0, 0.005, 0.015):
            eq, rets, turn, sw = simulate_single(exp, bret, start, end, fee)
            avg = statistics.mean(exp[start:end + 1])
            out["models"][name][f"fee_{fee}"] = metrics(
                eq, rets, avg, turn, sw, days, start, end, fee, bret)
    for name, exps in theme_models.items():
        out["models"][name] = {}
        for fee in (0.0, 0.005, 0.015):
            eq, rets, turn, sw = simulate_theme(exps, sret, start, end, fee)
            avg = statistics.mean(
                statistics.mean([exps[si][t] for si in range(len(BASKET))])
                for t in range(start, end + 1))
            out["models"][name][f"fee_{fee}"] = metrics(
                eq, rets, avg, turn, sw, days, start, end, fee, bret)

    # 子区间 2026-07-31 → 09-07（费用 0.5%）
    s2 = days.index("2026-07-31")
    sub = {}
    for name, exp in single_models.items():
        eq, rets, turn, sw = simulate_single(exp, bret, s2, end, 0.005)
        avg = statistics.mean(exp[s2:end + 1])
        m = metrics(eq, rets, avg, turn, sw, days, s2, end, 0.005, bret)
        sub[name] = {"ret": m["total_return_pct"], "dd": m["max_dd_pct"],
                     "avg_exp": m["avg_exposure_pct"], "switches": sw}
    for name, exps in theme_models.items():
        eq, rets, turn, sw = simulate_theme(exps, sret, s2, end, 0.005)
        avg = statistics.mean(
            statistics.mean([exps[si][t] for si in range(len(BASKET))])
            for t in range(s2, end + 1))
        m = metrics(eq, rets, avg, turn, sw, days, s2, end, 0.005, bret)
        sub[name] = {"ret": m["total_return_pct"], "dd": m["max_dd_pct"],
                     "avg_exp": m["avg_exposure_pct"], "switches": sw}
    out["sub_window_2026H2_fee0.5"] = sub

    # ── E05b：主题级 + 换手控制 ──
    def throttle(exp, min_change):
        res = [exp[0]]
        cur = exp[0]
        for i in range(1, len(exp)):
            if abs(exp[i] - cur) >= min_change:
                cur = exp[i]
            res.append(cur)
        return res

    def hold_days(exp, min_days):
        res = []
        last_change = -10 ** 9
        cur = exp[0]
        for i in range(len(exp)):
            di = date.fromisoformat(days[i]).toordinal()
            if abs(exp[i] - cur) > 1e-9 and di - last_change >= min_days:
                cur = exp[i]
                last_change = di
            res.append(cur)
        return res

    def monthly(exp):
        res = [exp[0]]
        cur = exp[0]
        for i in range(1, len(exp)):
            if days[i][8:10] <= "03":
                cur = exp[i]
            res.append(cur)
        return res

    e05b = {}
    e05b_exps = {}
    for base_name, exps in theme_models.items():
        variants = {
            "throttle15": [throttle(e, 0.15) for e in exps],
            "hold30d": [hold_days(e, 30) for e in exps],
            "monthly": [monthly(e) for e in exps],
        }
        for vname, vexp in variants.items():
            row = {}
            for fee in (0.0, 0.005, 0.015):
                eq, rets, turn, sw = simulate_theme(vexp, sret, start, end, fee)
                avg = statistics.mean(
                    statistics.mean([vexp[si][t] for si in range(len(BASKET))])
                    for t in range(start, end + 1))
                row[f"fee_{fee}"] = metrics(eq, rets, avg, turn, sw,
                                            days, start, end, fee, bret)
            e05b[f"{base_name}|{vname}"] = row
            e05b_exps[f"{base_name}|{vname}"] = vexp
    out["e05b_theme_turnover_control"] = e05b

    # E05b 分年度（fee 0.5%）
    out["e05b_yearly_fee0.5"] = {}
    for year in ["2023", "2024", "2025", "2026"]:
        di = [i for i, d in enumerate(days) if d.startswith(year) and start <= i <= end]
        if len(di) < 20:
            continue
        s_y, e_y = di[0], di[-1]
        row = {}
        for key, vexp in e05b_exps.items():
            eq, rets, turn, sw = simulate_theme(vexp, sret, s_y, e_y, 0.005)
            avg = statistics.mean(
                statistics.mean([vexp[si][t] for si in range(len(BASKET))])
                for t in range(s_y, e_y + 1))
            m = metrics(eq, rets, avg, turn, sw, days, s_y, e_y, 0.005, bret)
            row[key] = {"ret": m["total_return_pct"], "dd": m["max_dd_pct"],
                        "calmar": m["calmar"], "switches": sw}
        # 基线
        for bname, bexp in (("BH100", [1.0] * N), ("CONST80", [0.8] * N)):
            eq, rets, turn, sw = simulate_single(bexp, bret, s_y, e_y, 0.005)
            m = metrics(eq, rets, statistics.mean(bexp[s_y:e_y + 1]),
                        turn, sw, days, s_y, e_y, 0.005, bret)
            row[bname] = {"ret": m["total_return_pct"], "dd": m["max_dd_pct"],
                          "calmar": m["calmar"], "switches": sw}
        out["e05b_yearly_fee0.5"][year] = row

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "E05_v0.1_results.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    print("saved", path)
    for name in out["models"]:
        m = out["models"][name]["fee_0.005"]
        m0 = out["models"][name]["fee_0.0"]
        m15 = out["models"][name]["fee_0.015"]
        print(f'{name:16s} ret(0/0.5/1.5)={m0["total_return_pct"]:7.2f}/{m["total_return_pct"]:7.2f}/{m15["total_return_pct"]:7.2f} '
              f'DD={m["max_dd_pct"]:7.2f} Calmar={m["calmar"]} vol={m["ann_vol_pct"]} avgExp={m["avg_exposure_pct"]} turn/y={m["turnover_per_year"]} sw={m["switches"]}')
    print("sub 2026H2:", json.dumps(sub, ensure_ascii=False))
    for key, row in out["e05b_theme_turnover_control"].items():
        m = row["fee_0.005"]
        m15 = row["fee_0.015"]
        print(f'{key:26s} ret(0.5/1.5)={m["total_return_pct"]:7.2f}/{m15["total_return_pct"]:7.2f} '
              f'DD={m["max_dd_pct"]:7.2f} Calmar={m["calmar"]} turn/y={m["turnover_per_year"]} sw={m["switches"]}')
    for year, row in out["e05b_yearly_fee0.5"].items():
        keep = {k: v for k, v in row.items()
                if k in ("BH100", "CONST80", "THEME_VOL|hold30d", "THEME_VOL|monthly",
                         "THEME_VOLxTREND|hold30d", "THEME_TREND|hold30d")}
        print("yearly", year, json.dumps(keep, ensure_ascii=False))


if __name__ == "__main__":
    main()
