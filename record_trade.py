"""统一交易记录入口。所有买入/卖出通过此函数，确保 shares/cost/plans 同步更新。

用法:
  python3 record_trade.py buy 019633 3000 "放量确认，主仓加码"
  python3 record_trade.py sell 020608 965.70 shares "机器人减仓"
  python3 record_trade.py plan 011370 buy 2000 "明天不大涨" "CPO加仓计划"

成交约定：用户操作默认 T 日 15:00 前下单，按 T 日净值成交。
记录买入时若成交日净值未发布，暂用最新已知净值估算份额，
待成交日净值落地后按当日净值校准份额（见 PROJECT_CONTEXT.md）。

也可以在代码中调用 record_trade()。
"""
import json, os, sys
from config import DATA_DIR, TRADING_CONFIG
from datetime import date
from collections import defaultdict
from storage import write_json

try:  # 分层现金储备（v1.2）：模块缺失时降级为固定下限
    import cash_reserve as _cr
except ImportError:  # pragma: no cover
    _cr = None


def fetch_reserve_state(tier_result=None):
    """读取当前储备层级（判定由仪表盘 /api/cash-reserve 提供；不可用时回退 L0）。

    返回 tier_result dict（floor_pct 为允许的现金下限，%）；
    任何异常都回退到常规层，保证"拿不到数据时不放松约束"。
    """
    if _cr is None:
        return {
            "tier": "L0", "floor_pct": TRADING_CONFIG["position"]["min_cash_pct"],
            "label": "分层储备模块不可用，使用固定下限", "matched": [],
            "checks": [], "data_ok": False, "deployment_allowed": False,
        }
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:5000/api/cash-reserve", timeout=8) as r:
            data = json.load(r)
        if isinstance(data, dict) and "floor_pct" in data:
            return data
    except Exception:
        pass
    # 服务不可用 → 保守回退（不放松约束），提示用户手动判定
    return {
        "tier": "L0",
        "floor_pct": TRADING_CONFIG["position"]["min_cash_pct"],
        "label": "仪表盘不可用，按常规下限保守处理（如需动用储备请先启动仪表盘）",
        "matched": [], "checks": [], "data_ok": False, "deployment_allowed": False,
    }

def record_trade(pf, action, fund_code, amount_or_shares, note="", **kwargs):
    """记录一笔交易并更新所有关联数据。

    Args:
        pf: portfolio dict
        action: 'buy' | 'sell' | 'plan'
        fund_code: 基金代码
        amount_or_shares: 买入金额(元) 或 卖出份额数(当 unit='shares'时)
        note: 备注
        **kwargs: unit='shares' 表示按份额卖出, nav=净值(用于算份额)

    Returns: 更新后的 pf
    """
    today = date.today().strftime('%Y-%m-%d')

    if action == 'plan':
        # 添加待执行计划
        pf.setdefault('pending_plans', []).append({
            "fund_code": fund_code,
            "fund_name": kwargs.get('fund_name', fund_code),
            "direction": kwargs.get('direction', 'buy'),
            "target": amount_or_shares,
            "executed": 0,
            "remaining": amount_or_shares,
            "status": "pending",
            "condition": note,
            "created": today,
            "note": kwargs.get('plan_note', ''),
        })
        pf['action_log'].insert(0, {
            "date": today, "action": f"📋 计划 {fund_code} {kwargs.get('direction','buy')} ¥{amount_or_shares:,}",
            "fund": fund_code, "reason": note,
        })
        return pf

    if action == 'buy':
        for h in pf['holdings']:
            if h.get('fund_code') == fund_code:
                amount = amount_or_shares
                nav = kwargs.get('nav') or h.get('nav', 1)
                total_assets = pf.get('total_assets', pf['cash'])

                # ── 硬约束：现金下限（v1.2 分层现金储备）──
                # 下限随"市场极端程度"分层放宽：L0 10% / L1 7% / L2 4% / L3 0%
                # 判定由 cash_reserve 提供（数据不可得时保守回退 L0）。
                base_floor_pct = TRADING_CONFIG["position"]["min_cash_pct"]
                if kwargs.get('cash_floor_pct') is not None:
                    min_cash_pct = float(kwargs['cash_floor_pct'])
                    reserve_state = None
                else:
                    reserve_state = fetch_reserve_state()
                    min_cash_pct = float(reserve_state.get("floor_pct", base_floor_pct))
                min_cash = total_assets * min_cash_pct / 100
                if pf['cash'] - amount < min_cash:
                    hint = ""
                    if reserve_state is not None and _cr is not None:
                        if reserve_state.get("deployment_allowed"):
                            hint = (f"（当前 {reserve_state.get('tier')}："
                                    f"{reserve_state.get('label')}）")
                        else:
                            nxt = _cr.next_tier_hint(reserve_state)
                            hint = f"（当前 {reserve_state.get('tier')}，{nxt}）" if nxt else ""
                    raise ValueError(
                        f"买入 ¥{amount:,.0f} 将使现金低于 {min_cash_pct:g}% 下限"
                        f"（v1.2 分层储备硬约束）{hint}"
                    )
                # 动用储备（买入后现金低于常规下限）→ 登记储备状态，供归还检查用
                cash_after = pf['cash'] - amount
                if min_cash_pct < base_floor_pct and cash_after < total_assets * base_floor_pct / 100:
                    rs = pf.setdefault('cash_reserve', {})
                    cur = rs.get('deployed_amount', 0.0) or 0.0
                    rs.update({
                        'tier': (reserve_state or {}).get('tier', rs.get('tier', 'L1')),
                        'floor_pct': min_cash_pct,
                        'deployed_amount': round(cur + amount, 2),
                        'returned_amount': rs.get('returned_amount', 0.0),
                        'returned': False,
                    })
                    pf['action_log'].insert(0, {
                        "date": today,
                        "action": f"🔓 动用储备 ¥{amount:,.0f}",
                        "fund": f"{h.get('fund_name','')} ({fund_code})",
                        "reason": (f"{rs['tier']} 级动用（现金下限放宽至 {min_cash_pct:g}%）；"
                                   f"{'；'.join((reserve_state or {}).get('matched', []))}；"
                                   f"退出触发区间即归还（不看盈亏）"),
                    })

                # ── 参考线：板块/主题超线必须填写理由（v1.1）──
                over_lines = []
                sector_after_pct = ((h.get('amount', 0) + amount) / total_assets * 100) if total_assets else 0
                max_sector_pct = TRADING_CONFIG["position"]["max_sector_pct"]
                if sector_after_pct > max_sector_pct:
                    over_lines.append(f"板块 {h.get('sector', '')} {sector_after_pct:.1f}% > {max_sector_pct}%")
                theme = h.get('theme')
                themes_cfg = (pf.get('position_config') or {}).get('themes', {})
                if theme:
                    theme_limit = themes_cfg.get(theme, {}).get('max_exposure', 0.30) * 100
                    theme_amount = sum(
                        x.get('amount', 0) for x in pf.get('holdings', []) if x.get('theme') == theme
                    )
                    theme_after_pct = ((theme_amount + amount) / total_assets * 100) if total_assets else 0
                    if theme_after_pct > theme_limit:
                        over_lines.append(f"主题 {theme} {theme_after_pct:.1f}% > {theme_limit:.0f}%")
                if over_lines and not note:
                    raise ValueError(
                        f"超参考线加仓必须填写理由（引用 Thesis）：{'; '.join(over_lines)}"
                    )

                # 更新金额和成本
                h['amount'] = round(h['amount'] + amount, 2)
                h['cost_basis'] = round(h.get('cost_basis', 0) + amount, 2)
                # 更新份额
                if nav > 0:
                    add_shares = round(amount / nav, 2)
                    h['shares'] = round(h.get('shares', 0) + add_shares, 2)
                # 重算持有收益
                h['holding_return'] = round(h['amount'] - h['cost_basis'], 2)
                if h['cost_basis'] > 0:
                    h['holding_return_pct'] = round(h['holding_return'] / h['cost_basis'] * 100, 2)

                pf['cash'] = round(pf['cash'] - amount, 2)
                entry = {
                    "date": today, "action": f"🟢 买入 ¥{amount:,}",
                    "fund": f"{h.get('fund_name','')} ({fund_code})", "reason": note,
                }
                if over_lines:
                    entry["over_reference"] = True
                    entry["over_lines"] = over_lines
                pf['action_log'].insert(0, entry)
                break

    elif action == 'sell':
        unit = kwargs.get('unit', 'shares')
        for h in pf['holdings']:
            if h.get('fund_code') == fund_code:
                if unit == 'shares':
                    sell_shares = amount_or_shares
                    nav = kwargs.get('nav') or h.get('nav', 1)
                    sell_amount = round(sell_shares * nav, 2)
                    old_shares = h.get('shares', 0)
                    old_cost = h.get('cost_basis', 0)
                    if old_shares > 0:
                        cost_per_share = old_cost / old_shares
                        h['shares'] = round(old_shares - sell_shares, 2)
                        h['cost_basis'] = round(h['shares'] * cost_per_share, 2)
                    h['amount'] = round(h['amount'] - sell_amount, 2)
                else:
                    sell_amount = amount_or_shares
                    h['amount'] = round(h['amount'] - sell_amount, 2)

                h['holding_return'] = round(h['amount'] - h.get('cost_basis', 0), 2)
                if h.get('cost_basis', 0) > 0:
                    h['holding_return_pct'] = round(h['holding_return'] / h['cost_basis'] * 100, 2)

                pf['cash'] = round(pf['cash'] + sell_amount, 2)
                pf['action_log'].insert(0, {
                    "date": today, "action": f"🔴 卖出 ¥{sell_amount:,.0f}",
                    "fund": f"{h.get('fund_name','')} ({fund_code})", "reason": note,
                })
                break

    # 更新待执行计划
    for p in pf.get('pending_plans', []):
        if p.get('fund_code') == fund_code and p['status'] == 'pending':
            p['executed'] = round(p['executed'] + amount_or_shares, 2)
            p['remaining'] = round(p['target'] - p['executed'], 2)
            if p['remaining'] <= 0:
                p['status'] = 'done'

    # 重算板块和总资产
    sectors = defaultdict(lambda: {'funds':[], 'total_amount':0})
    for h in pf['holdings']:
        if h.get('status') == 'sold' or h['amount'] <= 0: continue
        s = h.get('sector', '其他')
        sectors[s]['total_amount'] += h['amount']
        did = h.get('dashboard_id','')
        if did and did not in sectors[s]['funds']:
            sectors[s]['funds'].append(did)

    total_holdings = sum(s['total_amount'] for s in sectors.values())
    pf['total_assets'] = round(pf['cash'] + total_holdings, 2)
    for s, info in sectors.items():
        info['pct'] = round(info['total_amount'] / pf['total_assets'] * 100, 1)
    pf['sector_allocation'] = dict(sectors)
    pf['updated'] = today

    return pf


if __name__ == '__main__':
    with open(os.path.join(DATA_DIR, 'portfolio.json'), encoding='utf-8') as f:
        pf = json.load(f)

    if len(sys.argv) < 5:
        print("用法: python3 record_trade.py <buy|sell|plan> <fund_code> <amount> <note> [nav=...]")
        sys.exit(1)

    action = sys.argv[1]
    fund_code = sys.argv[2]
    amount = float(sys.argv[3])
    note = sys.argv[4]
    kwargs = {}
    for a in sys.argv[5:]:
        if '=' in a:
            k, v = a.split('=', 1)
            kwargs[k] = float(v) if v.replace('.','').isdigit() else v

    try:
        pf = record_trade(pf, action, fund_code, amount, note, **kwargs)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    write_json(os.path.join(DATA_DIR, 'portfolio.json'), pf)

    print(f'✅ {action} {fund_code} ¥{amount:,.0f} — {note}')
    print(f'   现金: ¥{pf["cash"]:,.2f} | 总资产: ¥{pf["total_assets"]:,.0f}')
