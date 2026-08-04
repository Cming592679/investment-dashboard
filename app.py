"""Investment Dashboard — 基金监控仪表盘（多基金版 + 缓存 + 历史快照 + 数据健康检测）"""

import json
import os
import re
import threading
import time as _time
from datetime import datetime, date, timedelta
from flask import Flask, render_template, jsonify, request
from config import (
    FUNDS, EXIT_LEVELS,
    LEADING_INDICATORS, KEY_DATES, CYCLE_ASSESSMENTS,
    BOTTLENECK_CLUSTERS, BOTTLENECK_CONCENTRATION_WARN,
    SHARED_INDICATORS, BOTTLENECK_DISRUPTION,
    CYCLE_COUNTER_HYPOTHESIS, DIVERGENCE_DOWNGRADE_WEEKS,
    DYNAMIC_THRESHOLD_COEFFICIENT, DYNAMIC_THRESHOLD_LOOKBACK_DAYS,
    MIN_SAMPLE_SIZE_WARNING, CONTROL_BENCHMARKS,
)
from data_fetcher import get_index_snapshot, get_stock_snapshot
from trading_rules import evaluate_daily_actions

# ══════════════════════════════════════════════════════════
# 数据健康检测 — 指标过期 & 缺失事件
# ══════════════════════════════════════════════════════════

# 已知公司财报日历（用于检测 KEY_DATES 中遗漏的事件）
# aliases 用于中英文名称匹配
CORPORATE_CALENDAR = {
    "TSMC": {
        "ticker": "TSM",
        "aliases": ["台积电", "tsmc", "TSMC"],
        "events": [
            {"date": date(2026, 7, 16), "event": "Q2 法说会", "importance": "critical"},
            {"date": date(2026, 10, 15), "event": "Q3 法说会", "importance": "critical"},
        ],
        "affected_funds": ["019633", "014194", "024239", "CPO"],
    },
    "NVDA": {
        "ticker": "NVDA",
        "aliases": ["英伟达", "nvidia", "NVDA"],
        "events": [
            {"date": date(2026, 8, 20), "event": "Q2 财报", "importance": "critical"},
        ],
        "affected_funds": ["024239", "CPO", "021528"],
    },
    "ASML": {
        "ticker": "ASML",
        "aliases": ["阿斯麦", "asml", "ASML"],
        "events": [
            {"date": date(2026, 7, 17), "event": "Q2 财报", "importance": "critical"},
        ],
        "affected_funds": ["019633", "014194", "024239"],
    },
    "SK海力士": {
        "ticker": "000660.KS",
        "aliases": ["SK海力士", "SK 海力士", "海力士", "sk hynix"],
        "events": [
            {"date": date(2026, 7, 25), "event": "Q2 财报(HBM)", "importance": "critical"},
        ],
        "affected_funds": ["024239", "019633"],
    },
    "三星": {
        "ticker": "005930.KS",
        "aliases": ["三星", "samsung"],
        "events": [
            {"date": date(2026, 7, 30), "event": "Q2 财报", "importance": "high"},
        ],
        "affected_funds": ["024239"],
    },
    "美光": {
        "ticker": "MU",
        "aliases": ["美光", "micron"],
        "events": [
            {"date": date(2026, 9, 25), "event": "Q4 财报", "importance": "high"},
        ],
        "affected_funds": ["019633", "024239"],
    },
    "中芯国际": {
        "ticker": "688981.SS",
        "aliases": ["中芯国际", "中芯", "SMIC"],
        "events": [
            {"date": date(2026, 8, 15), "event": "Q2 财报", "importance": "critical"},
        ],
        "affected_funds": ["014194"],
    },
    "北方华创": {
        "ticker": "002371.SZ",
        "aliases": ["北方华创"],
        "events": [
            {"date": date(2026, 8, 25), "event": "Q2 财报", "importance": "critical"},
        ],
        "affected_funds": ["014194"],
    },
    "中际旭创": {
        "ticker": "300308.SZ",
        "aliases": ["中际旭创"],
        "events": [
            {"date": date(2026, 8, 24), "event": "半年报", "importance": "critical"},
        ],
        "affected_funds": ["CPO"],
    },
    "Rocket Lab": {
        "ticker": "RKLB",
        "aliases": ["rocket lab", "rocketlab"],
        "events": [
            {"date": date(2026, 8, 10), "event": "Q2 财报", "importance": "critical"},
        ],
        "affected_funds": ["015789"],
    },
}


def _parse_data_date(value):
    """从指标 value 字符串中提取数据对应的*发布日期*（而非数据所属期间）。
    月度数据通常次月发布，季度数据通常季末后2-4周发布。
    返回 date 对象或 None。"""
    today = date.today()

    def _valid_month(m_val):
        m_int = int(m_val)
        return m_int if 1 <= m_int <= 12 else None

    def _next_month(y, m):
        """返回下个月的 15 日（模拟月度数据发布时间）"""
        if m == 12:
            return date(y + 1, 1, 15)
        return date(y, m + 1, 15)

    def _quarter_end_publish(y, q):
        """季度数据：季末 + 1 个月为发布日期"""
        end_month = q * 3
        if end_month == 12:
            return date(y + 1, 1, 15)
        return date(y, end_month + 1, 15)

    # "2026年5月" — 月度数据，次月发布 → 用下月 15 日
    m = re.search(r'(\d{4})年(\d{1,2})月', value)
    if m:
        month = _valid_month(m.group(2))
        if month:
            return _next_month(int(m.group(1)), month)
    m = re.search(r'(\d{4})Q([1-4])', value)
    if m:
        return _quarter_end_publish(int(m.group(1)), int(m.group(2)))
    # "5月"（假设当年，前置必须是非数字或行首）
    m = re.search(r'(?:^|[^0-9])(\d{1,2})月', value)
    if m:
        month = _valid_month(m.group(1))
        if month:
            return _next_month(today.year, month)
    # "Q1" / "Q2"（假设当年）— 季度 → 季末+1月
    m = re.search(r'(?:^|[^0-9])Q([1-4])(?:\s|$|,|→)', value)
    if m:
        return _quarter_end_publish(today.year, int(m.group(1)))
    # "H1" → 7月, "H2" → 次年1月
    m = re.search(r'H([12])', value)
    if m:
        return date(today.year, 7 if m.group(1) == '1' else 12, 15)
    return None


def _get_max_age_days(update_cycle):
    """根据 update_cycle 描述确定最长可接受的更新间隔（天）"""
    if not update_cycle:
        return None
    if '日度' in update_cycle:
        return 2
    if '月度' in update_cycle or '每月' in update_cycle:
        return 35
    if '季度' in update_cycle or '季末' in update_cycle or '季报' in update_cycle:
        return 110
    if '年度' in update_cycle or '年初' in update_cycle:
        return 370
    return None  # 事件驱动型，无法自动判断


def check_indicator_staleness(fund_id=None):
    """检查领先指标是否过期。返回过期指标列表。"""
    today = date.today()
    stale_list = []

    funds_to_check = {fund_id: FUNDS[fund_id]} if fund_id else FUNDS
    for fid in funds_to_check:
        indicators = LEADING_INDICATORS.get(fid, {})
        for name, info in indicators.items():
            # 优先使用显式 last_updated
            last_updated_str = info.get("last_updated", "")
            if last_updated_str:
                try:
                    data_date = date.fromisoformat(last_updated_str)
                except ValueError:
                    data_date = _parse_data_date(info.get("value", ""))
            else:
                data_date = _parse_data_date(info.get("value", ""))

            if data_date is None:
                continue

            max_age = _get_max_age_days(info.get("update_cycle", ""))
            if max_age is None:
                continue

            age = (today - data_date).days
            if age > max_age:
                stale_list.append({
                    "fund_id": fid,
                    "fund_short": FUNDS.get(fid, {}).get("short", fid),
                    "indicator": name,
                    "value_snippet": info.get("value", "")[:60],
                    "data_date": data_date.strftime("%Y-%m-%d"),
                    "age_days": age,
                    "max_age_days": max_age,
                    "update_cycle": info.get("update_cycle", ""),
                    "severity": "critical" if age > max_age * 2 else "warning",
                })

    return stale_list


def detect_missing_events():
    """交叉比对 CORPORATE_CALENDAR 和 KEY_DATES，发现遗漏的关键事件。"""
    today = date.today()
    future_cutoff = today + timedelta(days=60)  # 只看未来60天内的
    missing = []

    for company, cal in CORPORATE_CALENDAR.items():
        for event in cal["events"]:
            if event["date"] < today or event["date"] > future_cutoff:
                continue  # 已过期或太远
            # 构建匹配关键词列表：公司名 + ticker + 别名
            match_keywords = [company.lower(), cal["ticker"].lower()]
            match_keywords += [a.lower() for a in cal.get("aliases", [])]

            for fid in cal["affected_funds"]:
                fund_dates = KEY_DATES.get(fid, [])
                # 检查该事件是否已被追踪（关键词匹配 + 日期差 ≤3天）
                found = any(
                    any(kw in kd["event"].lower() for kw in match_keywords)
                    and abs((kd["date"] - event["date"]).days) <= 3
                    for kd in fund_dates
                )
                if not found:
                    fund_short = FUNDS.get(fid, {}).get("short", fid)
                    missing.append({
                        "company": company,
                        "ticker": cal["ticker"],
                        "fund_id": fid,
                        "fund_short": fund_short,
                        "event": f"{company} {event['event']}",
                        "date_str": event["date"].strftime("%Y-%m-%d"),
                        "importance": event["importance"],
                    })

    return missing


def check_recently_passed_events():
    """检查最近 14 天内已过期的关键事件。有 result 标记为已跟进，无则标记待分析。"""
    today = date.today()
    recently_passed = []

    for fid, events in KEY_DATES.items():
        for e in events:
            days_ago = (today - e["date"]).days
            if 0 <= days_ago <= 14:
                fund_short = FUNDS.get(fid, {}).get("short", fid)
                result = e.get("result", "")
                recently_passed.append({
                    "fund_id": fid,
                    "fund_short": fund_short,
                    "event": e["event"],
                    "date_str": e["date"].strftime("%Y-%m-%d"),
                    "days_ago": days_ago,
                    "importance": e.get("importance", "normal"),
                    "has_analysis": bool(result),
                    "result": result,
                })

    return recently_passed

app = Flask(__name__)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(PROJECT_DIR, "history")
REVIEWS_DIR = os.path.join(PROJECT_DIR, "reviews")
OPTIMIZE_TOPICS_PATH = os.path.join(PROJECT_DIR, "optimize", "topics.json")
HISTORY_INDEX_PATH = os.path.join(HISTORY_DIR, "_index.json")

# ══════════════════════════════════════════════════════════
# 缓存层
# ══════════════════════════════════════════════════════════

_cache = {}       # {fund_id: {"data": {...}, "fetched_at": datetime}}
_cache_lock = threading.Lock()
_fetching = False
_last_auto_refresh_date = None  # 记录上次自动刷新的日期


def _fetch_one_fund(fund_id, fund):
    """抓取单只基金的完整数据（纯函数，不含缓存逻辑）"""
    stocks = {}
    for ticker, name in fund["stocks"].items():
        s = get_stock_snapshot(ticker)
        s["name"] = name
        stocks[ticker] = s

    indices = {}
    for ticker, name in fund["indices"].items():
        s = get_index_snapshot(ticker)
        s["name"] = name
        indices[ticker] = s

    specials = {}
    for ticker, info in fund.get("specials", {}).items():
        s = get_stock_snapshot(ticker)
        s["name"] = info["name"]
        s["note"] = info.get("note", "")
        specials[ticker] = s

    assessment = compute_assessment(fund, stocks, indices, specials, fund_id)

    # 领先指标 & 关键事件 & 周期判断
    today = date.today()
    leading = LEADING_INDICATORS.get(fund_id, {})
    key_dates_raw = KEY_DATES.get(fund_id, [])
    key_dates = []
    for kd in key_dates_raw:
        days_left = (kd["date"] - today).days
        key_dates.append({
            **kd,
            "date_str": kd["date"].strftime("%Y-%m-%d"),
            "days_left": days_left,
            "passed": days_left < 0,
        })
    cycle = CYCLE_ASSESSMENTS.get(fund_id, {})

    # 生成预测
    prediction = _generate_prediction(fund_id, assessment, leading, cycle)

    # P1-任务5：反方假设
    counter = CYCLE_COUNTER_HYPOTHESIS.get(fund_id, "")
    if counter:
        cycle = dict(cycle) if cycle else {}
        cycle["counter_hypothesis"] = counter

    # P0-任务4：瓶颈破坏条件状态
    disruption_status = {}
    for tag, info in BOTTLENECK_DISRUPTION.items():
        if fund_id in info["affected_funds"]:
            for cond in info["conditions"]:
                if cond["status"] != "none":
                    disruption_status[tag] = {
                        "label": info["label"],
                        "condition": cond["desc"],
                        "status": cond["status"],
                        "note": cond.get("note", ""),
                    }

    # 拉基准 ETF 实际涨跌作为 fund_return_pct
    bm_ticker = fund.get("benchmark", "")
    fund_return_pct = None
    if bm_ticker:
        # 优先从已拉取的数据中找
        for src in [stocks, indices, specials]:
            if bm_ticker in src and not src[bm_ticker].get("error"):
                fund_return_pct = src[bm_ticker].get("day_change_pct")
                break
        # 没找到就单独拉
        if fund_return_pct is None:
            bm_snap = get_stock_snapshot(bm_ticker)
            if not bm_snap.get("error"):
                fund_return_pct = bm_snap.get("day_change_pct")

    return {
        "fund_id": fund_id,
        "name": fund["name"],
        "short": fund["short"],
        "market": fund["market"],
        "stocks": stocks,
        "indices": indices,
        "specials": specials,
        "assessment": assessment,
        "leading_indicators": leading,
        "key_dates": key_dates,
        "cycle_assessment": cycle,
        "prediction": prediction,
        "disruption_status": disruption_status,
        "fund_return_pct": fund_return_pct,
    }


def _refresh_all():
    """后台刷新全部基金缓存"""
    global _fetching, _last_auto_refresh_date
    with _cache_lock:
        _fetching = True

    try:
        now = datetime.now()
        for fid, fund in FUNDS.items():
            try:
                data = _fetch_one_fund(fid, fund)
                with _cache_lock:
                    _cache[fid] = {"data": data, "fetched_at": now}
            except Exception as e:
                print(f"  ⚠ 抓取 {fid} 失败: {e}")
        _last_auto_refresh_date = now.date()
        # 保存当日快照
        try:
            _save_daily_snapshot()
        except Exception as e:
            print(f"  ⚠ 快照保存失败: {e}")
    finally:
        with _cache_lock:
            _fetching = False


def _get_fund_response(fund_id, force_refresh=False):
    """获取基金数据：优先缓存，可选强制刷新"""
    fund = FUNDS.get(fund_id)
    if not fund:
        return None

    # 强制刷新：重新抓取这一只
    if force_refresh:
        data = _fetch_one_fund(fund_id, fund)
        now = datetime.now()
        with _cache_lock:
            _cache[fund_id] = {"data": data, "fetched_at": now}
        return _attach_meta(data, now, False)

    # 有缓存直接用
    with _cache_lock:
        entry = _cache.get(fund_id)
        is_fetching = _fetching

    if entry:
        return _attach_meta(entry["data"], entry["fetched_at"], is_fetching)

    # 无缓存 → 同步抓取（首次访问）
    data = _fetch_one_fund(fund_id, fund)
    now = datetime.now()
    with _cache_lock:
        _cache[fund_id] = {"data": data, "fetched_at": now}
    return _attach_meta(data, now, False)


def _save_daily_snapshot():
    """保存当日快照到 history/，同时更新 _index.json"""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    today_str = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    snapshot = {"date": today_str, "fetched_at": now_str, "funds": {}}
    with _cache_lock:
        for fid in FUNDS:
            entry = _cache.get(fid)
            if not entry:
                continue
            d = entry["data"]
            a = d["assessment"]
            # 精简存储：只保留关键判断字段
            stocks_brief = {}
            for tk, s in d.get("stocks", {}).items():
                stocks_brief[tk] = {
                    "name": s.get("name", ""),
                    "price": s.get("price"),
                    "chg_pct": s.get("day_change_pct"),
                    "rsi": s.get("rsi"),
                    "above_ma50": s.get("above_ma50"),
                }
            indices_brief = {}
            for tk, s in d.get("indices", {}).items():
                indices_brief[tk] = {
                    "name": s.get("name", ""),
                    "price": s.get("price"),
                    "chg_pct": s.get("day_change_pct"),
                    "above_ma50": s.get("above_ma50"),
                }
            # 用 _fetch_one_fund 预计算的 benchmark 涨跌
            fund_return = d.get("fund_return_pct")

            snapshot["funds"][fid] = {
                "name": d["name"],
                "score": a["score"],
                "conclusion": a["conclusion"],
                "emoji": a["emoji"],
                "details": a.get("details", []),
                "fund_return_pct": fund_return,
                "stocks": stocks_brief,
                "indices": indices_brief,
            }

    # 写入当日快照（含预测）
    preds = {}
    for fid in snapshot["funds"]:
        entry = _cache.get(fid)
        if entry and "prediction" in entry["data"]:
            preds[fid] = entry["data"]["prediction"]
    snapshot["predictions"] = preds

    snap_path = os.path.join(HISTORY_DIR, f"{today_str}.json")
    snapshot = _sanitize_json(snapshot)
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # 同时写一份纯预测记录到 predictions/（含双轨验证）
    preds_dir = os.path.join(PROJECT_DIR, "predictions")
    os.makedirs(preds_dir, exist_ok=True)
    pred_path = os.path.join(preds_dir, f"{today_str}.json")
    # Extract indicator predictions for the prediction file
    indicator_preds = {}
    for fid in preds:
        entry = _cache.get(fid)
        if entry and "prediction" in entry["data"]:
            ip = entry["data"]["prediction"].get("indicator_predictions", {})
            indicator_preds[fid] = {
                "price_prediction": {
                    "direction": entry["data"]["prediction"]["direction"],
                    "label": entry["data"]["prediction"]["label"],
                    "verify_date": entry["data"]["prediction"]["verify_date"],
                },
                "indicator_predictions": ip,
                "indicator_verify_date": entry["data"]["prediction"].get("indicator_verify_date", ""),
            }
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump({
            "date": today_str,
            "generated_at": now_str,
            "predictions": preds,
            "two_tier_predictions": indicator_preds,
        }, f, ensure_ascii=False, indent=2)

    # 更新 index
    index = []
    if os.path.exists(HISTORY_INDEX_PATH):
        try:
            with open(HISTORY_INDEX_PATH, "r", encoding="utf-8") as f:
                index = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            index = []

    # 去重：同一天覆盖
    index = [e for e in index if e.get("date") != today_str]
    index.append({
        "date": today_str,
        "fetched_at": now_str,
        "funds": {fid: {
            "score": snapshot["funds"][fid]["score"],
            "conclusion": snapshot["funds"][fid]["conclusion"],
            "return_pct": snapshot["funds"][fid].get("fund_return_pct"),
        } for fid in snapshot["funds"]}
    })
    with open(HISTORY_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"📸 快照已保存: {today_str} ({len(snapshot['funds'])} 只基金)")


def _sanitize_json(obj):
    """递归清理 NaN/Infinity 为 None，确保 JSON 合法"""
    import math
    if isinstance(obj, dict):
        return {k: _sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_json(v) for v in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def _attach_meta(data, fetched_at, is_fetching):
    """给响应附加时间元信息 + 指标健康状态"""
    fund_id = data.get("fund_id", "")
    # 仅检查当前基金的指标过期
    staleness = check_indicator_staleness(fund_id=fund_id) if fund_id else []
    result = {
        **data,
        "cached_at": fetched_at.strftime("%Y-%m-%d %H:%M:%S"),
        "fetching": is_fetching,
        "health": {
            "stale_indicators": staleness,
            "stale_count": len(staleness),
        },
    }
    # 递归清理 NaN → null，防止 JSON 解析失败
    return _sanitize_json(result)


# ══════════════════════════════════════════════════════════
# 后台定时刷新（每日 18:00）
# ══════════════════════════════════════════════════════════

def _scheduler_loop():
    """后台线程：每日 18:00 刷新快照"""
    global _last_auto_refresh_date
    while True:
        _time.sleep(30)
        now = datetime.now()
        today = now.date()

        # 每日 18:00-18:02 刷新
        if now.hour == 18 and now.minute <= 2:
            if _last_auto_refresh_date != today:
                print(f"⏰ 定时刷新触发 {now.strftime('%H:%M:%S')}")
                _refresh_all()


# ══════════════════════════════════════════════════════════
# 复盘辅助函数
# ══════════════════════════════════════════════════════════

def _check_tier1_gate():
    """Tier-1 门禁：检查指标层是否有 ≥1 季度的验证样本"""
    # 检查最早的预测是否已过 90 天
    preds_dir = os.path.join(PROJECT_DIR, "predictions")
    if not os.path.exists(preds_dir):
        return {"ready": False, "reason": "无预测记录", "warning": "尚未生成任何预测，无法进行 Tier-1 验证"}
    files = sorted([f for f in os.listdir(preds_dir) if f.endswith(".json")])
    if not files:
        return {"ready": False, "reason": "无预测文件", "warning": "预测目录为空"}
    earliest = files[0].replace(".json", "")
    try:
        earliest_date = date.fromisoformat(earliest)
        days_elapsed = (date.today() - earliest_date).days
    except ValueError:
        return {"ready": False, "reason": "日期解析失败", "warning": "预测文件名格式异常"}
    if days_elapsed < 90:
        return {
            "ready": False,
            "reason": f"仅积累 {days_elapsed} 天（需 ≥90）",
            "warning": f"Tier-1 指标层验证样本不足（{days_elapsed}/90 天），当前所有权重调整均为「实验性/未经确认」，不可直接触发正式参数变更。仅 Tier-2 价格层可进入观察日志。"
        }
    return {"ready": True, "reason": f"已积累 {days_elapsed} 天", "warning": ""}


def _calc_dynamic_threshold(fid, index_data):
    """按板块动态计算 Tier-2 判定阈值：周涨跌标准差 × 0.5"""
    returns = []
    for entry in index_data:
        f = entry.get("funds", {}).get(fid, {})
        r = f.get("fund_return_pct")
        if r is not None:
            returns.append(r)
    if len(returns) < 5:
        return 1.0  # fallback to default 1%
    # 按周分组（每5个交易日一组），算周涨跌
    weekly = []
    for i in range(0, len(returns), 5):
        chunk = returns[i:i+5]
        if len(chunk) >= 3:  # 至少 3 个交易日才算有效周
            weekly.append(sum(chunk))
    if len(weekly) < 4:
        return 1.0
    import statistics
    std = statistics.stdev(weekly)
    threshold = round(std * DYNAMIC_THRESHOLD_COEFFICIENT, 2)
    return max(threshold, 0.3)  # 不低于 0.3%，避免阈值过小


def _count_oscillation_predictions(predictions_data):
    """统计震荡/flat 预测占比"""
    total = 0
    neutral = 0
    for entry in predictions_data:
        for fid, p in entry.get("predictions", {}).items():
            total += 1
            if p.get("direction", "") in ("flat", "flat-down"):
                neutral += 1
    return total, neutral


def _compute_confidence_calibration(predictions_data, index_data):
    """按置信度分桶计算原始准确率"""
    buckets = {"高": {"total": 0, "correct": 0}, "中": {"total": 0, "correct": 0}, "低": {"total": 0, "correct": 0}}
    for pred_entry in predictions_data:
        pred_date = pred_entry.get("date", "")
        for fid, p in pred_entry.get("predictions", {}).items():
            conf = p.get("confidence", "低")
            if conf not in buckets:
                conf = "低"
            buckets[conf]["total"] += 1
            direction = p.get("direction", "")
            verify_date = p.get("verify_date", "")
            # 查找验证日的实际收益
            actual = None
            for idx_entry in index_data:
                if idx_entry.get("date") == verify_date:
                    f = idx_entry.get("funds", {}).get(fid, {})
                    actual = f.get("fund_return_pct")
                    break
            if actual is None:
                continue
            # 判定
            threshold = 1.0  # 使用默认阈值（动态阈值需要额外计算）
            if direction == "up" and actual >= threshold:
                buckets[conf]["correct"] += 1
            elif direction == "up" and actual >= 0:
                buckets[conf]["correct"] += 0.5
            elif direction == "down" and actual <= -threshold:
                buckets[conf]["correct"] += 1
            elif direction == "down" and actual <= 0:
                buckets[conf]["correct"] += 0.5
            elif direction in ("flat", "flat-down") and abs(actual) <= threshold:
                buckets[conf]["correct"] += 1
    return buckets


def _tier2_verdict(direction, actual, threshold):
    """Tier-2 判定：方向 + 强度"""
    if direction == "up":
        if actual >= threshold:       return "✅"
        elif actual >= 0:             return "➡️"
        else:                          return "❌"
    elif direction == "down":
        if actual <= -threshold:      return "✅"
        elif actual <= 0:             return "➡️"
        else:                          return "❌"
    else:  # flat / flat-down — 跟 up/down 同样严格
        if abs(actual) <= threshold:  return "✅"
        elif abs(actual) <= threshold * 2: return "➡️"
        else:                          return "❌"
    # 注：flat 预测错误不再享受隐性减罚——超出阈值 2 倍直接 ❌


def _generate_monthly_review():
    today = date.today()
    month_str = today.strftime("%Y-%m")

    snapshots = []
    for i in range(31):
        d = today - timedelta(days=30 - i)
        snap_path = os.path.join(HISTORY_DIR, f"{d.strftime('%Y-%m-%d')}.json")
        if os.path.exists(snap_path):
            with open(snap_path, "r", encoding="utf-8") as f:
                snapshots.append(json.load(f))

    if not snapshots:
        print("  ⚠ 本月暂无快照，跳过复盘")
        return

    # 收集预测数据
    predictions_data = []
    preds_dir = os.path.join(PROJECT_DIR, "predictions")
    if os.path.exists(preds_dir):
        for fname in sorted(os.listdir(preds_dir)):
            if fname.endswith(".json") and not fname.startswith("_"):
                try:
                    with open(os.path.join(preds_dir, fname), "r", encoding="utf-8") as f:
                        predictions_data.append(json.load(f))
                except Exception:
                    pass

    # ── Tier-1 门禁 ──
    gate = _check_tier1_gate()

    # ── 统计 ──
    total_preds = sum(len(pe.get("predictions", {})) for pe in predictions_data)
    n = total_preds
    small_warn = f"\n> ⚠️ 样本量较小（n={n}），准确率数字仅供参考，暂不建议据此调整权重。\n" if 0 < n < MIN_SAMPLE_SIZE_WARNING else ""

    lines = [
        f"# 月度复盘 — {month_str}",
        f"\n生成时间: {today.strftime('%Y-%m-%d')}",
        f"\n快照天数: {len(snapshots)} | 有效预测: {n} 条",
    ]
    if not gate["ready"]:
        lines.append(f"\n> 🔒 **Tier-1 门禁未通过**: {gate['reason']}")
        lines.append(f"\n> ⚠️ {gate['warning']}")
    if small_warn:
        lines.append(small_warn)
    lines.append(f"\n---\n")

    # ═══ Tier-2 价格层 ═══
    lines.append(f"## Tier-2 价格层验证（30天窗口）")
    lines.append(f"\n> 仅作短期噪音监控，不作为方法论对错证据。")
    lines.append(f"\n| 板块 | 预测日 | 方向 | 置信度 | 验证日 | 实际 | 动态阈值 | 判定 |")
    lines.append(f"|------|--------|------|--------|--------|------|---------|------|")

    all_verdicts = []
    for pe in predictions_data:
        pred_date = pe.get("date", "")
        for fid, p in pe.get("predictions", {}).items():
            direction = p.get("direction", "")
            conf = p.get("confidence", "低")
            verify_date = p.get("verify_date", "")
            actual = None
            for snap in snapshots:
                if snap.get("date") == verify_date:
                    actual = snap.get("funds", {}).get(fid, {}).get("fund_return_pct")
                    break
            if actual is None:
                continue
            threshold = _calc_dynamic_threshold(fid, snapshots)
            verdict = _tier2_verdict(direction, actual, threshold)
            all_verdicts.append({"fid": fid, "conf": conf, "verdict": verdict, "direction": direction})
            name = FUNDS.get(fid, {}).get("short", fid)
            lines.append(f"| {name} | {pred_date} | {p.get('label','?')} | {conf} | {verify_date} | {actual:+.2f}% | ±{threshold}% | {verdict} |")

    vd = {"✅": sum(1 for v in all_verdicts if v["verdict"] == "✅"),
          "➡️": sum(1 for v in all_verdicts if v["verdict"] == "➡️"),
          "❌": sum(1 for v in all_verdicts if v["verdict"] == "❌")}
    lines.append(f"\n### Tier-2 汇总")
    lines.append(f"\n✅ {vd['✅']} / ➡️ {vd['➡️']} / ❌ {vd['❌']}（共 {len(all_verdicts)} 条）")

    # ── 震荡预测占比 ──
    osc_total, osc_neutral = _count_oscillation_predictions(predictions_data)
    if osc_total > 0:
        osc_ratio = osc_neutral / osc_total * 100
        drift_msg = f" ⚠️ 震荡/flat 预测占比偏高，系统可能在往保守方向漂移" if osc_ratio > 40 else ""
        lines.append(f"\n### 震荡预测占比监控")
        lines.append(f"\n震荡/flat 预测: {osc_neutral}/{osc_total}（{osc_ratio:.1f}%）{drift_msg}")

    # ═══ 对照组超额收益 ═══
    lines.append(f"\n---\n## 对照组：超额收益分析")
    lines.append(f"\n| 板块 | 板块累计 | 基准指数 | 超额收益 | 买入持有 |")
    lines.append(f"|------|---------|---------|---------|---------|")
    for fid in FUNDS:
        name = FUNDS[fid]["short"]
        fund_returns = [snap.get("funds", {}).get(fid, {}).get("fund_return_pct")
                        for snap in snapshots if snap.get("funds", {}).get(fid, {}).get("fund_return_pct") is not None]
        fund_cum = round(sum(fund_returns), 2) if fund_returns else None
        bm_ticker = CONTROL_BENCHMARKS.get(fid, "")
        bm_returns = []
        if bm_ticker:
            for snap in snapshots:
                fdata = snap.get("funds", {}).get(fid, {})
                for src_key in ["indices", "stocks"]:
                    if bm_ticker in fdata.get(src_key, {}):
                        val = fdata[src_key][bm_ticker].get("chg_pct")
                        if val is not None:
                            bm_returns.append(val)
                        break
        bm_cum = round(sum(bm_returns), 2) if bm_returns else None
        excess = round(fund_cum - bm_cum, 2) if (fund_cum is not None and bm_cum is not None) else None
        lines.append(f"| {name} | {fund_cum or '--'}% | {bm_cum or '--'}% | {excess or '--'}% | {fund_cum or '--'}% |")

    # ═══ 置信度校准 ═══
    lines.append(f"\n---\n## 置信度校准报告")
    lines.append(f"\n> 按置信度分桶展示「未加权」原始准确率，检验高置信度是否真的更准。")
    calib = _compute_confidence_calibration(predictions_data, snapshots)
    lines.append(f"\n| 置信度 | 预测数 | 正确/半对 | 原始准确率 |")
    lines.append(f"|--------|--------|----------|-----------|")
    for conf in ["高", "中", "低"]:
        b = calib[conf]
        if b["total"] > 0:
            lines.append(f"| {conf} | {b['total']} | {b['correct']:.1f} | {round(b['correct']/b['total']*100,1)}% |")
        else:
            lines.append(f"| {conf} | 0 | — | — |")

    # ═══ 各板块明细 ═══
    lines.append(f"\n---\n## 各板块评分走势")
    for fid, fund_info in FUNDS.items():
        lines.append(f"\n### {fund_info['short']} ({fid})")
        lines.append(f"\n| 日期 | 评分 | 结论 | 实际涨跌 |")
        lines.append(f"|------|-----|------|---------|")
        for snap in snapshots:
            fs = snap.get("funds", {}).get(fid)
            if fs:
                r = fs.get("fund_return_pct")
                lines.append(f"| {snap['date']} | {fs['score']}/10 | {fs['conclusion']} | {f'{r:+.2f}%' if r is not None else '—'} |")
        scores = [snap.get("funds", {}).get(fid, {}).get("score", 5)
                  for snap in snapshots if snap.get("funds", {}).get(fid)]
        if scores:
            avg = sum(scores) / len(scores)
            trend = "上升" if len(scores) >= 2 and scores[-1] > scores[0] else \
                    "下降" if len(scores) >= 2 and scores[-1] < scores[0] else "持平"
            lines.append(f"\n- 本月平均评分: {avg:.1f}/10 | 趋势: {trend} | 最高: {max(scores)}/10, 最低: {min(scores)}/10")

    # ═══ 复盘要点 ═══
    lines.append(f"\n---\n## 复盘要点")
    if not gate["ready"]:
        lines.append(f"\n- 🔒 Tier-1 门禁未通过: 禁止基于 Tier-2 结果触发正式参数变更。Tier-2 结果仅进入观察日志")
    lines.append(f"\n- [ ] 是否有误报或漏报？")
    lines.append(f"- [ ] 震荡预测占比是否偏高？")
    lines.append(f"- [ ] 高置信度预测是否真的更准？")
    lines.append(f"- [ ] 超额收益是否为正？系统是否提供了超越 beta 的增量价值？")
    lines.append(f"\n> 自动生成于 {today.strftime('%Y-%m-%d %H:%M')}")

    report = "\n".join(lines)
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    report_path = os.path.join(REVIEWS_DIR, f"{month_str}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📋 月度复盘已生成: {month_str}.md")


def _start_scheduler():
    t = threading.Thread(target=_scheduler_loop, daemon=True)
    t.start()


# ══════════════════════════════════════════════════════════
# 路由
# ══════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html", funds=FUNDS)


@app.route("/api/funds")
def api_funds():
    return jsonify({
        fid: {"name": f["name"], "short": f["short"], "market": f["market"]}
        for fid, f in FUNDS.items()
    })


@app.route("/api/fund/<fund_id>")
def api_fund(fund_id):
    force = request.args.get("refresh") == "1"
    result = _get_fund_response(fund_id, force_refresh=force)
    if result is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(result)


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """手动触发全量刷新"""
    global _fetching
    with _cache_lock:
        already = _fetching
    if already:
        return jsonify({"status": "already_refreshing"})
    # 在后台线程执行，避免阻塞请求
    t = threading.Thread(target=_refresh_all, daemon=True)
    t.start()
    return jsonify({"status": "started"})


@app.route("/api/status")
def api_status():
    """返回缓存状态"""
    with _cache_lock:
        fetching = _fetching
        entries = {
            fid: {"cached": fid in _cache,
                  "fetched_at": _cache[fid]["fetched_at"].strftime("%Y-%m-%d %H:%M:%S") if fid in _cache else None}
            for fid in FUNDS
        }
    return jsonify({
        "fetching": fetching,
        "funds": entries,
        "fund_count": len(FUNDS),
    })


@app.route("/api/health")
def api_health():
    """数据健康检测：指标过期 + 遗漏事件 + 过期未分析"""
    staleness = check_indicator_staleness()
    missing_events = detect_missing_events()
    recently_passed = check_recently_passed_events()

    # 汇总统计
    critical_stale = [s for s in staleness if s["severity"] == "critical"]
    health_score = 100
    health_score -= len(critical_stale) * 10
    health_score -= len([s for s in staleness if s["severity"] == "warning"]) * 3
    health_score -= len(missing_events) * 5
    health_score -= len(recently_passed) * 2
    health_score = max(0, health_score)

    return jsonify({
        "health_score": health_score,
        "status": "healthy" if health_score >= 80 else "warning" if health_score >= 50 else "critical",
        "staleness": {
            "total": len(staleness),
            "critical": len(critical_stale),
            "warning": len(staleness) - len(critical_stale),
            "items": staleness,
        },
        "missing_events": {
            "total": len(missing_events),
            "items": missing_events,
        },
        "recently_passed": {
            "total": len(recently_passed),
            "items": recently_passed,
        },
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


# ══════════════════════════════════════════════════════════
# 历史快照 API
# ══════════════════════════════════════════════════════════

@app.route("/api/history")
def api_history():
    """返回历史快照索引"""
    if not os.path.exists(HISTORY_INDEX_PATH):
        return jsonify([])
    with open(HISTORY_INDEX_PATH, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/api/history/<date_str>")
def api_history_date(date_str):
    """返回某一天的完整快照"""
    snap_path = os.path.join(HISTORY_DIR, f"{date_str}.json")
    if not os.path.exists(snap_path):
        return jsonify({"error": "not found"}), 404
    with open(snap_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(_sanitize_json(data))


# ══════════════════════════════════════════════════════════
# 优化专题 API
# ══════════════════════════════════════════════════════════

def _load_topics():
    if not os.path.exists(OPTIMIZE_TOPICS_PATH):
        return {"topics": []}
    with open(OPTIMIZE_TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_topics(data):
    os.makedirs(os.path.dirname(OPTIMIZE_TOPICS_PATH), exist_ok=True)
    with open(OPTIMIZE_TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route("/api/optimize/topics")
def api_optimize_topics():
    return jsonify(_load_topics())


@app.route("/api/optimize/topics", methods=["POST"])
def api_optimize_add_topic():
    data = _load_topics()
    new_topic = request.json
    new_topic["id"] = str(len(data["topics"]) + 1)
    new_topic.setdefault("status", "pending")
    new_topic.setdefault("created", date.today().strftime("%Y-%m-%d"))
    data["topics"].append(new_topic)
    _save_topics(data)
    return jsonify(new_topic), 201


@app.route("/api/optimize/topics/<topic_id>", methods=["PUT"])
def api_optimize_update_topic(topic_id):
    data = _load_topics()
    for t in data["topics"]:
        if t["id"] == topic_id:
            t.update(request.json)
            _save_topics(data)
            return jsonify(t)
    return jsonify({"error": "not found"}), 404


# ══════════════════════════════════════════════════════════
# 每周复盘 API
# ══════════════════════════════════════════════════════════

@app.route("/api/review")
def api_review():
    """返回最近的复盘报告列表"""
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(REVIEWS_DIR) if f.endswith(".md")],
        reverse=True
    )
    return jsonify([{"file": f, "path": f"/reviews/{f}"} for f in files])


@app.route("/api/review/generate", methods=["POST"])
def api_review_generate():
    """生成月度复盘报告（委托给 _generate_monthly_review）"""
    _generate_monthly_review()
    month_str = date.today().strftime("%Y-%m")
    return jsonify({"status": "generated", "month": month_str, "file": f"{month_str}.md"})

@app.route("/api/bottleneck-exposure")
def api_bottleneck_exposure():
    """返回各共享瓶颈的敞口统计"""
    clusters = {}
    for tag, info in BOTTLENECK_CLUSTERS.items():
        fund_statuses = {}
        green_count = 0
        for fid in info["funds"]:
            with _cache_lock:
                entry = _cache.get(fid)
            if entry and "assessment" in entry["data"]:
                a = entry["data"]["assessment"]
                fund_statuses[fid] = {
                    "short": entry["data"]["short"],
                    "conclusion": a["conclusion"],
                    "emoji": a["emoji"],
                    "score": a["score"],
                }
                if a["conclusion"] in ("安心持有", "继续持有"):
                    green_count += 1
            else:
                fund_statuses[fid] = {"short": FUNDS.get(fid, {}).get("short", fid), "conclusion": "?", "emoji": "⚪", "score": "?"}

        warn = green_count >= BOTTLENECK_CONCENTRATION_WARN and len(info["funds"]) >= 3
        clusters[tag] = {
            "label": info["label"],
            "desc": info["desc"],
            "funds": fund_statuses,
            "green_count": green_count,
            "total_dependent": len(info["funds"]),
            "concentration_warning": warn,
        }

    # 找出触发警告的簇
    warnings = [
        {"tag": tag, "label": c["label"], "count": c["green_count"]}
        for tag, c in clusters.items() if c["concentration_warning"]
    ]

    return jsonify({"clusters": clusters, "warnings": warnings})


# ══════════════════════════════════════════════════════════
# P0-任务2&4&6：评估逻辑增强（联动降级 + 破坏条件 + 背离）
# ══════════════════════════════════════════════════════════

# 背离追踪：{fund_id: {"weeks": int, "started": date}}
_divergence_tracker = {}

def _check_cascade_downgrade(fund_id, leading):
    """检查是否有共享指标恶化，触发联动降级
    只检查有真实数据的指标（value != '--'），忽略空白占位符"""
    downgrades = []
    for indicator_key, config in SHARED_INDICATORS.items():
        if fund_id not in config["funds"]:
            continue
        # 检查该指标在任意依赖板块中的 trend 变化
        for fid in config["funds"]:
            other_leading = LEADING_INDICATORS.get(fid, {})
            for name, v in other_leading.items():
                if indicator_key in name:
                    # 跳过空白占位符数据
                    if v.get("value") == "--":
                        continue
                    if v.get("trend") in ("flat", "down"):
                        downgrades.append({
                            "indicator": indicator_key,
                            "from_fund": fid,
                            "trend": v["trend"],
                            "weight": config["cascade_weight"],
                        })
                        break
    return downgrades


def _check_disruption_trigger(fund_id):
    """检查瓶颈破坏条件是否有实质突破 → 硬触发降级
    返回 (negative_triggers, positive_triggers) 分别对应利空和利好"""
    negative = []
    positive = []
    for tag, info in BOTTLENECK_DISRUPTION.items():
        if fund_id not in info["affected_funds"]:
            continue
        for cond in info["conditions"]:
            if cond["status"] == "breakthrough":
                entry = {
                    "bottleneck": info["label"],
                    "condition": cond["desc"],
                    "note": cond.get("note", ""),
                }
                # 检查该突破是否对本基金是利好
                positive_for = cond.get("positive_for", [])
                if fund_id in positive_for:
                    positive.append(entry)
                else:
                    negative.append(entry)
    return negative, positive



def compute_assessment(fund, stocks, indices, specials, fund_id=None):
    """三层架构 + 决策树判定

    Layer 1 · 即时信号 — 暴跌/RSI极端/MA50趋势（日报级别）
    Layer 2 · 瓶颈状态 — 破坏条件 + 联动降级（周/月级别）
    Layer 3 · 周期锚点 — 调节 Layer1 的解读权重（季/年级别）

    不再算单一总分。走决策树得出最终判定。"""
    details = []
    t = fund.get("exit_thresholds", {})
    leading = LEADING_INDICATORS.get(fund_id, {}) if fund_id else {}
    cycle = CYCLE_ASSESSMENTS.get(fund_id, {}) if fund_id else {}
    stage = cycle.get("stage", "")

    # ══════════════════════════════════════════════════
    # Layer 1 · 即时信号（日报）
    # ══════════════════════════════════════════════════

    # 领先指标方向
    up_count = sum(1 for v in leading.values() if v.get("trend") == "up")
    down_count = sum(1 for v in leading.values() if v.get("trend") == "down")
    flat_count = sum(1 for v in leading.values() if v.get("trend") == "flat")
    total_leading = len(leading)
    up_ratio = up_count / total_leading if total_leading else 0
    leading_bullish = up_ratio >= 0.5

    # MA50 趋势
    ma_ok = sum(1 for s in stocks.values() if s.get("above_ma50"))
    ma_total = sum(1 for s in stocks.values() if s.get("above_ma50") is not None)
    ma_ratio = ma_ok / ma_total if ma_total else 1
    idx_ok = sum(1 for s in indices.values() if s.get("above_ma50"))
    idx_total = sum(1 for s in indices.values() if s.get("above_ma50") is not None)
    idx_ratio = idx_ok / idx_total if idx_total else 1
    ma_healthy = ma_ratio >= 0.8 and idx_ratio >= 0.8
    ma_broken = ma_ratio < 0.5 or idx_ratio < 0.5

    # RSI 状态
    oversold_threshold = t.get("rsi_oversold", 30)
    overbought_threshold = t.get("rsi_overbought", 75)
    rsi_low = sum(1 for s in stocks.values() if s.get("rsi") and s["rsi"] <= oversold_threshold)
    rsi_high = sum(1 for s in stocks.values() if s.get("rsi") and s["rsi"] >= overbought_threshold)
    deep_oversold = rsi_low >= 3
    broad_overbought = rsi_high >= 4

    # 暴跌信号
    crash_drops = [tk for tk, s in stocks.items() if (s.get("day_change_pct") or 0) <= -8]
    warn_drops = [tk for tk, s in stocks.items() if (s.get("day_change_pct") or 0) <= -5]
    special_crash = [s.get('name', tk) for tk, s in specials.items() if (s.get("day_change_pct") or 0) <= -8]
    special_warn = [s.get('name', tk) for tk, s in specials.items() if (s.get("day_change_pct") or 0) <= -5]
    has_crash = bool(crash_drops) or bool(special_crash)
    has_warning = bool(warn_drops) or bool(special_warn)

    # Layer 1 摘要
    if has_crash:
        details.append(f"🚨 Layer1 暴跌预警: {', '.join(crash_drops + special_crash)}")
    elif has_warning:
        details.append(f"⚠ Layer1 异常下跌: {', '.join(warn_drops + special_warn)}")
    if deep_oversold:
        details.append(f"⚡ Layer1 RSI深度超卖({rsi_low}/{len(stocks)}只) — 反弹概率大")
    if broad_overbought:
        details.append(f"🔥 Layer1 RSI极端超买({rsi_high}/{len(stocks)}只) — 回调风险高")
    if ma_healthy:
        details.append(f"📈 Layer1 MA50趋势完好（成分{ma_ok}/{ma_total} 指数{idx_ok}/{idx_total}）")
    elif ma_broken:
        details.append(f"📉 Layer1 MA50大面积破位（成分{ma_ok}/{ma_total} 指数{idx_ok}/{idx_total}）")
    else:
        details.append(f"📊 Layer1 MA50部分破位（成分{ma_ok}/{ma_total} 指数{idx_ok}/{idx_total}）")
    details.append(f"📋 Layer1 领先指标: {up_count}↑{flat_count}→{down_count}↓ ({'偏多' if leading_bullish else '偏空'})")

    # ══════════════════════════════════════════════════
    # Layer 2 · 瓶颈状态（周/月）
    # ══════════════════════════════════════════════════
    disruption_negative, disruption_positive = _check_disruption_trigger(fund_id) if fund_id else ([], [])
    disruption_downgrade = bool(disruption_negative)
    disruption_upgrade = bool(disruption_positive)
    cascade_downgrades = _check_cascade_downgrade(fund_id, leading) if fund_id else []
    cascade_active = bool(cascade_downgrades)

    if disruption_downgrade:
        details.append("⚠ Layer2 瓶颈破坏(利空): 逻辑基础动摇")
        for dt in disruption_negative:
            details.append(f"  {dt['bottleneck']}: {dt['condition']}")
    if disruption_upgrade:
        details.append("🟢 Layer2 瓶颈突破(利好): 国产替代方向受益")
        for dt in disruption_positive:
            details.append(f"  {dt['bottleneck']}: {dt['condition']}")
    if cascade_active:
        for cd in cascade_downgrades:
            details.append(f"🔗 Layer2 联动降级: {cd['indicator']}→{cd['trend']}（来自{cd['from_fund']}）")

    # ══════════════════════════════════════════════════
    # Layer 3 · 周期锚点（季/年）— 调节解读权重
    # ══════════════════════════════════════════════════
    cycle_weights = {
        "early":       {"label": "早期", "oversold_read": "机会", "overbought_read": "正常初期热度"},
        "mid":         {"label": "中期", "oversold_read": "观望", "overbought_read": "关注"},
        "mid-to-late": {"label": "中后期", "oversold_read": "警惕", "overbought_read": "减仓信号"},
        "late":        {"label": "晚期", "oversold_read": "陷阱", "overbought_read": "坚决减仓"},
    }
    w = cycle_weights.get(stage, {"label": "未知", "oversold_read": "观望", "overbought_read": "关注"})
    details.append(f"🎯 Layer3 周期锚点: {cycle.get('label', stage or '未知')} → 超卖={w['oversold_read']} 超买={w['overbought_read']}")

    # ══════════════════════════════════════════════════
    # 决策树判定
    # ══════════════════════════════════════════════════

    # 分支1: 瓶颈破坏(利空) → 最强信号，直接红色
    if disruption_downgrade:
        conclusion = "考虑跑路"
        emoji = "🔴"
        desc = "瓶颈破坏条件触发！逻辑基础动摇，需重新评估整个投资假设"
        if disruption_upgrade:
            desc += "（但同时有国产替代利好，需区分对待）"

    # 分支2: 基本面+技术面双杀
    elif not leading_bullish and has_crash and ma_broken:
        conclusion = "考虑跑路"
        emoji = "🔴"
        desc = "领先指标转空 + 暴跌 + MA50破位 = 三重利空叠加，反弹减仓"

    # 分支3: 技术面恶化但周期早期 + 基本面完好
    elif has_crash and stage == "early" and leading_bullish:
        conclusion = "超卖观望"
        emoji = "🟡"
        desc = f"暴跌发生在周期早期+基本面完好 → 不宜追卖，等企稳。超卖解读: {w['oversold_read']}"

    # 分支4: 深度超卖 + 基本面完好 → 逆向机会
    elif deep_oversold and leading_bullish and not disruption_downgrade:
        if stage == "early":
            conclusion = "关注加仓"
            emoji = "🟢"
            desc = f"周期早期+基本面向好+深度超卖 → 反弹概率大，可考虑分批加仓"
        else:
            conclusion = "超卖观望"
            emoji = "🟡"
            desc = f"深度超卖但周期{stage} → 等企稳信号确认后再操作"

    # 分支5: 基本面完好 + 周期早期 + 趋势完好 → 安心
    elif leading_bullish and stage == "early" and not ma_broken:
        conclusion = "安心持有"
        emoji = "🟢"
        desc = "领先指标向好+周期早期+趋势完好 → 按计划持有，回调可加仓"

    # 分支6: 全面超买 + 周期中后期 → 警惕
    elif broad_overbought and stage in ("mid-to-late", "late"):
        conclusion = "高位警惕"
        emoji = "🔴"
        desc = f"周期{stage}+RSI极端超买 → {w['overbought_read']}，考虑分批减仓锁定利润"

    # 分支7: 基本面好但技术面破位 → 背离观望
    elif leading_bullish and ma_broken and not has_crash:
        conclusion = "忍着不动"
        emoji = "🟡"
        desc = "基本面与技术面背离 → 多看少动，等关键事件落地后方向明确"

    # 分支8: 正常状态
    elif leading_bullish:
        conclusion = "安心持有"
        emoji = "🟢"
        desc = "领先指标向好，按计划持有"
    elif has_warning:
        conclusion = "忍着不动"
        emoji = "🟡"
        desc = "有异常信号但未到跑路级别，保持关注"
    else:
        conclusion = "忍着不动"
        emoji = "🟡"
        desc = "信号分歧，多看少动"

    # ── 附加联动降级提示 ──
    if cascade_active and conclusion == "安心持有":
        conclusion = "忍着不动"
        emoji = "🟡"
        desc += "（联动降级触发，暂时降档）"

    return {
        "score": 0,  # 不再用线性分数，返回0表示"见决策树"
        "max_score": 0,
        "conclusion": conclusion,
        "emoji": emoji,
        "desc": desc,
        "details": details,
        "cascade_downgrades": cascade_downgrades,
        "disruption_triggers": disruption_negative,
        "divergence_weeks": 0,
    }
def _generate_prediction(fund_id, assessment, leading, cycle):
    """基于领先指标 + 周期位置 + 综合评分，生成可验证的结构化预测"""
    up_count = sum(1 for v in leading.values() if v.get("trend") == "up")
    down_count = sum(1 for v in leading.values() if v.get("trend") == "down")
    flat_count = sum(1 for v in leading.values() if v.get("trend") == "flat")
    total = len(leading)
    score = assessment["score"]
    cycle_risk = cycle.get("risk", "green") if cycle else "green"

    # 预测逻辑
    reasons = []
    if total > 0:
        up_ratio = up_count / total
        if up_ratio >= 0.8:
            bull_score = 3
            reasons.append(f"{up_count}/{total} 领先指标向上，基本面强劲")
        elif up_ratio >= 0.5:
            bull_score = 1
            reasons.append(f"{up_count}/{total} 领先指标向上，{flat_count}项走平待观察")
        elif down_count >= 2:
            bull_score = -2
            reasons.append(f"{down_count}/{total} 领先指标向下，基本面恶化")
        else:
            bull_score = 0
            reasons.append(f"领先指标分歧（{up_count}↑ {flat_count}→ {down_count}↓），方向不明")
    else:
        bull_score = 0

    # 周期修正
    if cycle:
        stage = cycle.get("stage", "")
        if stage == "early":
            bull_score += 1
            reasons.append("周期处于早期，上升空间大")
        elif stage in ("mid-to-late", "late"):
            bull_score -= 1
            reasons.append(f"周期处于{cycle.get('label','晚期')}，警惕见顶")
        if cycle_risk == "red":
            bull_score -= 1
            reasons.append("周期风险标记为红色")

    # 综合判定修正（使用结论而非已弃用的score字段）
    conclusion = assessment.get("conclusion", "")
    if conclusion in ("安心持有", "关注加仓"):
        reasons.append("Dashboard判定偏正面，基本面+技术面共振向上")
    elif conclusion in ("考虑跑路", "高位警惕"):
        bull_score -= 1
        reasons.append("Dashboard判定偏负面，保持谨慎")

    # 方向判定
    if bull_score >= 2:
        direction = "up"
        label = "看涨"
        emoji = "📈"
        confidence = "中" if bull_score >= 3 else "低"
    elif bull_score >= 0:
        direction = "flat"
        label = "震荡偏强"
        emoji = "📊"
        confidence = "低"
    elif bull_score >= -1:
        direction = "flat-down"
        label = "震荡偏弱"
        emoji = "📉"
        confidence = "低"
    else:
        direction = "down"
        label = "看跌"
        emoji = "🔻"
        confidence = "中" if bull_score <= -3 else "低"

    # 关键观察点（可验证的证伪条件）
    key_dates = KEY_DATES.get(fund_id, [])
    today = date.today()
    upcoming = [kd for kd in key_dates if kd["date"] > today]
    upcoming.sort(key=lambda x: x["date"])
    watchpoints = []
    if upcoming:
        first = upcoming[0]
        watchpoints.append(f"{first['event']}（{first['date'].strftime('%m/%d')}）后重新评估")
    if down_count > 0 or flat_count > 0:
        watchpoints.append(f"关注 {down_count+flat_count} 项走弱指标是否改善")
    if score <= 4:
        watchpoints.append("综合评分若跌破3 → 果断跑路")

    # ── P0-任务3：指标层预测 ─────────────────
    # 对每个有真实数据的领先指标，预测下次读数的方向
    indicator_predictions = {}
    for name, v in leading.items():
        if v.get("value") == "--":
            continue
        current_trend = v.get("trend", "flat")
        indicator_predictions[name] = {
            "current_value": v["value"],
            "current_trend": current_trend,
            "predicted_next_trend": current_trend,  # 预测趋势延续
            "update_cycle": v.get("update_cycle", ""),
        }

    # 验证日期
    verify_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")  # 月度验证
    indicator_verify_date = (today + timedelta(days=90)).strftime("%Y-%m-%d")  # 指标层按季度验证

    return {
        "direction": direction,
        "prediction_type": "neutral" if direction in ("flat", "flat-down") else "directional",
        "label": label,
        "emoji": emoji,
        "confidence": confidence,
        "timeframe": "未来1月",
        "verify_date": verify_date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "reasons": reasons,
        "watchpoints": watchpoints,
        # P0-任务3：双轨验证
        "indicator_predictions": indicator_predictions,
        "indicator_verify_date": indicator_verify_date,
        "verification_tiers": {
            "tier1_indicator": {
                "desc": "指标层验证（季度）：预测的指标趋势 vs 实际公布数据是否吻合 — 验证瓶颈逻辑是否正确",
                "verify_by": indicator_verify_date,
            },
            "tier2_price": {
                "desc": "价格层验证（30天）：预测的方向 vs 实际走势 — 仅作噪音监控，不作为方法论对错证据",
                "verify_by": verify_date,
                "grading": "三档：✅(方向+强度吻合) / ➡️(方向对但强度偏弱) / ❌(方向错)",
            },
        },
    }


# ══════════════════════════════════════════════════════════
# 交易操作 API
# ══════════════════════════════════════════════════════════

@app.route("/api/action")
def api_action():
    """返回今日操作建议（叠层信号交易系统）"""
    pf = _load_portfolio()
    if not pf:
        return jsonify({"error": "portfolio.json not found"}), 404

    # 构建 dashboard_cache: {fund_id: {"data": ..., "fetched_at": ...}}
    dash_cache = {}
    with _cache_lock:
        for fid in FUNDS:
            entry = _cache.get(fid)
            if entry:
                dash_cache[fid] = entry

    result = evaluate_daily_actions(pf, dash_cache)
    return jsonify(_sanitize_json(result))


# ══════════════════════════════════════════════════════════
# 持仓总览
# ══════════════════════════════════════════════════════════

PORTFOLIO_PATH = os.path.join(PROJECT_DIR, "portfolio.json")


def _load_portfolio():
    if not os.path.exists(PORTFOLIO_PATH):
        return None
    with open(PORTFOLIO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_portfolio(data):
    data["updated"] = date.today().strftime("%Y-%m-%d")
    with open(PORTFOLIO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route("/portfolio")
def portfolio_page():
    return render_template("portfolio.html")


@app.route("/api/portfolio")
def api_portfolio():
    """返回持仓数据 + 实时 Dashboard 判定"""
    pf = _load_portfolio()
    if not pf:
        return jsonify({"error": "portfolio.json not found"}), 404

    # 用缓存中的实时判定覆盖 sector 状态
    enriched_sectors = {}
    for sector, info in pf.get("sector_allocation", {}).items():
        enriched = dict(info)
        # 找到该板块对应 dashboard 基金的最新判定
        dash_ids = info.get("funds", [])
        conclusions = []
        for did in dash_ids:
            with _cache_lock:
                entry = _cache.get(did)
            if entry and "assessment" in entry["data"]:
                a = entry["data"]["assessment"]
                conclusions.append({
                    "conclusion": a["conclusion"],
                    "emoji": a["emoji"],
                    "desc": a.get("desc", ""),
                    "return_pct": entry["data"].get("fund_return_pct"),
                })
        if conclusions:
            # 取最差的判定
            worst = min(conclusions, key=lambda c: {
                "安心持有": 0, "关注加仓": 0, "继续持有": 1,
                "忍着不动": 2, "超卖观望": 2, "高位警惕": 3,
                "考虑跑路": 4,
            }.get(c["conclusion"], 2))
            enriched["live_conclusion"] = worst["conclusion"]
            enriched["live_emoji"] = worst["emoji"]
            enriched["live_return_pct"] = worst["return_pct"]
        enriched_sectors[sector] = enriched

    pf["sector_allocation_live"] = enriched_sectors

    # 添加各持仓的实时判定
    for h in pf.get("holdings", []):
        did = h.get("dashboard_id")
        if did:
            with _cache_lock:
                entry = _cache.get(did)
            if entry and "assessment" in entry["data"]:
                a = entry["data"]["assessment"]
                h["live_conclusion"] = a["conclusion"]
                h["live_emoji"] = a["emoji"]
                h["live_return_pct"] = entry["data"].get("fund_return_pct")
                h["live_prediction"] = entry["data"].get("prediction", {}).get("label", "")

    return jsonify(pf)


@app.route("/api/portfolio/update", methods=["POST"])
def api_portfolio_update():
    """更新持仓数据（手动触发）"""
    data = request.json
    pf = _load_portfolio() or {}
    pf.update(data)
    _save_portfolio(pf)
    return jsonify({"status": "saved", "updated": pf["updated"]})


@app.route("/api/portfolio/action", methods=["POST"])
def api_portfolio_add_action():
    """追加操作日志"""
    pf = _load_portfolio()
    if not pf:
        return jsonify({"error": "portfolio.json not found"}), 404
    action = request.json
    action["date"] = date.today().strftime("%Y-%m-%d")
    pf.setdefault("action_log", []).insert(0, action)
    _save_portfolio(pf)
    return jsonify({"status": "logged"})


# ══════════════════════════════════════════════════════════
# 启动
# ══════════════════════════════════════════════════════════

def _warmup_cache():
    """后台预热：启动后自动拉取全部板块数据"""
    _time.sleep(2)  # 等 Flask 完全启动
    print("🔥 缓存预热中...")
    _refresh_all()
    print("✅ 缓存预热完成")


if __name__ == "__main__":
    import os as _os
    _start_scheduler()

    # Flask debug reloader fork 两个进程，只在子进程预热
    if _os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        warmup_thread = threading.Thread(target=_warmup_cache, daemon=True)
        warmup_thread.start()

    print("⏰ 定时刷新已启动（每日 18:00）")
    print("📊 Investment Dashboard 基金监控仪表盘")
    print(f"   已配置 {len(FUNDS)} 只基金")
    print("   打开 http://localhost:5000")

    app.run(debug=True, host="127.0.0.1", port=5000)
