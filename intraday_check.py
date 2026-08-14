"""盘中实时检查：pending_plans 触发状态 + 异常告警

用法:
  python3 intraday_check.py           # 输出当前状态
  python3 intraday_check.py --json    # JSON输出（供前端）
"""
import urllib.request, json, sys, os
from datetime import date, datetime
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
API = 'http://localhost:5000/api'

# ═══════════════════════════════════
# 数据获取
# ═══════════════════════════════════

def get_estimate(code):
    """获取单只基金盘中估值"""
    try:
        url = f"https://v1.apizero.cn/api/fund?action=estimate&code={code}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')
        data = json.loads(resp)
        if data.get('code') == 0:
            return data['data']
    except: pass
    return None

def get_dashboard_data(fund_id):
    """获取板块实时技术指标"""
    try:
        return json.loads(urllib.request.urlopen(f'{API}/fund/{fund_id}').read())
    except: return {}

# ═══════════════════════════════════
# Plan 触发检查
# ═══════════════════════════════════

def _weighted_rsi(fund_id, stocks):
    """用 HOLDING_WEIGHTS 加权计算板块 RSI。核心权重股主导。
    返回 (加权RSI, 权重覆盖数/总数)。无权重则 fallback 简单平均。
    """
    try:
        from config import DATA_DIR,  BOARD_FUND_MAP, HOLDING_WEIGHTS
        fund_code = BOARD_FUND_MAP.get(fund_id)
        weights = HOLDING_WEIGHTS.get(fund_code) if fund_code else None
    except ImportError:
        weights = None

    if weights:
        total_w = 0.0
        weighted_rsi = 0.0
        covered = 0
        for ticker, w in weights.items():
            s = stocks.get(ticker)
            if s and s.get('rsi') is not None:
                weighted_rsi += w * s['rsi']
                total_w += w
                covered += 1
        if total_w > 0:
            return weighted_rsi / total_w, covered, len(weights)

    # fallback 简单平均
    rsis = [s.get('rsi') for s in stocks.values() if s.get('rsi') is not None]
    if rsis:
        return sum(rsis) / len(rsis), len(rsis), len(stocks)
    return None, 0, 0


def check_plan(plan, portfolio):
    """检查一条 plan 是否触发。返回状态字符串。"""
    module = plan.get('module', '')
    trigger = plan.get('trigger', '')
    today = date.today()

    # === CPO: 加权RSI < 50 ===
    if module == 'CPO' and plan['direction'] == 'buy':
        d = get_dashboard_data('CPO')
        stocks = d.get('stocks', {})
        wrsi, covered, total = _weighted_rsi('CPO', stocks)
        if wrsi is not None:
            if wrsi < 50:
                return f"✅ 触发！加权RSI={wrsi:.1f}<50（核心权重股主导）→ {plan['action_if_triggered']}"
            else:
                return f"❌ 未触发 加权RSI={wrsi:.1f}≥50 → {plan['action_if_not']}"
        return f"? 无RSI数据"

    # === 半导体设备: SMIC Q2 8/15 ===
    if module == '半导体设备':
        smic_date = date(2026, 8, 15)
        days_left = (smic_date - today).days
        if days_left > 0:
            return f"👀 等 {days_left} 天 → 8/15 中芯国际Q2"
        elif days_left == 0:
            return f"⚡ 今天！中芯国际Q2 → {plan['action_if_triggered']}"
        else:
            return f"📋 已过期 {abs(days_left)} 天，请跟进结果"

    # === 军工电子: 持有收益 > -15% ===
    if module == '军工电子':
        for h in portfolio['holdings']:
            if h.get('fund_code') == '015789':
                ret = h.get('holding_return_pct', -99)
                if ret > -15:
                    return f"✅ 触发！持有收益 {ret:+.1f}% > -15% → {plan['action_if_triggered']}"
                else:
                    gap = -15 - ret
                    return f"❌ 未触发 持有收益 {ret:+.1f}% 还需涨 {gap:.1f}% → {plan['action_if_not']}"
        return "? 无持仓数据"

    # === 产业机遇: 季度报告 ===
    if module == '半导体(全链)':
        return f"👀 观察中 → {plan['note'][:40]}"

    # === 默认 ===
    if plan.get('status') == 'done':
        return "✅ 已完成"

    return f"📋 {plan['status']} → {plan['note'][:40]}"


# ═══════════════════════════════════
# 异常告警
# ═══════════════════════════════════

def check_alerts(portfolio):
    """检查盘中异常"""
    alerts = []
    for h in portfolio['holdings']:
        code = h.get('fund_code', '')
        if h.get('amount', 0) <= 0 or h.get('status') in ('sold', 'non_investment', 'sell_pending'):
            continue

        est = get_estimate(code)
        if not est: continue

        chg = est.get('change_rate')
        if chg is None: continue
        chg = float(chg)

        name = est.get('fund_name', code)[:20]

        # 单日涨跌 > ±5%
        if chg > 5:
            alerts.append(f"🔴 {name} 暴涨 +{chg:.1f}%")
        elif chg < -5:
            alerts.append(f"🔴 {name} 暴跌 {chg:.1f}%")

    # RSI 极端区（用加权 RSI）
    for fid in ['019633', '015789', 'CPO', 'STORAGE']:
        d = get_dashboard_data(fid)
        if not d: continue
        stocks = d.get('stocks', {})
        wrsi, _, _ = _weighted_rsi(fid, stocks)
        if wrsi is None: continue
        short = d.get('short', fid)
        if wrsi > 75:
            alerts.append(f"⚠ {short} RSI={wrsi:.1f} 超买区")
        elif wrsi < 30:
            alerts.append(f"⚡ {short} RSI={wrsi:.1f} 超卖区")

    return alerts


# ═══════════════════════════════════
# 主入口
# ═══════════════════════════════════

def run(portfolio):
    """返回 {plans: [...], alerts: [...], estimates: {...}}"""
    # 盘中估值（批量获取，注意50次/天限额）
    estimates = {}
    for h in portfolio['holdings']:
        code = h.get('fund_code', '')
        if h.get('amount', 0) <= 0 or h.get('status') in ('sold', 'non_investment', 'sell_pending'):
            continue
        est = get_estimate(code)
        if est:
            estimates[code] = {
                'name': est.get('fund_name', ''),
                'change_rate': float(est.get('change_rate', 0)),
                'estimate': est.get('estimate'),
                'net_value': est.get('net_value'),
                'update_time': est.get('update_time', ''),
            }

    # Plan 检查
    plans_status = []
    for p in portfolio.get('pending_plans', []):
        if p.get('status') == 'done':
            continue
        status = check_plan(p, portfolio)
        plans_status.append({
            'module': p['module'],
            'fund': p.get('fund', ''),
            'direction': p.get('direction', ''),
            'target': p.get('target', 0),
            'remaining': p.get('remaining', 0),
            'status': status,
            'trigger': p.get('trigger', ''),
        })

    # 告警
    alerts = check_alerts(portfolio)

    return {'plans': plans_status, 'alerts': alerts, 'estimates': estimates}


# ═══════════════════════════════════
# CLI
# ═══════════════════════════════════

if __name__ == '__main__':
    with open(os.path.join(DATA_DIR, 'portfolio.json')) as f:
        pf = json.load(f)

    result = run(pf)

    if '--json' in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== 📋 待执行计划 ===")
        for p in result['plans']:
            icon = '✅' if '触发' in p['status'] else '👀' if '等' in p['status'] else '❌'
            print(f"  {icon} [{p['module']}] {p['status']}")

        if result['alerts']:
            print("\n=== 🚨 盘中告警 ===")
            for a in result['alerts']:
                print(f"  {a}")

        if result['estimates']:
            print("\n=== 📊 盘中估值 ===")
            for code, e in result['estimates'].items():
                print(f"  {code} {e['name'][:20]:20s} {e['change_rate']:+.2f}% (更新{e['update_time']})")
