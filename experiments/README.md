# Investment Method Identification Experiment

> 阶段：Phase-1（结构识别 / Candidate Registry / 数据审计）。尚未进入 v2 设计，未改代码，未冻结任何参数。
> 起：2026-09-08。方法学输入为用户提供的《Market Regime / Risk Budget 方法论实验》全文。

## 红线

1. 本目录只放方法论、聚合结果与实验设计；**不放个人数据**（持仓/现金/逐笔流水）。
2. 个人级明细（操作分类台账、直觉日志原文、逐笔回测数据）放 `PERSONAL_DATA_DIR/experiments/`，不入 Git。
3. 所有结论必须带标签：`OBSERVED / HYPOTHESIS / DESIGN ASSUMPTION / VALIDATED / REJECTED / UNKNOWN`。
4. 回测遵守 decision-time only；无法保证时明确标记 `LOOK-AHEAD RISK`。
5. 参数版本必须可追溯（见 STRATEGY_REPLAY_RESULTS.md 模板）。

## 文件

- `MARKET_REGIME_EXPERIMENT.md` — 实验总纲：候选指标注册表、数据可用性、缺口、假设登记、停止条件。
- `STRATEGY_REPLAY_RESULTS.md` — 回测结果登记（E00 已归档）。
- `INTUITION_LOG.md` — 用户直觉记录模板（原文在个人数据目录）。
- `OVERRIDE_ANALYSIS.md` — 非正式规则操作的分类框架（明细台账在个人数据目录）。
- `EXPERIMENT_DECISION_LOG.md` — 实验决策日志。

## 当前状态（2026-09-08）

- E00 零费用 5.5 周回测已归档（标记为有缺陷，不得引为结论）。
- Market Regime Candidate Registry v0.1 建立（全部 CANDIDATE / UNKNOWN）。
- 首批 INTUITION / OVERRIDE 样例已分类（个人数据目录）。
- E01-panel-v0.1 已拉取并落盘个人数据目录（2022-06→今，宽基+板块代理+基金净值）。
- 个人数据侧已建 `DATA_INCIDENT_LOG.md`（缺失/错位/修复记录）。
- E02 v0.1 指标筛查完成：趋势/广度对未来收益无预测力；波动率对 fwdDD 弱-中信号。
- E04/E06 v0.1 Risk Budget 回测完成：波动率降暴露作为独立择时层被 REJECT；
  恒定较低暴露列为 CANDIDATE（详见 RISK_BUDGET_RESULTS.md）。
- E05 v0.1 Global vs Theme 完成：全局条件化被 REJECT；主题级波动率预算 + 最短持有 30 天
  成为当前最强 CANDIDATE（Calmar 0.86，待 walk-forward 验证，详见 RISK_BUDGET_GLOBAL_VS_THEME.md）。
- E07 v0.1 walk-forward 完成：主题级波动率预算 + 最短持有通过样本外检验
  （OOS Calmar 1.95 vs BH100 1.45），参数重选无增量 → 采用固定默认参数
  （详见 WALKFORWARD_RESULTS.md）。
- E08 台账：38 张交易截图 OCR → 250 条去重条目（2026-05-14~09-09），
  基金名解析 47/48；FIFO 费用精算与持仓对账脚本已入库，
  明细与待确认清单在个人数据目录 `experiments/ledger/`（不入 Git）。
- E08 后续：修复台账解析 5 个 bug（去重含时间/清仓明细/A/C分离/撤单/名称解析），
  FIFO 实际费率 0.278%；成本敏感性复算强化了主题级预算结论。
- **收敛产物**：`V2_RULEBOOK_PROPOSAL.md`（候选，未冻结）。

## 阶段状态

第一阶段（方法识别实验）已收敛：核心结论为「主题级 Risk Budget + 30 天最短持有」是最强候选，
全局降暴露被排除；但样本不足、代理 ETF、格点假设，故**不建议冻结 v2**。
下一步：反事实交叉验证（用户新手期数据）+ 再积累一个周期后再决定。
- 待用户：提供 7/31→9/7 完整交易流水（截图/导出）；确认分析执行时段。
