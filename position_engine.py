"""动态仓位模型 V2 — 多因子 Position Sizing

用法:
  python3 position_engine.py          # 输出完整因子表
  python3 position_engine.py --save   # 输出并保存 snapshot
"""
import urllib.request, json, sys, os
from config import DATA_DIR
from datetime import date
from collections import defaultdict
from storage import write_json

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
API = 'http://localhost:5000/api'

# ═══════════════════════════════════════
# 因子定义
# ═══════════════════════════════════════

def rsi_factor(rsi):
    """RSI→仓位权重：越低仓位越重"""
    if rsi is None: return 1.0
    return max(0.3, min(1.5, 1 + 2.0 * (50 - rsi) / 100))

def trend_factor(ma_ok, total):
    """MA50修复率→连续映射，消除悬崖效应"""
    if total == 0: return 0.5
    return max(0.5, min(1.0, 0.5 + 0.1 * ma_ok))

def fundamental_score(up_count, total):
    """领先指标up比例→百分比分数"""
    if total == 0: return 50
    return up_count / total * 100

def fundamental_factor(score):
    """分数→因子，避免硬阈值悬崖。0指标=中性1.0"""
    if score is None or score < 0: return 1.0
    if score >= 80: return 1.2
    if score >= 60: return 1.1
    if score >= 40: return 1.0
    if score >= 20: return 0.7
    return 0.5

def risk_factor(vol_percentile):
    """波动率分位数→风险因子"""
    if vol_percentile is None: return 1.0
    if vol_percentile >= 0.85: return 0.6   # 极端（之前0.4太激进）
    if vol_percentile >= 0.70: return 0.7   # 显著升高
    if vol_percentile >= 0.50: return 0.8   # 偏高
    return 1.0                               # 正常

# ═══════════════════════════════════════
# 数据获取
# ═══════════════════════════════════════

def get_volatility_percentile(fund_id):
    """用 Bollinger bandwidth 作为波动率代理。比完整历史波动率轻量。"""
    try:
        d = json.loads(urllib.request.urlopen(f'{API}/fund/{fund_id}').read())
        stocks = d.get('stocks', {})
        # 用 Bollinger bandwidth_pct 的中位数作为波动率代理
        bws = []
        for s in stocks.values():
            bw = s.get('indicators', {}).get('bollinger', {}).get('bandwidth_pct')
            if bw: bws.append(bw)
        if not bws: return None
        avg_bw = sum(bws) / len(bws)
        # 简化：将当前 bandwidth 映射到分位数（后续可用历史数据改进）
        # bandwidth > 30% = 高波动，< 15% = 低波动
        if avg_bw > 30: return 0.90
        if avg_bw > 20: return 0.75
        if avg_bw > 12: return 0.50
        return 0.25
    except: return None

def get_fund_data(fund_id):
    """获取基金的全部评估数据"""
    try:
        return json.loads(urllib.request.urlopen(f'{API}/fund/{fund_id}').read())
    except: return {}

# ═══════════════════════════════════════
# 主计算
# ═══════════════════════════════════════

def compute_all(portfolio, save_snapshot=False):
    """计算全部持仓的目标仓位。返回结果列表。"""
    holdings = [h for h in portfolio['holdings']
                if h.get('amount', 0) > 0 and h.get('status') not in ('sold', 'non_investment', 'sell_pending')]
    config = portfolio.get('position_config', {})
    themes = config.get('themes', {})
    threshold = config.get('rebalance_threshold', 0.01)
    max_total = config.get('max_total_exposure', 0.80)
    total_assets = portfolio['total_assets']

    results = []
    theme_exposure = defaultdict(float)

    for h in holdings:
        code = h.get('fund_code', '')
        did = h.get('dashboard_id', code)
        name = h.get('fund_name', code)[:20]
        stage = h.get('evidence_stage') or h.get('tier', 'active')
        base = h.get('base', 0.08)  # v1.1：overweight 不再是档位，由敞口层动态判定
        max_pos = h.get('max', 0.15)
        theme = h.get('theme', '')
        current_amt = h['amount']
        current_pct = current_amt / total_assets if total_assets > 0 else 0

        # 获取实时数据
        d = get_fund_data(did) if did else {}

        # RSI
        stocks = d.get('stocks', {})
        rsis = [s.get('rsi') for s in stocks.values() if s.get('rsi')]
        avg_rsi = sum(rsis) / len(rsis) if rsis else None

        # MA50
        ma_ok = sum(1 for s in stocks.values() if s.get('above_ma50'))
        ma_total = sum(1 for s in stocks.values() if s.get('above_ma50') is not None)
        if ma_total == 0: ma_total = len(stocks)

        # 领先指标
        leading = d.get('leading_indicators', {})
        up_count = sum(1 for v in leading.values() if v.get('trend') == 'up')
        total_leading = len(leading)
        if total_leading == 0: total_leading = 1  # 无指标→中性

        # 波动率
        vol_pct = get_volatility_percentile(did)

        # 五个因子
        rsi_f = round(rsi_factor(avg_rsi), 2)
        trend_f = round(trend_factor(ma_ok, ma_total), 2)
        fund_score = round(fundamental_score(up_count, total_leading), 0)
        fund_f = round(fundamental_factor(fund_score), 2)
        risk_f = round(risk_factor(vol_pct), 2)

        # Raw target
        raw = round(base * rsi_f * trend_f * fund_f * risk_f * 100, 1)
        # Final target (capped at max)
        final = min(raw, max_pos * 100)
        delta = round(final - current_pct * 100, 1)

        # Action
        if abs(delta) < threshold * 100:
            action = 'HOLD'
        elif delta > 0:
            action = '🟢 BUY'
        else:
            action = '🔴 REDUCE'

        results.append({
            'code': code, 'name': name, 'tier': stage, 'theme': theme,
            'current': round(current_pct * 100, 1),
            'base_pct': round(base * 100, 1),
            'rsi': round(avg_rsi, 1) if avg_rsi else None,
            'rsi_f': rsi_f,
            'ma_ok': ma_ok, 'ma_total': ma_total, 'trend_f': trend_f,
            'fund_score': fund_score, 'fund_f': fund_f,
            'risk_f': risk_f,
            'raw': raw, 'final': final, 'delta': delta, 'action': action,
            'max': round(max_pos * 100, 1),
        })

        if theme:
            theme_exposure[theme] += current_pct

    # 主题约束检查
    theme_warnings = []
    for t, info in themes.items():
        current_exp = theme_exposure.get(t, 0) * 100
        max_exp = info.get('max_exposure', 0.30) * 100
        if current_exp > max_exp:
            theme_warnings.append(f"⚠ {t}: {current_exp:.1f}% > {max_exp:.0f}% 上限")

    # 总仓位检查
    total_current = sum(r['current'] for r in results)
    total_warning = f"⚠ 总仓位 {total_current:.1f}% > {max_total*100:.0f}%" if total_current > max_total * 100 else ""

    # 保存 snapshot
    if save_snapshot:
        snap_dir = os.path.join(DATA_DIR, 'position_snapshots')
        os.makedirs(snap_dir, exist_ok=True)
        today = date.today().strftime('%Y-%m-%d')
        snap = {
            'date': today, 'total_assets': total_assets,
            'total_position': round(total_current, 1),
            'results': results, 'theme_warnings': theme_warnings,
        }
        write_json(os.path.join(snap_dir, f'{today}.json'), snap)

    return results, theme_warnings, total_warning, total_current


def print_table(results, theme_warnings, total_warning, total_current):
    """打印因子展开表"""
    print(f"{'持仓':18s} {'当前':>5s} {'基础':>5s} {'RSI':>5s} {'RSI_f':>5s} {'MA50':>5s} {'Trend':>5s} {'Fund%':>5s} {'Fund_f':>5s} {'Risk':>5s} {'Raw':>5s} {'Final':>5s} {'Δ':>5s} {'操作':>8s}")
    print("-" * 110)

    for r in results:
        rsi_str = f"{r['rsi']:>4.1f}" if r['rsi'] else '   ?'
        print(f"{r['name']:18s} {r['current']:>4.1f}% {r['base_pct']:>4.1f}% {rsi_str:>5s} {r['rsi_f']:>5.2f} {r['ma_ok']}/{r['ma_total']:1d} {r['trend_f']:>5.2f} {r['fund_score']:>4.0f}% {r['fund_f']:>5.2f} {r['risk_f']:>5.2f} {r['raw']:>4.1f}% {r['final']:>4.1f}% {r['delta']:>+4.1f}% {r['action']:>8s}")

    print(f"\n总仓位: {total_current:.1f}%")

    if theme_warnings:
        print("\n主题约束:")
        for w in theme_warnings: print(f"  {w}")
    if total_warning:
        print(f"  {total_warning}")


# ═══════════════════════════════════════
# CLI
# ═══════════════════════════════════════

if __name__ == '__main__':
    with open(os.path.join(DATA_DIR, 'portfolio.json')) as f:
        pf = json.load(f)

    save = '--save' in sys.argv
    results, tw, tlw, tc = compute_all(pf, save_snapshot=save)
    print_table(results, tw, tlw, tc)
