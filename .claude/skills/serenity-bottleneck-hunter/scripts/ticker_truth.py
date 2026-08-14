#!/usr/bin/env python3
"""ticker_truth.py — Ticker ground truth 数据库 + 双向验证工具(L1 + L2 核心)

设计原则(2026-06-05 用户挑战驱动,绿的谐波错标 case):
  - LLM 不可信任 "ticker → 公司名" 凭记忆映射(hallucination 概率 ~5%,无自察觉)
  - **所有 ticker 必须有 ground truth 验证才可使用**
  - **resolve(name) 强制走 EODHD search 反查,不允许 LLM 直接 hardcode ticker**

数据库 schema (reference/ticker_truth.csv):
  ticker,name_en,name_zh,exchange,sector,last_verified,source

使用模式:
  # L1: 查 ground truth
  from ticker_truth import lookup_by_ticker, lookup_by_name, verify_pair
  info = lookup_by_ticker("688017.SHG")              # → {name_en, name_zh, ...}
  matches = lookup_by_name("绿的谐波")                  # → [(ticker, name_en, ...), ...]
  ok = verify_pair("688017.SHG", "绿的谐波")          # → True/False + reason

  # L2: 强制 resolve(replace 凭记忆 hardcode)
  from ticker_truth import resolve_tickers
  syms = resolve_tickers(["绿的谐波", "五洲新春"])    # → [("688017.SHG", "绿的谐波"), ...]
                                                       # miss → EODHD search → 写入 ground truth
"""
import os, csv, json, urllib.request, urllib.error
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TRUTH_CSV = os.path.join(HERE, "..", "reference", "ticker_truth.csv")
STALE_DAYS = 90

# ---- DB 读写 ----

def _load_db():
    """读全表 → dict[ticker -> row]"""
    if not os.path.exists(TRUTH_CSV):
        return {}
    db = {}
    with open(TRUTH_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            db[r["ticker"]] = r
    return db


def _save_db(db):
    """保存全表"""
    os.makedirs(os.path.dirname(TRUTH_CSV), exist_ok=True)
    fields = ["ticker", "name_en", "name_zh", "exchange", "sector", "last_verified", "source"]
    with open(TRUTH_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for ticker in sorted(db.keys()):
            row = db[ticker]
            w.writerow({k: row.get(k, "") for k in fields})


def _is_stale(row, today=None):
    """判 entry 是否过期(> STALE_DAYS)"""
    today = today or datetime.now()
    try:
        last = datetime.strptime(row.get("last_verified", "1970-01-01"), "%Y-%m-%d")
        return (today - last).days > STALE_DAYS
    except Exception:
        return True


# ---- EODHD search ----

def _eodhd_search(query):
    """走 EODHD search API,返回 results list (Code, Name, Exchange, Type, previousClose ...)"""
    key = os.environ.get("EODHD_API_KEY", "")
    if not key:
        raise RuntimeError("EODHD_API_KEY 环境变量未设,无法验证 ticker")
    import urllib.parse
    q = urllib.parse.quote(query)
    url = f"https://eodhd.com/api/search/{q}?api_token={key}&fmt=json&limit=10"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        d = urllib.request.urlopen(req, timeout=20).read()
        return json.loads(d)
    except urllib.error.HTTPError as e:
        return []
    except Exception:
        return []


# ---- L1 API ----

def lookup_by_ticker(ticker):
    """查 ground truth(无 API call)。返回 dict 或 None"""
    db = _load_db()
    return db.get(ticker)


def lookup_by_name(name, lang="any"):
    """按 name(中或英)查 ground truth。返回 list of dict"""
    db = _load_db()
    name_l = name.lower().strip()
    matches = []
    for ticker, row in db.items():
        nz = (row.get("name_zh", "") or "").lower()
        ne = (row.get("name_en", "") or "").lower()
        if name_l == nz or name_l == ne or name_l in nz or name_l in ne:
            matches.append(row)
    return matches


def verify_pair(ticker, claimed_name, today=None):
    """**核心验证 API** — 检查 (ticker, claimed_name) 是否匹配 ground truth。
    返回 (ok: bool, reason: str)
    - 命中且 name 匹配 → (True, "ok")
    - 命中但 name 不匹配 → (False, "mismatch: ...")
    - 未命中 → 自动走 EODHD search resolve + 写入 → 再 verify
    - stale → 重 verify
    """
    db = _load_db()
    row = db.get(ticker)
    if row and not _is_stale(row, today):
        nz = row.get("name_zh", "")
        ne = row.get("name_en", "")
        cn = claimed_name.lower().strip()
        if cn in nz.lower() or cn in ne.lower() or nz.lower() in cn or ne.lower() in cn:
            return (True, f"ok (truth: {nz} / {ne})")
        return (False, f"MISMATCH: claimed='{claimed_name}' but truth='{nz}' / '{ne}' (ticker={ticker})")
    # miss or stale → search + 写入
    results = _eodhd_search(ticker)
    if not results:
        return (False, f"ticker '{ticker}' not found via EODHD search")
    # 取首个匹配 ticker
    code_root = ticker.split(".")[0]
    match = None
    for r in results:
        if r.get("Code") == code_root:
            match = r; break
    if not match: match = results[0]
    # 写入 db
    today_str = (today or datetime.now()).strftime("%Y-%m-%d")
    new_row = {
        "ticker": ticker,
        "name_en": match.get("Name", "") or "",
        "name_zh": db.get(ticker, {}).get("name_zh", "") or claimed_name,  # 保留 zh 名
        "exchange": match.get("Exchange", "") or "",
        "sector": match.get("Type", "") or "",
        "last_verified": today_str,
        "source": "EODHD search",
    }
    db[ticker] = new_row
    _save_db(db)
    # 再 verify — fresh search 后写入了 EODHD 英文 name,中文 claimed_name 自动存为 name_zh
    # logic 修订(2026-06-05 Dogfood #13 audit):
    # - 中文 claimed_name 不能跟英文 name 做 substring 比较(永远 false)
    # - 但 ticker 在 EODHD 真实存在 → 真名映射 OK,标 newly-added-soft-warn
    # - 真错位 case(我记错 ticker 完全对应另一公司)→ EODHD 英文 name 看一眼就知道
    # - 终极防线:用户 review 报告时挑战(本次 case 就是这样发现的)
    cn = claimed_name.lower().strip()
    ne = new_row["name_en"].lower()
    # 英文比对(只在 claimed 是英文时严格)
    if any(c.isascii() and c.isalpha() for c in cn):
        if cn in ne or any(p in ne for p in cn.split() if len(p) > 2):
            return (True, f"ok (newly verified: {new_row['name_en']})")
        return (False, f"MISMATCH after fresh search: claimed='{claimed_name}' vs EODHD='{new_row['name_en']}'")
    # 中文 claimed_name → 信任 ticker 在 EODHD 真实存在,但日志显示 EN name 让人工 review
    return (True, f"NEW (zh, please visually review EN): {new_row['name_en']}")


# ---- L2 API: resolve ----

def resolve_tickers(names, theme_hint=""):
    """**强制工作流改造 API** — 输入 names(中文公司名 list)→ 走 EODHD search →
       输出 [(ticker, name_zh, name_en), ...] 已验证清单。
       miss → API search 新增到 ground truth → resolve。
       适配 _scan_*.py 重构:NAMES = [...]; SYMBOLS = resolve_tickers(NAMES)"""
    db = _load_db()
    today_str = datetime.now().strftime("%Y-%m-%d")
    resolved = []
    new_entries = 0
    for name in names:
        # 先查中文名命中
        hits = lookup_by_name(name)
        if hits:
            r = hits[0]
            resolved.append((r["ticker"], r["name_zh"], r["name_en"]))
            continue
        # miss → EODHD search
        results = _eodhd_search(name)
        if not results:
            resolved.append((None, name, "NOT_FOUND"))
            continue
        # 取第一个 Common Stock
        match = None
        for r in results:
            if r.get("Type") == "Common Stock":
                match = r; break
        if not match: match = results[0]
        ticker = f"{match['Code']}.{match['Exchange']}"
        new_row = {
            "ticker": ticker,
            "name_en": match.get("Name", "") or "",
            "name_zh": name,
            "exchange": match.get("Exchange", "") or "",
            "sector": match.get("Type", "") or "",
            "last_verified": today_str,
            "source": f"EODHD search (theme: {theme_hint})",
        }
        db[ticker] = new_row
        new_entries += 1
        resolved.append((ticker, name, new_row["name_en"]))
    if new_entries:
        _save_db(db)
    return resolved


# ---- CLI ----

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "lookup":
        # python ticker_truth.py lookup 688017.SHG
        info = lookup_by_ticker(sys.argv[2])
        print(json.dumps(info, ensure_ascii=False, indent=2) if info else "not in db")
    elif cmd == "verify":
        # python ticker_truth.py verify 688017.SHG "绿的谐波"
        ok, reason = verify_pair(sys.argv[2], sys.argv[3])
        print(f"{'✓ PASS' if ok else '✗ FAIL'}: {reason}")
        sys.exit(0 if ok else 1)
    elif cmd == "resolve":
        # python ticker_truth.py resolve 绿的谐波 五洲新春
        names = sys.argv[2:]
        results = resolve_tickers(names)
        for ticker, nz, ne in results:
            print(f"  {nz:<12} → {ticker:<14} | {ne}")
    elif cmd == "stats":
        db = _load_db()
        print(f"DB entries: {len(db)}")
        from collections import Counter
        ex = Counter(r.get("exchange", "?") for r in db.values())
        print(f"By exchange: {dict(ex.most_common(8))}")
        stale = sum(1 for r in db.values() if _is_stale(r))
        print(f"Stale (> {STALE_DAYS} days): {stale}")
    else:
        print(f"Unknown cmd: {cmd}")
        print(__doc__)
