# Market Regime / Risk Budget 实验总纲

## 1. 目标

回答三个问题，然后才谈 v2：

1. “我觉得市场变危险了”——我到底在看什么？
2. 这些东西历史上是否真的有信息？
3. 风险增加时该降多少暴露，这个数字为什么是这个数字？

本轮不产出规则，只产出：**哪些已验证、哪些仍是候选、哪些应该排除**。

## 2. 候选架构（仅目标，不实现）

```text
Thesis → Core Position
        → Market Regime（Trend / Breadth / Volatility / Leadership）
        → Risk Budget
        → Asset/Theme State → Tactical Adjustment
        → Target Position → Portfolio Constraints → Human Confirm
```

现有系统与之重叠部分：Thesis/Tier、板块级 Regime、L1-L4、仓位参考线。
现有系统缺失部分：组合级 Regime、Risk Budget、统一仲裁。
本轮要验证的是：**缺失的部分是否真的增加价值，还是伪复杂度**（V2_REVIEW 的警告作为对照组保留）。

## 3. Market Regime Candidate Registry v0.1

> 状态约定：全部为 CANDIDATE / UNKNOWN；不赋权重；不预设领先性。

| 维度 | 候选指标 | 本地历史（7/6→9/6） | 需外部长历史 |
|---|---|---|---|
| A Trend | 指数 vs MA20/50/200；MA20/50 斜率；20D/60D momentum | 指数快照部分字段 | ✅ 2023+ |
| B Breadth | 成分 >MA20/50/200 比例；涨跌家数；新高新低 | 成分 >MA50、RSI（快照内） | ✅ 全市场广度 |
| C Volatility | 20D realized vol；ATR/price；vol percentile；扩张速度 | 无 | ✅ 从 K 线可算 |
| D RS/Leadership | 风险资产 vs 大盘；成长 vs 防御；主题 vs 基准 | indices 字段部分可用 | ✅ |
| E Portfolio Breadth | 持仓主题 >MA50 比例 / RS>0 / RSI>50 / 回撤比例 | ✅ 7/6 起逐日可算 | 更早需回填 |

## 4. 数据可用性与缺口（摘要）

| 数据 | 范围 | 可用性 |
|---|---|---|
| history/ + predictions/ | 2026-07-06 → 09-06（54 条） | ✅ 板块结论/成分 RSI/MA50 |
| portfolio_history/ | 07-07 → 09-04（42 条） | 🟡 早期只含部分基金 |
| 每日备份 portfolio.json | 08-17 → 09-06 | ✅ 完整账；⚠ 部分日总资产被净值错位 bug 污染 |
| 基金净值（已抓 8+1 只） | 07-30 → 09-04 | ✅ 未落盘，待转正式实验数据 |
| 指数/ETF 长历史 | 未拉取 | 待用户确认范围 |

关键缺口：7/31 现金与完整持仓缺失；action_log 早段不全；8/17 前无完整账；
净值错位 bug 使备份总资产曲线不可直接当真实收益；样本仅 2 个月，覆盖不了 Regime A–F。

> 更新（2026-09-08）：**E01-panel-v0.1 已落盘** 至 `PERSONAL_DATA_DIR/experiments/market_data/`
> （klines.json / fund_navs.json / manifest.json，均不入 Git）。范围：6 个宽基指数 + 7 只板块/海外代理 ETF
> 2022-06→今（MA200 预热），18 只相关基金净值（部分 C 类份额成立晚，2023 段需用代理 ETF）。
> 缺口：全市场涨跌家数/新高新低无现成长历史源；021169 仅 2026-04 起。
> 明细数据状态见个人数据目录 `DATA_INCIDENT_LOG.md`。

## 5. 假设登记（示例）

- `OBSERVED` 2026-07-31→09-04 零费回测：持有 +2.65% / ±5% +6.00% / 80-20 +3.09% / ±3% +6.40%（有 LOOK-AHEAD RISK 与零费假设，见 STRATEGY_REPLAY_RESULTS.md E00）。
- `HYPOTHESIS` 波段收益主要来自回撤管理而非方向判断（待 E04 验证）。
- `HYPOTHESIS` 组合自身广度（E）可能比单一指数更早反映风险扩散（待 E02 验证）。
- `UNKNOWN` 全局 Regime 与主题 Regime 的分工（E05）。
- `UNKNOWN` Risk Budget 离散 vs 连续（E06）。

> E02 v0.1 更新（2026-09-08）：对未来收益，候选指标均无显著预测力；
> 对未来 20D 最大回撤，波动率类信号最一致（rho −0.23~−0.29，弱到中等）；
> 趋势/广度/RSI 高度冗余。详见 INDICATOR_SCREEN_RESULTS.md。

## 6. 实验队列

- E00 归档零费回测（有缺陷样本）— done
- E01 数据面板（范围待确认）
- E02 指标单变量筛查 + 相关性去重
- E03 Regime A–F 分段
- E04 模型 A–D Replay（含真实费用）
- E05 Global vs Theme
- E06 Risk Budget 映射
- E07 Override/Intuition 分类（首批样例已入个人数据台账）

## 7. 停止条件（对齐用户 §21）

结构明确 / Regime 有候选 / 覆盖多市场状态 / Budget 数字有来源 / 费用影响明确 /
Override 可解释 / 输出 KEEP-CANDIDATE-REJECT-UNKNOWN 清单。

满足后输出 `V2_RULEBOOK_PROPOSAL.md`，等用户确认，**禁止直接进入实现**。
