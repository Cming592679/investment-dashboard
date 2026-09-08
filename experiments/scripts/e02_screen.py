"""E02 v0.1 — Market Regime 候选指标单变量筛查。

输入: PERSONAL_DATA_DIR/experiments/market_data/klines.json（E01-panel-v0.1）
输出: PERSONAL_DATA_DIR/experiments/results/E02_v0.1_results.json

内容: 每个候选指标(t) vs 篮子未来 5D/20D 收益与未来 20D 最大回撤 的 Spearman rho、
      低/中/高三分档均值、指标间高相关对、关键时点读数。
注意: 未来收益为 t+1..t+n；指标只用 <=t 数据（无决策时间穿越）。
      重叠窗口、样本内，rho 仅作描述，不做显著性推断。
"""
import json
import math
import os
import statistics

D = os.path.join(os.environ.get(
    "PERSONAL_DATA_DIR",
    "/home/cc/Acai-Knowledge/workspace/personal-investment-data"),
    "experiments", "market_data")
OUT_DIR = os.path.join(os.path.dirname(D), "results")

BASKET = ["sh512760", "sz159995", "sz159997", "sh512660",
          "sz159611", "sh000688", "sh513100", "sh513180"]
BROAD = "sh000300"
GROW = "sz399006"


def load():
    k = json.load(open(os.path.join(D, "klines.json")))
    days = set()
    for s in BASKET + [BROAD, GROW]:
        days.update(r["d"] for r in k[s]["rows"])
    days = sorted(d for d in days if d <= "2026-09-07")
    px = {s: {r["d"]: r["c"] for r in k[s]["rows"] if r["d"] <= "2026-09-07"}
          for s in BASKET + [BROAD, GROW]}
    N = len(days)
    C = {s: [px[s].get(d) for d in days] for s in BASKET + [BROAD, GROW]}
    return days, C


def ma(v, n, i):
    return None if i + 1 < n else sum(v[i - n + 1:i + 1]) / n


def rets(v):
    return [None] + [v[i] / v[i - 1] - 1 for i in range(1, len(v))]


def rsi(v, n=14):
    out = [None]
    ag = al = 0
    for i in range(1, len(v)):
        g = max(v[i] - v[i - 1], 0)
        l = max(v[i - 1] - v[i], 0)
        if i <= n:
            ag += g
            al += l
        else:
            ag = (ag * (n - 1) + g) / n
            al = (al * (n - 1) + l) / n
        out.append(100 if al == 0 else 100 - 100 / (1 + ag / al))
    return out


def trailing(v, n, i):
    if i - n + 1 < 0:
        return None
    return math.prod(1 + x for x in v[i - n + 1:i + 1] if x is not None) - 1


def fwd_ret(v, n, i):
    seg = [x for x in v[i + 1:i + 1 + n] if x is not None]
    return None if len(seg) < n else math.prod(1 + x for x in seg) - 1


def vol20(v, i):
    if i < 20:
        return None
    seg = [v[j] for j in range(i - 20, i + 1) if v[j] is not None]
    if len(seg) < 15:
        return None
    r = [math.log(seg[j] / seg[j - 1]) for j in range(1, len(seg))]
    return statistics.pstdev(r) * math.sqrt(252) * 100


def fwd_dd(v, i, n):
    seg = v[i + 1:i + 1 + n]
    if len(seg) < n or any(x is None for x in seg):
        return None
    peak = -1e18
    mdd = 0
    for x in seg:
        peak = max(peak, x)
        mdd = min(mdd, (x - peak) / peak)
    return mdd * 100


def spearman(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 30:
        return None

    def rank(vals):
        o = sorted(range(len(vals)), key=lambda i: vals[i])
        rk = [0] * len(vals)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and vals[o[j + 1]] == vals[o[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for t in range(i, j + 1):
                rk[o[t]] = avg
            i = j + 1
        return rk

    rx = rank([p[0] for p in pairs])
    ry = rank([p[1] for p in pairs])
    n = len(pairs)
    mx = sum(rx) / n
    my = sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    sdx = math.sqrt(sum((x - mx) ** 2 for x in rx))
    sdy = math.sqrt(sum((y - my) ** 2 for y in ry))
    return cov / (sdx * sdy) if sdx > 0 and sdy > 0 else 0.0


def main():
    days, C = load()
    N = len(days)
    bret = []
    for i in range(N):
        rs = [C[s][i] / C[s][i - 1] - 1 for s in BASKET if C[s][i - 1]]
        bret.append(sum(rs) / len(rs) if rs else None)
    bpath = [None] * N
    acc = 1.0
    for i in range(N):
        if i > 0 and bret[i] is not None:
            acc *= 1 + bret[i]
        bpath[i] = acc
    c = C[BROAD]

    IND = {}
    IND["csi_ma20"] = [(c[i] / ma(c, 20, i) - 1) * 100 if ma(c, 20, i) else None
                       for i in range(N)]
    IND["csi_ma200"] = [(c[i] / ma(c, 200, i) - 1) * 100 if ma(c, 200, i) else None
                        for i in range(N)]
    IND["csi_mom20"] = [trailing(rets(c), 20, i) for i in range(N)]
    IND["csi_mom60"] = [trailing(rets(c), 60, i) for i in range(N)]
    vols = [vol20(c, i) for i in range(N)]
    IND["csi_vol20"] = vols
    vp = []
    for i in range(N):
        cur = vols[i]
        if cur is None or i < 60:
            vp.append(None)
            continue
        hist = [vols[j] for j in range(max(0, i - 252), i) if vols[j] is not None]
        vp.append(100 * sum(1 for x in hist if x <= cur) / len(hist) if hist else None)
    IND["csi_vol_pct"] = vp

    keys = ["ma20", "ma50", "mom20", "rsi50", "dd60", "rs20"]
    abr = {x: [] for x in keys}
    for i in range(N):
        vals = {x: 0 for x in keys}
        cnt = 0
        for s in BASKET:
            v = C[s]
            m20 = ma(v, 20, i)
            m50 = ma(v, 50, i)
            if m20 is None:
                continue
            cnt += 1
            if v[i] >= m20:
                vals["ma20"] += 1
            if m50 is not None and v[i] >= m50:
                vals["ma50"] += 1
            r20 = trailing(rets(v), 20, i)
            if r20 is not None and r20 > 0:
                vals["mom20"] += 1
            rr = rsi(v)
            if rr[i] is not None and rr[i] > 50:
                vals["rsi50"] += 1
            if (v[i] / max(v[max(0, i - 60):i + 1]) - 1) * 100 < -5:
                vals["dd60"] += 1
            if r20 is not None:
                bc = trailing(rets(c), 20, i)
                if bc is not None and r20 > bc:
                    vals["rs20"] += 1
        for x in keys:
            abr[x].append(100 * vals[x] / cnt if cnt else None)
    for x in keys:
        IND["br_" + x] = abr[x]
    IND["grow_rel"] = [
        (trailing(rets(C[GROW]), 20, i) - trailing(rets(c), 20, i)) if i >= 19 else None
        for i in range(N)]
    IND["basket_vol20"] = [
        statistics.mean([vol20(C[s], i) for s in BASKET if vol20(C[s], i) is not None])
        if any(vol20(C[s], i) is not None for s in BASKET) else None
        for i in range(N)]

    f5 = [fwd_ret(bret, 5, i) for i in range(N)]
    f20 = [fwd_ret(bret, 20, i) for i in range(N)]
    fdd = [fwd_dd(bpath, i, 20) for i in range(N)]
    start = days.index("2023-01-03")
    idx = list(range(start, N - 20))
    Y5 = [f5[i] for i in idx]
    Y20 = [f20[i] for i in idx]
    YDD = [fdd[i] for i in idx]

    corr_rows = []
    for name in IND:
        A = [IND[name][i] for i in idx]
        for lab, Y in [("fwd5", Y5), ("fwd20", Y20), ("fwdDD20", YDD)]:
            corr_rows.append({"indicator": name, "outcome": lab,
                              "rho": round(spearman(A, Y), 4)})

    inds = list(IND)
    red = []
    for i in range(len(inds)):
        for j in range(i + 1, len(inds)):
            A = [IND[inds[i]][t] for t in idx]
            B = [IND[inds[j]][t] for t in idx]
            r = spearman(A, B)
            if r is not None and abs(r) > 0.7:
                red.append({"a": inds[i], "b": inds[j], "rho": round(r, 2)})

    def tercile(name):
        tri = sorted([(v, i) for i, v in enumerate([IND[name][t] for t in idx])
                      if v is not None])
        n = len(tri)
        third = n // 3
        out = []
        for g in [tri[:third], tri[third:2 * third], tri[2 * third:]]:
            if not g:
                out.append(None)
                continue
            ys5 = [Y5[i] for _, i in g if Y5[i] is not None]
            ys20 = [Y20[i] for _, i in g if Y20[i] is not None]
            yd = [YDD[i] for _, i in g if YDD[i] is not None]
            out.append({"range": (round(g[0][0], 2), round(g[-1][0], 2)),
                        "fwd5_pct": round(statistics.mean(ys5) * 100, 2) if ys5 else None,
                        "fwd20_pct": round(statistics.mean(ys20) * 100, 2) if ys20 else None,
                        "fwdDD20_pct": round(statistics.mean(yd), 2) if yd else None,
                        "n": len(g)})
        return out

    terc = {n: tercile(n) for n in
            ["csi_ma200", "csi_mom20", "br_ma50", "br_mom20",
             "csi_vol_pct", "br_dd60", "basket_vol20"]}

    def pct_rank(series, v):
        h = [x for x in series if x is not None]
        return round(100 * sum(1 for x in h if x <= v) / len(h), 0) if h and v is not None else None

    key_dates = []
    for d0 in ["2026-07-31", "2026-08-10", "2026-08-24", "2026-08-28", "2026-09-04"]:
        i = days.index(d0)
        row = {"date": d0}
        for n in ["csi_ma200", "br_ma50", "br_mom20", "csi_vol_pct", "br_dd60"]:
            row[n] = round(IND[n][i], 2) if IND[n][i] is not None else None
            row[n + "_pct"] = pct_rank([IND[n][t] for t in idx], IND[n][i])
        key_dates.append(row)

    res = {"dataset": "E01-panel-v0.1", "analysis": "E02-v0.1",
           "window": "2023-01-03..2026-09-07", "n": len(idx),
           "basket": BASKET, "spearman": corr_rows, "redundant_pairs": red,
           "terciles": terc, "key_dates": key_dates,
           "note": "Forward outcomes use t+1..t+n; indicators use <=t. "
                   "Descriptive only (overlapping, in-sample). Breadth=8 proxies."}
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "E02_v0.1_results.json")
    json.dump(res, open(path, "w"), ensure_ascii=False, indent=1)
    print("saved", path)
    top = sorted(corr_rows, key=lambda r: abs(r["rho"]), reverse=True)[:8]
    for r in top:
        print(r)
    print("redundant:", red)


if __name__ == "__main__":
    main()
