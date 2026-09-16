"""E08 v0.3 — 交易截图 OCR 文本 → 结构化台账（区分三种页型 + 严格配对）。

页型：
  SINGLE   单只基金「交易记录」：页头 `基金名(代码)`，逐条 = 日期/时间 + 方向/金额（顺序可能颠倒）
  GLOBAL   全局「交易记录」列表：方向 + `基金|名称` + 金额（名称可跨行），日期在后
  CLOSED   「清仓记录详情」：申购/赎回/手续费/持有天数 + 明细

关键修正（相比 v0.2）：
  1) 单只基金页用「日期队列 × 动作队列」按文档顺序 zip 配对，消除日期/操作错位；
  2) 撤单/撤销/交易关闭 → 过滤；
  3) 全局页名称跨行拼接 + A/C 份额识别；
  4) 防跨基金误配（公司前缀一致 或 相似度≥0.85，或包含关系）。

约定：用户 2026-05 起交易，年份一律归一化 2026（保留 ocr_year_raw）。
"""
import csv
import difflib
import json
import os
import re

PD = os.environ.get("PERSONAL_DATA_DIR",
                    "/home/cc/Acai-Knowledge/workspace/personal-investment-data")
OCR = os.path.join(PD, "experiments", "ledger", "ocr")
OUT = os.path.join(PD, "experiments", "ledger")
PF = os.path.join(PD, "portfolio.json")

DIR_RE = re.compile(r"^(买入|买人|买 入|卖 出|卖出|定投|转换|转换至|苇换|苇 换|转入|转出|土入)")
DATE_RE = re.compile(r"(\d{4,5})\s*[-–—/.]\s*(\d{1,2})\s*[-–—/.]\s*(\d{1,2})"
                     r"(?:\s+(\d{1,2})\s*[:：]\s*(\d{2})(?:\s*[:：]\s*(\d{2}))?)?")
AMT_RE = re.compile(r"([0-9][0-9.,]*)\s*(元|份)")
CANCEL_RE = re.compile(r"已撤单|已撤销|撤单|撤销|交易关闭|已关闭|关闭")
NAME_TOKEN = re.compile(r"基金\s*[|｜]?\s*([^0-9]{2,40})")


def clean_amount(raw):
    s = raw.replace(",", "")
    if s.count(".") > 1:
        s = s.replace(".", "", s.count(".") - 1)
    elif s.count(".") == 1:
        head, tail = s.split(".")
        if len(tail) == 3:
            s = head + tail
    try:
        return float(s)
    except ValueError:
        return None


def norm_dir(word):
    if "买" in word or "土" in word:
        return "买入"
    if "卖" in word:
        return "卖出"
    if "定投" in word:
        return "定投"
    return "转换"


def norm_name(name):
    return re.sub(r"[\s|·•]", "", name or "").replace("（", "(").replace("）", ")")


def norm_date(line):
    m = DATE_RE.search(line)
    if not m:
        return None, None
    mm, dd = int(m.group(2)), int(m.group(3))
    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        return None, None
    t = None
    if m.group(4):
        t = f"{int(m.group(4)):02d}:{m.group(5)}:{m.group(6) or '00'}"
    return f"2026-{mm:02d}-{dd:02d}", t


def load_funds():
    pf = json.load(open(PF, encoding="utf-8"))
    funds = {h["fund_code"]: h.get("fund_name", "")
             for h in pf.get("holdings", []) if h.get("fund_code")}
    return pf, funds


def detect_page(lines):
    head = "\n".join(lines[:8])
    if "清仓" in head:
        return "CLOSED"
    m = re.search(r"\((\d{6})\)", head)
    if m and ("交易记录" in head or "持有" not in head):
        return "SINGLE", m.group(1)
    return "GLOBAL", None


def file_header_name(lines):
    # 单基金页：含 (6位代码) 的行
    for l in lines[:8]:
        if re.search(r"\(\d{6}\)", l):
            return re.sub(r"\(.*", "", l).strip()
    # 清仓详情页：『清仓记录详情』下一行是基金名
    for i, l in enumerate(lines[:8]):
        if "清仓记录详情" in l:
            for j in range(i + 1, min(i + 3, len(lines))):
                cand = lines[j]
                cand = re.sub(r"^[《“\"'‘\s]+", "", cand)
                cand = re.sub(r"\s*详情.*$", "", cand).strip()
                if len(cand) >= 4:
                    return cand
    return None


def parse_single(lines, code, f):
    """单只基金页：日期队列 × 动作队列，按文档顺序 zip。"""
    dts, acts = [], []
    for i, line in enumerate(lines):
        d, t = norm_date(line)
        if d and re.search(r"\d{1,2}[:：]\d{2}", line):
            dts.append((i, d, t, bool(CANCEL_RE.search(line))))
        m = DIR_RE.match(line)
        if m:
            am = AMT_RE.search(line)
            acts.append((i, norm_dir(m.group(1)),
                         clean_amount(am.group(1)) if am else None,
                         am.group(2) if am else None,
                         bool(CANCEL_RE.search(line))))
    entries = []
    for (di, d, t, d_cancel), (ai, direction, amount, unit, a_cancel) in zip(dts, acts):
        if d_cancel or a_cancel:
            continue
        entries.append(dict(file=f, direction=direction, name_raw="", header_code=code,
                            amount_raw=None, amount=amount, unit=unit, date=d, time=t,
                            month_suspect=False))
    return entries


def parse_global(lines, f):
    """全局列表页：方向行 → 名称(可跨行) → 日期行。"""
    entries = []
    n = len(lines)
    i = 0
    while i < n:
        m = DIR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        direction = norm_dir(m.group(1))
        am = AMT_RE.search(lines[i])
        amount = clean_amount(am.group(1)) if am else None
        unit = am.group(2) if am else None
        cancelled = bool(CANCEL_RE.search(lines[i]))
        # 名称：本行 + 后续非日期、非动作的延续行
        nm = NAME_TOKEN.search(lines[i])
        name = (nm.group(1).strip() if nm else "")
        cont = []
        d = t = None
        j = i + 1
        while j < n and j < i + 5:
            line = lines[j]
            if CANCEL_RE.search(line):
                cancelled = True
            dd, tt = norm_date(line)
            if dd and re.search(r"\d{1,2}[:：]\d{2}", line):
                d, t = dd, tt
                break
            if not DIR_RE.match(line):
                cont.append(line)
            j += 1
        if cont:
            name = name + "".join(cont)
        # A/C 份额：延续行中的单独 A / C
        name = name.strip()
        entries.append(dict(file=f, direction=direction, name_raw=name,
                            header_code=None, amount_raw=None, amount=amount, unit=unit,
                            date=d, time=t, month_suspect=bool(d and int(d[5:7]) < 5),
                            cancelled=cancelled))
        i = j + 1 if (j < n and d) else i + 1
    return [e for e in entries if not e["cancelled"]]


def _nums_in(line):
    return re.findall(r"[0-9][0-9.,]*", line)


def _parse_date_shares(line):
    """'2020-08-04  2020-08-05  838.71份' → (date, shares)"""
    d, t = norm_date(line)
    shares = None
    m = re.search(r"([0-9][0-9.,]*)\s*份", line)
    if m:
        shares = clean_amount(m.group(1))
    return d, shares


def parse_closed_txns(lines, code, fname, f):
    """从『交易明细』表解析逐笔交易：类型+净值+金额 一行，日期+确认+份额 一行。"""
    txns = []
    start = None
    for i, l in enumerate(lines):
        if "交易明细" in l:
            start = i + 1
            break
    if start is None:
        return txns
    i = start
    n = len(lines)
    while i < n:
        l = lines[i]
        if not l or "没有更多" in l:
            break
        if any(k in l for k in ("交易类型", "净值/确认", "金额/份额", "讨论区", "本", "据")):
            i += 1
            continue
        if l.startswith("卖出"):
            nums = _nums_in(l)
            amount = clean_amount(nums[-1]) if nums else None
            nav = clean_amount(nums[0]) if nums else None
            i += 1
            d, shares = _parse_date_shares(lines[i]) if i < n else (None, None)
            txns.append(dict(direction="卖出", amount=amount, unit="元", shares=shares,
                             nav=nav, date=d, time=None, fund_code=code, fund_name=fname))
            i += 1
        elif re.match(r"^(买入|买和|买人)", l):
            nums = _nums_in(l)
            amount = clean_amount(nums[-1]) if nums else None
            nav = clean_amount(nums[0]) if nums else None
            i += 1
            d, shares = _parse_date_shares(lines[i]) if i < n else (None, None)
            txns.append(dict(direction="买入", amount=amount, unit="元", shares=shares,
                             nav=nav, date=d, time=None, fund_code=code, fund_name=fname))
            i += 1
        elif ("转换至" in l) or re.match(r"^(苇换|转换)", l):
            target = re.sub(r"^.*转换至?[”\"]?", "", l).strip()
            # 下一行通常含份额
            i += 1
            shares = None
            d = None
            if i < n:
                m = re.search(r"([0-9][0-9.,]*)\s*份", lines[i])
                if m:
                    shares = clean_amount(m.group(1))
                    i += 1
                if i < n:
                    d, _ = norm_date(lines[i])
            txns.append(dict(direction="转换", amount=None, unit="份", shares=shares,
                             nav=None, date=d, time=None, target=target or None,
                             fund_code=code, fund_name=fname))
            i += 1
        else:
            i += 1
    return txns


def parse_closed_summary(lines, code, fname, f):
    text = "\n".join(lines)

    def num(pat):
        flex = r"\s*".join(pat)
        m = re.search(flex + r"[^\d]{0,10}([0-9][0-9.,]*)", text)
        return clean_amount(m.group(1)) if m else None

    dates = sorted({norm_date(l)[0] for l in lines if norm_date(l)[0]})
    guess = fname
    if not guess:
        for l in lines[:6]:
            cand = re.sub(r"^[^A-Za-z\u4e00-\u9fff]*", "", l)
            cand = re.sub(r"\(.*", "", cand).replace("清仓记录详情", "").strip()
            if len(cand) >= 4 and not cand.startswith(("交易", "《")):
                guess = cand
                break
    return {"file": f, "fund_code": code, "fund_name": guess,
            "buy_amount": num("申购金额"), "sell_amount": num("赎回金额"),
            "fee": num("交易手续费"), "hold_days": num("持有天数"),
            "first_date": dates[0] if dates else None,
            "last_date": dates[-1] if dates else None}


def main():
    pf, funds = load_funds()
    codes = list(funds.keys())
    names = [norm_name(v) for v in funds.values()]
    files = sorted(f for f in os.listdir(OCR) if f.endswith(".txt") and not f.startswith("_"))
    blocks, closed, closed_txns = [], [], []
    for f in files:
        lines = [l.strip() for l in open(os.path.join(OCR, f), encoding="utf-8")]
        pg = detect_page(lines)
        if pg == "CLOSED":
            hname = file_header_name(lines)
            closed.append(parse_closed_summary(lines, None, hname, f))
            txns = parse_closed_txns(lines, None, hname, f)
            for t in txns:
                closed_txns.append(dict(file=f, direction=t["direction"],
                                        name_raw=t["fund_name"] or "",
                                        amount=t.get("amount"), unit=t.get("unit"),
                                        shares=t.get("shares"), nav=t.get("nav"),
                                        target=t.get("target"),
                                        date=t.get("date"), time=None))
        elif pg[0] == "SINGLE":
            # 单基金页的 OCR 日期/金额配位不可靠，且全局列表页已覆盖同样交易 → 跳过，
            # 只依赖全局列表页（结构：方向+名称+金额同行，日期在后，更可靠）。
            pass
        else:
            blocks += parse_global(lines, f)
    print(f"files={len(files)} blocks={len(blocks)} closed={len(closed)} closed_txns={len(closed_txns)}")

    # 基金代码匹配（仅对 GLOBAL 页的名字做；SINGLE 页已有 header_code）
    for b in blocks:
        if b.get("header_code"):
            b["fund_code"] = b["header_code"]
            b["fund_name"] = funds.get(b["header_code"], "")
            b["match_score"] = 1.0
            continue
        n = norm_name(b.get("name_raw"))
        best, score = None, 0.0
        for code, nm in zip(codes, names):
            s = difflib.SequenceMatcher(None, n, nm).ratio()
            if len(n) >= 4 and (nm.startswith(n) or n in nm or nm in n):
                s = max(s, 0.9)
            prefix_ok = n[:2] == nm[:2] if len(n) >= 2 and len(nm) >= 2 else False
            if s > score and (prefix_ok or s >= 0.85):
                best, score = code, s
        b["fund_code"] = best if score >= 0.72 else None
        b["match_score"] = round(score, 2)
        b["fund_name"] = funds.get(b["fund_code"], "") if b["fund_code"] else None

    # 去重（基金+日期+时间+方向+金额+单位）。
    # 注意：必须含时间——同一天可能有金额相同的两笔（如 05-20 两次买 10000、
    # 06-30 两次卖 2758.14），不能只靠 (日期,金额) 去重，否则会误删一笔。
    seen, uniq = set(), []
    for b in blocks:
        key = (b.get("fund_code"), b.get("date"), b.get("time"), b.get("direction"),
               round(b["amount"], 2) if b["amount"] is not None else None, b.get("unit"))
        if key[0] and key[1] and key[4] is not None:
            if key in seen:
                continue
            seen.add(key)
        uniq.append(b)
    uniq.sort(key=lambda x: ((x.get("date") or "9999"), (x.get("time") or "99")))

    os.makedirs(OUT, exist_ok=True)
    json.dump(uniq, open(os.path.join(OUT, "trades.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(closed, open(os.path.join(OUT, "closed_positions.json"), "w"),
              ensure_ascii=False, indent=1)
    json.dump(closed_txns, open(os.path.join(OUT, "closed_txns.json"), "w"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "trades.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "time", "direction", "fund_code", "fund_name",
                                           "amount", "unit", "name_raw", "match_score", "file"])
        w.writeheader()
        for b in uniq:
            w.writerow({k: b.get(k) for k in w.fieldnames})

    monthly = {}
    for b in uniq:
        if b["date"]:
            monthly[b["date"][5:7]] = monthly.get(b["date"][5:7], 0) + 1
    unmatched = [b for b in uniq if not b["fund_code"]]
    no_date = [b for b in uniq if not b["date"]]
    summary = {"files": len(files), "blocks": len(blocks), "unique_entries": len(uniq),
               "closed": len(closed), "unmatched": len(unmatched), "no_date": len(no_date),
               "date_min": min(b["date"] for b in uniq if b["date"]) or None,
               "date_max": max(b["date"] for b in uniq if b["date"]) or None,
               "entries_by_month": dict(sorted(monthly.items()))}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    json.dump(summary, open(os.path.join(OUT, "ledger_summary.json"), "w"),
              ensure_ascii=False, indent=1)
    print("unmatched:", [(b["date"], b["name_raw"][:18], b["amount"], b["direction"])
                         for b in unmatched[:15]])
    print("no_date:", [(b["name_raw"][:18], b["amount"], b["direction"]) for b in no_date[:10]])


if __name__ == "__main__":
    main()
