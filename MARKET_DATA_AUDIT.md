# MARKET_DATA_AUDIT — 基金行情数据链路可靠性审计（P0-0）

> 状态：只读审计，未修改任何代码。
> 日期：2026-08-18
> 结论：当前系统的「昨日正式收益」与「今日盘中涨跌」都不可靠，且存在「估算/代理/官方」三类数据混用、静默 fallback 到旧值的问题。Rulebook v1.0 的 Price–Fundamental Divergence、RSI、Trend、涨幅透支、Daily 自动分类目前都建立在不可信输入上。

---

## 1. 数据链路总览（UI → API → service → source）

```
index.html / portfolio.html
   │  页面加载时 fetch
   ▼
/api/fund/<fid>      /api/portfolio       /api/action-plan       /api/intraday
   │ 缓存优先            │ 读 _cache + portfolio.json           │ 读 _cache
   ▼                     ▼
app._get_fund_response → app._fetch_one_fund
   │
   ├─ 官方净值收益: fund.eastmoney.com/pingzhongdata/{code}.js  (Data_netWorthTrend → equityReturn/时间戳)
   ├─ 盘中估值(一级): v1.apizero.cn/api/fund?action=estimate   (change_rate)
   ├─ 盘中估算(二级): app._weighted_proxy_estimate → yfinance 底层成分股加权
   └─ 盘中估算(三级): 基准ETF/指数 yfinance day_change_pct

portfolio.json 的 nav / nav_date / day_return_pct / daily_return
   ▲
   └─ 每日 20:00-20:02 scheduler → fund_nav_fetcher.update_portfolio_nav
        └─ hq.sinajs.cn/list=f_{code}（新浪收盘净值）
```

关键事实：**页面展示的实时判定与盘中涨跌，读的是进程内 `_cache`；该缓存只在每天 18:00-18:02 与启动预热时刷新一次**，交易时段内不会自动更新（除非手动 `/api/refresh?refresh=1`）。

---

## 2. 每个字段的最终来源

| 展示/存储字段 | 当前来源 | 类别 | 日期语义 | 更新时间语义 |
|---|---|---|---|---|
| 持仓 `nav`（当前净值） | 新浪 `hq.sinajs.cn` parts[1] | Official | 该基金最近一个已披露净值日 | 每日 20:00 一次性写入 |
| 持仓 `prev_nav`（昨日净值） | 新浪 parts[3] | Official | 上一净值日 | 同上 |
| 持仓 `day_return_pct`（昨日收益率） | 本地计算 `(nav-prev_nav)/prev_nav` | Official(派生) | 上一净值日 | 同上 |
| 持仓 `daily_return`（昨日收益额） | `amount × day_return_pct/100` | Official(派生) | 上一净值日 | 同上 |
| 汇总 `daily_return`（页面「昨日收益」） | 各持仓 `daily_return` 求和 | 混合 | **各基金净值日不一致** | 20:00 |
| dashboard `fund_return_pct` | 东财 pingzhongdata `Data_netWorthTrend[-1].equityReturn` | Official | 最近净值日 | 缓存刷新时 |
| dashboard `fund_nav_date` | 东财时间戳 → `strftime('%m/%d')` | Official | **丢年份** | 缓存刷新时 |
| dashboard `fund_return_est` | apizero `change_rate` → 代理加权 → 基准ETF | Estimated | 当日盘中 | 缓存刷新时 |
| 持仓 `live_return_pct`（页面「今日涨跌」） | `fund_return_est` 否则 `fund_return_pct` | **混用** | 不明确 | 缓存刷新时 |

---

## 3. 数据源清单

| 数据源 | endpoint | 关键参数 | 返回字段 | 更新频率 | token | 限流 | 盘中 | 历史NAV | QDII/海外 |
|---|---|---|---|---|---|---|---|---|---|
| 新浪财经 | `hq.sinajs.cn/list=f_{code}` | 基金代码 + Referer | name/nav/prev_nav/date/acc_nav | 收盘后 | 无 | 无(需Referer) | 否 | 否 | 部分(净值日期随基金自身披露) |
| 东方财富 pingzhong | `fund.eastmoney.com/pingzhongdata/{code}.js` | 基金代码 | Data_netWorthTrend(y/x/equityReturn) | 收盘后 | 无 | 无 | 否 | 是(数组) | 是(延迟更大) |
| 东方财富 f10/lsjz | `api.fund.eastmoney.com/f10/lsjz` | fundCode/pageIndex/pageSize + Referer | FSRQ/DWJZ/LJJZ/JZZZL | 收盘后 | 无 | 无 | 否 | 是 | 是 |
| apizero | `v1.apizero.cn/api/fund?action=estimate&code={code}` | 基金代码 | net_value/estimate/change_rate/nav_date/update_time | 盘中分钟级 | 无(匿名) | 50次/天,60s缓存 | 是 | 否 | 有限 |
| yfinance | `yf.Ticker(...).history` / `yf.download` | 股票/指数代码 | Close/High/Low/Volume/派生指标 | 盘中/日线 | 无 | 无明确 | 是(美股) | 是 | 是(美股标的) |

---

## 4. 实测记录（2026-08-18 10:04-10:05 实际请求）

| 基金 | 数据源 | 返回 NAV | 返回涨跌 | 数据日期 | 结果 |
|---|---|---|---|---|---|
| 019633 国泰半导体设备(A股) | 新浪 | 3.0815 | (prev 2.9386) | 2026-08-17 | ✅ 官方净值已有 8/17 |
| 019633 | 东财 pingzhong | 3.0815 | equityReturn 4.86% | 2026-08-17 | ✅ 与新浪一致 |
| 019633 | 东财 lsjz | 3.0815 | JZZZL 4.86% | 2026-08-17 | ✅ 三方一致 |
| 019633 | apizero | — | — | — | ❌ HTTP 502 失效 |
| 100055 富国(QDII) | 新浪 | 5.4292 | (prev 5.37) | 2026-08-14 | ✅ 官方净值停 8/14(QDII 延迟) |
| 100055 | 东财 pingzhong | 5.4292 | equityReturn 1.10% | 2026-08-14 | ✅ 一致 |
| 006479 纳斯达克(QDII) | 新浪 | 8.1879 | (prev 8.1995) | 2026-08-14 | ✅ 官方净值停 8/14 |
| 006479 | 东财 | 8.1879 | -0.14% | 2026-08-14 | ✅ 一致 |
| 006479 | apizero | — | — | — | ❌ HTTP 502 |

结论：新浪与东方财富两个官方净值源一致、可靠；**apizero 盘中估值当前全线 502，不可用**。

---

## 5. 为什么「昨日收益」和「今日盘中涨幅」拿不到真实值

### 5.1 昨日正式收益

- 来源本身可靠（新浪收盘净值），但 `update_portfolio_nav` 是**每天 20:00 只跑一次、且不重试**。
- 实测 019633 官方净值已更新到 8/17（+4.86%），但 portfolio.json 里仍停在 8/14（nav 2.9386）。说明 8/17 20:02 那次更新时，部分基金 8/17 净值还没披露，系统抓到了旧的 8/14，之后没有补拉。
- 汇总「昨日收益」把不同净值日（8/17、8/14、8/13、8/11）的日收益直接相加，语义混乱。

### 5.2 今日盘中涨幅

- 一级真实估值源 apizero 当前 502，等于失效。
- 失效后静默降级为「代理股票加权(yfinance)」或「基准ETF」，甚至最终回退到 `fund_return_pct`（官方净值收益），却仍显示在「今日涨跌」列。
- 页面读的是 `_cache`，缓存一天只在 18:00 刷一次，盘中不更新，所以「今日涨跌」通常不是当下数据。

---

## 6. 严重问题清单

1. ❌ **静默 fallback 到旧值**：`live_return_pct = est if est is not None else nav_ret`，无盘中估值时直接把官方净值收益塞进「今日涨跌」。
2. ❌ **缓存冒充实时**：`/api/portfolio`、`/api/action-plan`、监控页都读 `_cache`，一天仅 18:00 刷新一次。
3. ❌ **NAV 日期错位**：019633 官方已有 8/17，本地仍 8/14，因 20:00 单次更新无重试。
4. ❌ **QDII 时区/延迟未区分**：100055/006479 官方净值停在 8/14（QDII T+2），与 A股基金日期混在一起求和。
5. ❌ **fund_nav_date 丢年份**：`%m/%d` 格式化 + `is_today_nav` 只比月/日，跨年或语义易错。
6. ❌ **估算/官方/代理混用**：`fund_return_pct`(Official) 与 `fund_return_est`(Estimated) 在 UI 层被同一个「今日涨跌」字段消费。
7. ❌ **非交易日无日历判断**：周末/节假日可能把上一交易日数据当作当日。
8. ❌ **API 返回标的行情而非基金行情**：代理估算是底层股票/指数的市场涨跌，不是基金净值。
9. ❌ **数据失败静默降级**：多处 `except: pass`，失败时无任何 freshness 标记。

---

## 7. Official / Market / Estimated 三态

| 类别 | 含义 | 当前对应字段 | 允许用途 |
|---|---|---|---|
| **Official** | 基金官方净值/日收益/净值日/发布时间 | 新浪 nav/prev_nav/date、东财 equityReturn/nav、lsjz | 昨日正式收益、持仓估值、验证回填 |
| **Market** | 底层市场实时价格/涨跌/时间戳/交易时段 | yfinance stock/index 的 price/day_change_pct | 仅作代理估算输入，不直接当基金涨跌 |
| **Estimated** | 基于底层市场估算的基金盘中收益 | apizero change_rate、代理加权、基准ETF | 仅盘中参考，必须带 estimate timestamp/method/status |

三者不可混用。当前违反点：`live_return_pct` 把 Estimated 与 Official 塞进同一字段，且无 method/timestamp/status。

---

## 8. 分基金类型

| 类型 | 昨日正式收益来源 | 今日盘中涨跌是否存在官方数据 | 盘中应采用的代理 |
|---|---|---|---|
| A股基金 | 新浪/东财收盘净值（T+1 当晚） | 有（apizero 等第三方盘中估值，非官方） | apizero → 底层持仓加权 → 基准ETF |
| 港股相关基金 | 官方净值 T+1/T+2 | 无官方盘中估值 | 恒生成分/港股持仓加权 |
| 美股相关基金 | 官方净值 T+2（美股时区延迟） | 无官方盘中估值 | 美股持仓加权（注意时区：当日A股盘中对应前一日美股收盘） |
| QDII | 官方净值 T+2 或更久 | 无 | 底层海外持仓/基准指数，但需标注时区错位 |
| 全球科技基金 | 官方净值 T+2 | 无 | 底层美股科技持仓加权 |
| 黄金/商品 | 官方净值 T+1/T+2 | 无 | 底层金价/商品价格 |
| 债券基金 | 官方净值 T+1 | 无（债基盘中意义小） | 无需盘中，只展示官方净值 |

---

## 9. Reliability Matrix

| 数据字段 | 当前来源 | 当前是否可靠 | 数据日期语义 | 更新时间语义 | 是否实时 | 问题 |
|---|---|---|---|---|---|---|
| 昨日正式收益(nav/daily_return) | 新浪 | 源可靠，写入不可靠 | 各基金净值日不一致 | 20:00 单次 | 否 | 漏晚披露基金、无重试 |
| 今日盘中涨跌(live_return_pct) | apizero→proxy→官方 | ❌ | 不明确 | 缓存刷新时 | 否 | 三态混用、apizero 502 |
| 实时判定(conclusion/emoji) | 决策树+缓存 | 部分 | 基于缓存指标 | 18:00/启动 | 否 | 缓存一天一刷 |
| 领先指标 | 手动 config.py | 人为维护 | 各自 update_cycle | 手动 | 否 | 依赖人工更新 |

---

## 10. P0-0 修复方案（最小）

### 10.1 数据模型：三态分离

```json
{
  "official": {"nav": 3.0815, "prev_nav": 2.9386, "nav_date": "2026-08-17", "return_pct": 4.86, "published_at": "..."},
  "market":  {"ticker": "...", "price": 0, "change_pct": 0, "timestamp": "...", "session": "open/closed"},
  "estimated": {"value": 0, "method": "apizero|proxy|benchmark", "timestamp": "...", "status": "ok|stale|unavailable"}
}
```

### 10.2 最小修复步骤（进入实现后再做，本次不写代码）

1. 拆分 UI 字段：新增「官方净值收益」与「盘中估算涨跌」两个独立列，删除现有混用的「今日涨跌」。
2. 20:00 净值更新增加补拉：20:30 / 21:00 对「净值日不是今天的基金」重试一次；仍失败则保留旧值但标记 `nav_stale=true`。
3. `fund_nav_date` 存完整 `YYYY-MM-DD`，去掉 `%m/%d` 与 `is_today_nav` 的月/日比较。
4. 盘中估值三级 fallback 全部标注 `est_source` 与 `est_time`，绝不复用 `fund_return_pct` 当盘中值。
5. apizero 502 时显示「盘中估值不可用」，不静默回退到官方收益。
6. 缓存刷新：交易时段（A股 9:30-15:00）增加按需刷新或整点刷新，并记录 `fetched_at` 让 UI 展示数据新鲜度。
7. QDII/海外基金单独标记净值延迟窗口（T+2），不参与 A股同日的「昨日收益」求和语义。

### 10.3 推荐数据源与 fallback

- 官方净值主源：新浪 `hq.sinajs.cn`（快）+ 东方财富 `lsjz`（可回溯，交叉校验）。
- 盘中估算主源：apizero（恢复后）；备用：持仓加权代理(yfinance)。
- fallback 链（必须带 method 标记）：apizero → weighted_proxy → benchmark；全部失败 → 显式「不可用」，不回退官方收益冒充盘中。

### 10.4 freshness 判定与 stale 处理

- 每个值必须能回答：是什么、对应哪一天、几点抓到、来自哪里、Official/Market/Estimated。
- A股：`nav_date` 应为最近交易日；超过 1 个交易日 → stale。
- QDII/美股：允许 T+2 窗口；超过 → stale。
- stale 数据：UI 标注「数据截至 YYYY-MM-DD」，禁止作为 Price–Fundamental Divergence / RSI / Trend / 涨幅透支 / Daily 自动分类的输入参与决策。
