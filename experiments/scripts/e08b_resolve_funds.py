"""E08b — 把台账里的基金名称解析为代码，并抓取对应净值序列（用于 FIFO 精算）。

输入：experiments/ledger/trades.json
输出：experiments/ledger/fund_resolution.json, fund_navs_ledger.json
"""
import difflib
import json
import os
import re
import time
import urllib.parse
import urllib.request

PD = os.environ.get("PERSONAL_DATA_DIR",
                    "/home/cc/Acai-Knowledge/workspace/personal-investment-data")
LEDGER = os.path.join(PD, "experiments", "ledger")


def http_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))


def clean(name):
    return re.sub(r"[\s|·•]", "", name or "").replace("（", "(").replace("）", ")")


def main():
    trades = json.load(open(os.path.join(LEDGER, "trades.json"), encoding="utf-8"))
    names = {}
    for t in trades:
        nm = t.get("name_raw") or t.get("fund_name")
        if nm:
            names.setdefault(clean(nm), nm)
    print("distinct names:", len(names))

    resolution = {}
    for cname, raw in names.items():
        key = urllib.parse.quote(raw)
        try:
            data = http_json(
                f"https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key={key}")
            cands = (data.get("Datas") or [])
            best, best_score = None, 0.0
            for c in cands[:8]:
                nm = c.get("NAME") or ""
                s = difflib.SequenceMatcher(None, cname, clean(nm)).ratio()
                if s > best_score:
                    best, best_score = c, s
            if best and best_score >= 0.5:
                resolution[cname] = {"code": best.get("CODE"), "name": best.get("NAME"),
                                     "score": round(best_score, 2)}
            else:
                resolution[cname] = {"code": None, "name": None, "score": round(best_score, 2)}
        except Exception as e:
            resolution[cname] = {"code": None, "name": None, "error": str(e)}
        time.sleep(0.2)

    resolved = {k: v for k, v in resolution.items() if v.get("code")}
    print("resolved:", len(resolved), "/", len(resolution))
    for k, v in list(resolution.items()):
        if not v.get("code"):
            print("  UNRESOLVED:", k)

    navs = {}
    for k, v in resolved.items():
        code = v["code"]
        try:
            js = urllib.request.urlopen(urllib.request.Request(
                f"https://fund.eastmoney.com/pingzhongdata/{code}.js",
                headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8")
            m = re.search(r"var Data_netWorthTrend\s*=\s*(\[.*?\]);", js)
            if not m:
                continue
            rows = []
            for it in json.loads(m.group(1)):
                d = time.strftime("%Y-%m-%d", time.gmtime(it["x"] / 1000))
                if d >= "2026-03-01":
                    rows.append({"d": d, "nav": it["y"], "chg": it.get("equityReturn")})
            navs[code] = rows
        except Exception as e:
            navs[code] = []
        time.sleep(0.15)

    json.dump(resolution, open(os.path.join(LEDGER, "fund_resolution.json"), "w"),
              ensure_ascii=False, indent=1)
    json.dump(navs, open(os.path.join(LEDGER, "fund_navs_ledger.json"), "w"),
              ensure_ascii=False, indent=1)
    print("nav series saved:", sum(1 for v in navs.values() if v), "/", len(navs))


if __name__ == "__main__":
    main()
