"""统一交易记录入口。所有买入/卖出通过此函数，确保 shares/cost/plans 同步更新。

用法:
  python3 record_trade.py buy 019633 3000 "放量确认，主仓加码"
  python3 record_trade.py sell 020608 965.70 shares "机器人减仓"
  python3 record_trade.py plan 011370 buy 2000 "明天不大涨" "CPO加仓计划"

也可以在代码中调用 record_trade()。
"""
import json, os, sys
from config import DATA_DIR
from datetime import date
from collections import defaultdict
from storage import write_json

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
                pf['action_log'].insert(0, {
                    "date": today, "action": f"🟢 买入 ¥{amount:,}",
                    "fund": f"{h.get('fund_name','')} ({fund_code})", "reason": note,
                })
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
        if p['fund_code'] == fund_code and p['status'] == 'pending':
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

    pf = record_trade(pf, action, fund_code, amount, note, **kwargs)

    write_json(os.path.join(DATA_DIR, 'portfolio.json'), pf)

    print(f'✅ {action} {fund_code} ¥{amount:,.0f} — {note}')
    print(f'   现金: ¥{pf["cash"]:,.2f} | 总资产: ¥{pf["total_assets"]:,.0f}')
