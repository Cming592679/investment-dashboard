"""Investment Dashboard — 基金监控仪表盘（多基金版 + 缓存 + 历史快照）"""

import json
import os
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
)
from data_fetcher import get_index_snapshot, get_stock_snapshot

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
            snapshot["funds"][fid] = {
                "name": d["name"],
                "score": a["score"],
                "conclusion": a["conclusion"],
                "emoji": a["emoji"],
                "details": a.get("details", []),
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
        "funds": {fid: {"score": snapshot["funds"][fid]["score"],
                         "conclusion": snapshot["funds"][fid]["conclusion"]}
                  for fid in snapshot["funds"]}
    })
    with open(HISTORY_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"📸 快照已保存: {today_str} ({len(snapshot['funds'])} 只基金)")


def _attach_meta(data, fetched_at, is_fetching):
    """给响应附加时间元信息"""
    return {
        **data,
        "cached_at": fetched_at.strftime("%Y-%m-%d %H:%M:%S"),
        "fetching": is_fetching,
    }


# ══════════════════════════════════════════════════════════
# 后台定时刷新（每日 14:00）
# ══════════════════════════════════════════════════════════

def _scheduler_loop():
    """后台线程：每日 14:00 刷新快照 + 每月1日复盘"""
    global _last_auto_refresh_date
    _last_review_month = None
    while True:
        _time.sleep(30)
        now = datetime.now()
        today = now.date()

        # 每日 14:00-14:02 刷新
        if now.hour == 14 and now.minute <= 2:
            if _last_auto_refresh_date != today:
                print(f"⏰ 定时刷新触发 {now.strftime('%H:%M:%S')}")
                _refresh_all()

        # 每月 1 日 10:00-10:02 生成复盘
        if today.day == 1 and now.hour == 10 and now.minute <= 2:
            month_key = today.strftime("%Y-%m")
            if _last_review_month != month_key:
                _last_review_month = month_key
                print(f"📋 月度复盘触发 {now.strftime('%H:%M:%S')}")
                try:
                    _generate_monthly_review()
                except Exception as e:
                    print(f"  ⚠ 复盘失败: {e}")


def _generate_monthly_review():
    """生成月度复盘（内部函数，由调度器调用）"""
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

    lines = [
        f"# 月度复盘 — {month_str}",
        f"\n生成时间: {today.strftime('%Y-%m-%d')}",
        f"\n快照天数: {len(snapshots)}",
        f"\n---\n",
    ]

    for fid, fund_info in FUNDS.items():
        lines.append(f"\n## {fund_info['short']} ({fid})")
        lines.append(f"\n| 日期 | 评分 | 结论 | 研判细节 |")
        lines.append("|------|-----|------|---------|")
        for snap in snapshots:
            fs = snap.get("funds", {}).get(fid)
            if fs:
                detail_str = "；".join(fs.get("details", []))[:80] or "—"
                lines.append(f"| {snap['date']} | {fs['score']}/10 | {fs['conclusion']} | {detail_str} |")

        scores = [snap.get("funds", {}).get(fid, {}).get("score", 5)
                  for snap in snapshots if snap.get("funds", {}).get(fid)]
        if scores:
            avg = sum(scores) / len(scores)
            trend = "上升" if len(scores) >= 2 and scores[-1] > scores[0] else \
                    "下降" if len(scores) >= 2 and scores[-1] < scores[0] else "持平"
            lines.append(f"\n- 本月平均综合评分: {avg:.1f}/10")
            lines.append(f"- 趋势: {trend}")
            lines.append(f"- 最高: {max(scores)}/10, 最低: {min(scores)}/10")

    lines.append(f"\n---\n## Tier-1 指标层验证（方法论对错）")
    lines.append(f"\n验证方式：对比预测的指标趋势 vs 实际公布的数据")
    lines.append(f"\n- [ ] 各板块领先指标预测是否准确？")
    lines.append(f"- [ ] 哪些指标的趋势判断有系统性偏差？")
    lines.append(f"\n## Tier-2 价格层验证（短期噪音监控）")
    lines.append(f"\n验证方式：对比预测方向 vs 实际7日走势")
    lines.append(f"\n注意：价格层仅作短期监控，不作为方法论对错证据。")
    lines.append(f"牛市里\"看涨→没跌就算对\"会制造虚假高准确率，需配合强度偏差校准。")
    lines.append(f"\n| 板块 | 预测 | 实际方向 | 强度偏差 | 判定 |")
    lines.append(f"|------|------|---------|---------|------|")
    lines.append(f"| — | — | — | — | 待本月数据 |")
    lines.append(f"\n## 复盘要点")
    lines.append(f"\n- [ ] 是否有误报或漏报？")
    lines.append(f"- [ ] 阈值/权重是否需要调整？")
    lines.append(f"- [ ] 共享瓶颈敞口是否在可接受范围？")
    lines.append(f"- [ ] 瓶颈破坏条件有无新进展？")
    lines.append(f"\n> 自动生成于 {today.strftime('%Y-%m-%d %H:%M')}\n")

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
        return jsonify(json.load(f))


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
    """生成月度复盘报告"""
    today = date.today()
    month_str = today.strftime("%Y-%m")

    # 读取本月所有快照
    snapshots = []
    for i in range(31):
        d = today - timedelta(days=30 - i)
        snap_path = os.path.join(HISTORY_DIR, f"{d.strftime('%Y-%m-%d')}.json")
        if os.path.exists(snap_path):
            with open(snap_path, "r", encoding="utf-8") as f:
                snapshots.append(json.load(f))

    if not snapshots:
        return jsonify({"error": "本月暂无快照数据"}), 404

    # 生成复盘报告
    lines = [
        f"# 月度复盘 — {month_str}",
        f"\n生成时间: {today.strftime('%Y-%m-%d')}",
        f"\n快照天数: {len(snapshots)}",
        f"\n---\n",
    ]

    for fid, fund_info in FUNDS.items():
        lines.append(f"\n## {fund_info['short']} ({fid})")
        lines.append(f"\n| 日期 | 评分 | 结论 | 研判细节 |")
        lines.append("|------|-----|------|---------|")
        for snap in snapshots:
            fs = snap.get("funds", {}).get(fid)
            if fs:
                detail_str = "；".join(fs.get("details", []))[:100] or "—"
                lines.append(f"| {snap['date']} | {fs['score']}/10 | {fs['conclusion']} | {detail_str} |")

        # 趋势分析
        scores = []
        for snap in snapshots:
            fs = snap.get("funds", {}).get(fid)
            if fs:
                scores.append(fs.get("score", 5))
        if scores:
            avg = sum(scores) / len(scores)
            trend = "上升" if len(scores) >= 2 and scores[-1] > scores[0] else \
                    "下降" if len(scores) >= 2 and scores[-1] < scores[0] else "持平"
            lines.append(f"\n- 本月平均综合评分: {avg:.1f}/10")
            lines.append(f"- 趋势: {trend}")
            lines.append(f"- 最高: {max(scores)}/10, 最低: {min(scores)}/10")

    lines.append(f"\n---\n## Tier-1 指标层验证（方法论对错）")
    lines.append(f"\n验证方式：对比预测的指标趋势 vs 实际公布的数据")
    lines.append(f"\n- [ ] 各板块领先指标预测是否准确？趋势延续假设有哪些被打破？")
    lines.append(f"\n## Tier-2 价格层验证（短期噪音监控）")
    lines.append(f"\n验证方式：对比预测方向 vs 实际7日走势（不作为方法论对错证据）")
    lines.append(f"\n| 板块 | 预测 | 实际方向 | 强度偏差 | 判定 |")
    lines.append(f"|------|------|---------|---------|------|")
    lines.append(f"| — | — | — | — | 待本月数据 |")
    lines.append(f"\n## 复盘要点")
    lines.append(f"\n- [ ] 是否有误报或漏报？阈值/权重是否需要调整？")
    lines.append(f"- [ ] 共享瓶颈敞口是否在可接受范围？")
    lines.append(f"- [ ] 瓶颈破坏条件有无新进展？")
    lines.append(f"\n> 此报告由系统自动生成，请结合实际情况人工复核。\n")

    report = "\n".join(lines)
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    report_path = os.path.join(REVIEWS_DIR, f"{month_str}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return jsonify({"status": "generated", "month": month_str, "file": f"{month_str}.md"})


# ══════════════════════════════════════════════════════════
# 逃跑信号计算（与之前相同）
# ══════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════
# P0-任务1：共享瓶颈敞口 API
# ══════════════════════════════════════════════════════════

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
    """检查瓶颈破坏条件是否有实质突破 → 硬触发降级"""
    triggers = []
    for tag, info in BOTTLENECK_DISRUPTION.items():
        if fund_id not in info["affected_funds"]:
            continue
        for cond in info["conditions"]:
            if cond["status"] == "breakthrough":
                triggers.append({
                    "bottleneck": info["label"],
                    "condition": cond["desc"],
                    "note": cond.get("note", ""),
                })
    return triggers


def compute_assessment(fund, stocks, indices, specials, fund_id=None):
    """综合研判：领先指标(0-5) + 周期(0-2) + 技术面(0-3) = 0-10
       → 🟢 安心持有(≥6) / 🟡 忍着不动(3-5) / 🔴 考虑跑路(0-2)
       日涨跌幅已大幅降权（基金无法盘中交易，单日波动=噪音）"""
    details = []
    score = 0

    # ═══ 一、领先指标 (0-5分，权重最高) ═══
    leading = LEADING_INDICATORS.get(fund_id, {}) if fund_id else {}
    if leading:
        up_count = sum(1 for v in leading.values() if v.get("trend") == "up")
        down_count = sum(1 for v in leading.values() if v.get("trend") == "down")
        flat_count = sum(1 for v in leading.values() if v.get("trend") == "flat")
        total = len(leading)
        up_ratio = up_count / total if total else 0

        if up_ratio >= 0.8:
            details.append(f"领先指标 {up_count}/{total} 向好 → +5")
            score += 5
        elif up_ratio >= 0.5:
            details.append(f"领先指标 {up_count}↑{flat_count}→{down_count}↓ 偏多 → +3")
            score += 3
        elif down_count >= 2:
            details.append(f"领先指标 {down_count} 项向下 → +0")
            score += 0
        elif down_count >= 1:
            details.append(f"领先指标走弱（{down_count}↓）→ +1")
            score += 1
        else:
            details.append(f"领先指标分歧（{up_count}↑{flat_count}→{down_count}↓）→ +2")
            score += 2
    else:
        details.append("领先指标数据缺失 → +2（默认中性）")
        score += 2

    # ═══ 二、周期位置 (0-2分) ═══
    cycle = CYCLE_ASSESSMENTS.get(fund_id, {}) if fund_id else {}
    stage = cycle.get("stage", "")
    if stage == "early":
        details.append("周期早期 → +2")
        score += 2
    elif stage == "mid":
        details.append("周期中期 → +1")
        score += 1
    elif stage in ("mid-to-late",):
        details.append(f"周期中后期（{cycle.get('label','')}）→ +1")
        score += 1
    elif stage == "late":
        details.append("周期晚期 → +0")
        score += 0
    else:
        details.append("周期未知 → +1")
        score += 1

    # ═══ 三、技术面 (0-3分，日涨跌大幅降权) ═══
    # MA50 趋势 (0-2分)
    ma_ok = sum(1 for s in stocks.values() if s.get("above_ma50"))
    ma_total = sum(1 for s in stocks.values() if s.get("above_ma50") is not None)
    ma_ratio = ma_ok / ma_total if ma_total else 1
    idx_ok = sum(1 for s in indices.values() if s.get("above_ma50"))
    idx_total = sum(1 for s in indices.values() if s.get("above_ma50") is not None)
    idx_ratio = idx_ok / idx_total if idx_total else 1

    if ma_ratio >= 0.8 and idx_ratio >= 0.8:
        details.append(f"MA50 趋势完好（成分{ma_ok}/{ma_total} 指数{idx_ok}/{idx_total}）→ +2")
        score += 2
    elif ma_ratio >= 0.5 and idx_ratio >= 0.5:
        details.append(f"MA50 部分破位（成分{ma_ok}/{ma_total} 指数{idx_ok}/{idx_total}）→ +1")
        score += 1
    else:
        details.append(f"MA50 大面积破位（成分{ma_ok}/{ma_total} 指数{idx_ok}/{idx_total}）→ +0")
        score += 0

    # RSI 极端 + 暴跌 (0-1分，降权到极致)
    t = fund.get("exit_thresholds", {})
    rsi_high = sum(1 for s in stocks.values() if s.get("rsi") and s["rsi"] >= t.get("rsi_overbought", 75))
    if rsi_high >= 4:
        details.append(f"RSI 极端超买（{rsi_high}/{len(stocks)} 只）→ -1")
        score -= 1

    # 单日暴跌只保留极端情况（>8%），且只扣1分
    extreme_drops = [tk for tk, s in stocks.items() if (s.get("day_change_pct") or 0) <= -8]
    if len(extreme_drops) >= 3:
        details.append(f"极端暴跌（{', '.join(extreme_drops)} >8%）→ -1")
        score -= 1
    elif extreme_drops:
        details.append(f"部分极端暴跌（{', '.join(extreme_drops)} >8%）→ -0")
        # just note it, don't penalize

    # 特殊标的极端暴跌
    for tk, s in specials.items():
        if (s.get("day_change_pct") or 0) <= -8:
            details.append(f"{s.get('name', tk)} 极端暴跌 {s['day_change_pct']:.1f}% → -1")
            score -= 1

    # ═══ P1-任务7：双重计分检查 ═══
    if fund_id and cycle:
        cycle_note = cycle.get("note", "")
        for name in leading:
            # 检查领先指标关键词是否也出现在周期判断依据中
            keywords = name.split("【")[0].strip().rstrip("QoQYoY").strip()
            if len(keywords) >= 4 and keywords in cycle_note:
                details.append(f"⚠ 双重计分提示: \"{keywords}\" 同时出现在领先指标和周期判断中，可能被计入两个因子")
                break  # 只提示一次

    # ═══ P0-任务4：瓶颈破坏条件硬触发 ═══
    disruption_triggers = _check_disruption_trigger(fund_id) if fund_id else []
    disruption_downgrade = False
    if disruption_triggers:
        disruption_downgrade = True
        details.append("⚠ 瓶颈破坏条件触发！逻辑基础动摇 → 强制降级")
        for dt in disruption_triggers:
            details.append(f"  {dt['bottleneck']}: {dt['condition']} ({dt['note']})")

    # ═══ P0-任务2：共享指标联动降级 ═══
    cascade_downgrades = _check_cascade_downgrade(fund_id, leading) if fund_id else []
    cascade_downgrade = False
    if cascade_downgrades:
        cascade_downgrade = True
        total_weight = sum(cd["weight"] for cd in cascade_downgrades)
        score -= total_weight
        for cd in cascade_downgrades:
            details.append(f"联动降级: {cd['indicator']}→{cd['trend']}（来自{cd['from_fund']}）-{cd['weight']}")

    # ═══ P1-任务6：技术面/基本面背离检测 ═══
    divergence_active = False
    if fund_id:
        tech_score = 0
        # 技术面评分推断：从 details 中反向解析
        for d in details:
            if "MA50 趋势完好" in d:
                tech_score = 2
            elif "MA50 部分破位" in d:
                tech_score = 1
        fundamental_score = score - tech_score  # 近似：总分-技术分=基本分
        if tech_score == 0 and fundamental_score >= 4 and not disruption_downgrade:
            # 技术面弱但基本面强 → 检测背离
            today = date.today()
            tracker = _divergence_tracker.get(fund_id, {"weeks": 0, "started": today})
            last_started = tracker.get("started", today)
            if (today - last_started).days >= 7:  # 新的一周
                tracker["weeks"] += 1
                tracker["started"] = today
            elif tracker["weeks"] == 0:
                tracker["weeks"] = 1
                tracker["started"] = today
            _divergence_tracker[fund_id] = tracker

            if tracker["weeks"] >= DIVERGENCE_DOWNGRADE_WEEKS:
                details.append(f"技术面/基本面持续背离 {tracker['weeks']} 周 → 强制降级到🟡")
                divergence_active = True
        else:
            # 背离解除，重置
            if fund_id in _divergence_tracker:
                del _divergence_tracker[fund_id]

    # ═══ 综合判定 ═══
    score = max(0, min(10, score))  # clamp 0-10

    # 硬触发降级 > 综合评分
    if disruption_downgrade:
        conclusion = "考虑跑路"
        emoji = "🔴"
        desc = "瓶颈破坏条件触发！逻辑基础动摇，需重新评估整个投资假设"
    elif divergence_active or (cascade_downgrade and score >= 6):
        conclusion = "忍着不动"
        emoji = "🟡"
        desc = "因联动降级或技术面背离触发，暂时观望"
    elif score >= 6:
        conclusion = "安心持有"
        emoji = "🟢"
        desc = "领先指标+技术面共振，按计划持有，回调可加仓"
    elif score >= 3:
        conclusion = "忍着不动"
        emoji = "🟡"
        desc = "信号有分歧，多看少动，等关键事件落地后再判断"
    else:
        conclusion = "考虑跑路"
        emoji = "🔴"
        desc = "领先指标恶化或趋势破位，反弹减仓/清仓"

    return {
        "score": score,
        "max_score": 10,
        "conclusion": conclusion,
        "emoji": emoji,
        "desc": desc,
        "details": details,
        "cascade_downgrades": cascade_downgrades,
        "disruption_triggers": disruption_triggers,
        "divergence_weeks": _divergence_tracker.get(fund_id, {}).get("weeks", 0) if fund_id else 0,
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

    # 综合评分修正
    if score >= 7:
        reasons.append("综合评分高，基本面+技术面共振向上")
    elif score <= 3:
        bull_score -= 1
        reasons.append(f"综合评分偏低 {score}/10，保持谨慎")

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
    verify_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    indicator_verify_date = (today + timedelta(days=90)).strftime("%Y-%m-%d")  # 指标层按季度验证

    return {
        "direction": direction,
        "label": label,
        "emoji": emoji,
        "confidence": confidence,
        "timeframe": "未来1周",
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
                "desc": "价格层验证（7天）：预测的方向 vs 实际走势 — 仅作短期噪音监控，不作为方法论对错证据",
                "verify_by": verify_date,
                "grading": "三档：✅(方向+强度吻合) / ➡️(方向对但强度偏弱) / ❌(方向错)",
            },
        },
    }


# ══════════════════════════════════════════════════════════
# 启动
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    _start_scheduler()
    print("⏰ 定时刷新已启动（每日 14:00）")
    print("📊 Investment Dashboard 基金监控仪表盘")
    print(f"   已配置 {len(FUNDS)} 只基金")
    print("   打开 http://localhost:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
