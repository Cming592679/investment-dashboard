# tier / status 语义统一 — 迁移方案（草案，未实施）

> 状态：**仅方案**。本文件不改变任何代码或数据语义，等待用户确认后作为独立 P1 提交实施。
> 依据：`INVESTMENT_RULEBOOK_DRAFT.md` v1.1（Tier = 证据成熟度授权档）+ `RULEBOOK_MAPPING_AUDIT.md` §3.4/3.5。

---

## 1. 现状（旧语义，实测读取 2026-08-17 portfolio.json）

### 1.1 字段现状

| 字段 | 观测到的值 | 当前含义（旧） |
|---|---|---|
| `status` | active / core / sold / sell_pending / non_investment / watch | 生命周期状态，但混入了档位（core/watch）与超限标记（overweight） |
| `tier` | core / active / watch / overweight / sold | 档位，但 overweight 同时出现在 status 与 tier |
| `evidence_stage` | core / verify / watch / explore | v1.1 新字段，真实持仓已标注 |

### 1.2 字段消费方清单（迁移必须保持兼容）

| 调用方 | 读取字段 | 用途 |
|---|---|---|
| `app.py`（约 1846/1924 行） | `status` | 过滤 active 持仓（排除 sold/non_investment） |
| `app.py`（约 1984-1985 行） | `evidence_stage` | 行动计划显示档位上限（tier_cap_pct） |
| `position_engine.py`（89/103 行） | `status`、`tier` | 过滤持仓；`tier != 'overweight'` 决定 base=0.08 |
| `fund_nav_fetcher.py`（171/208/250/262/276/295 行） | `status` | sold/active 过滤、净值更新范围 |
| `record_trade.py`（142-151 行） | `status`、pending_plans.status | 卖出后置 sold；计划执行状态 |
| `intraday_check.py`（170/214 行） | `status` | 排除 sold/non_investment/sell_pending |
| `portfolio_schema.py`（58 行） | `evidence_stage` | 枚举校验 {explore,watch,verify,core,""} |

> `trading_rules.py` 当前不消费持仓 status/tier（仅 kdj.status 等技术状态），迁移不涉及。

---

## 2. 目标语义（v1.1）

### 2.1 三个字段各管一件事

| 字段 | 语义 | 允许值 |
|---|---|---|
| `status` | **生命周期**：这只基金现在处于哪个阶段 | active / sell_pending / sold / non_investment / observe |
| `tier` / `evidence_stage` | **证据成熟度授权档**（v1.1 正式字段为 evidence_stage） | explore ≤3% / watch ≤5% / verify ≤8% / core ≤15% |

- Tier 与 status 正交：sold 的基金可以保留历史 evidence_stage 供复盘，但不参与仓位计算。
- `overweight` 不是档位也不是生命周期，而是"敞口超参考线"的**瞬时状态**，由敞口计算层动态判定（`_compute_exposure` 已实现），不再落在 tier/status 上。
- `observe`：Thesis 证伪 Exit 后的观察期（1 个月，Rulebook A3），属于生命周期状态。

### 2.2 旧 → 新 映射

| 旧 `status` | 新 `status` | 旧 `tier` | 新 `evidence_stage` |
|---|---|---|---|
| active | active | active | verify（默认档） |
| core | active | core | core |
| watch | active | watch | watch |
| overweight | active | overweight | core（超限是状态；档位回退到证据成熟度） |
| sell_pending | sell_pending | sold | 保留历史值 |
| sold | sold | sold | 保留历史值（不参与计算） |
| non_investment | non_investment | non_investment | ""（不参与） |

> 已存在 `evidence_stage` 的持仓**以 evidence_stage 为准**，不做二次推断；映射仅用于缺失字段的补全。

---

## 3. 迁移步骤（实施时按此执行）

1. **dry-run 脚本**：读取 portfolio.json，输出每只持仓的旧值 → 新值映射表，不写盘。
2. **用户确认映射表**（尤其：active→verify 是否合适、overweight→core 是否接受）。
3. **数据归一化**：备份后按映射写回 `status` / `tier` / `evidence_stage`，`tier` 字段逐步废弃（保留兼容读取，写入时同步 evidence_stage）。
4. **代码收敛**：
   - `position_engine.py`：`tier != 'overweight'` 改为基于 `evidence_stage` 的档位上限；overweight 判定交给敞口层。
   - `portfolio_schema.py`：给 `status` 增加枚举校验（active/sell_pending/sold/non_investment/observe）。
   - `record_trade.py` / `fund_nav_fetcher.py` / `intraday_check.py`：status 过滤语义不变，仅枚举对齐。
5. **验证**：`python3 -m py_compile` + 启动冒烟 + `/api/portfolio`、`/api/action-plan` 输出与迁移前逐字段对比（除字段名外无差异）。
6. **回滚**：数据层用备份恢复 portfolio.json；代码层 git revert 对应 commit。

---

## 4. 风险与注意事项

- **行为变化点只有一个**：position_engine 的 base 判定从"是否 overweight"改为档位上限。当前持仓里 tier=overweight 的只有军工电子（evidence_stage=core），映射后 base 不变，无实际影响。
- 不在本次迁移中引入新的档位/观察仓逻辑（Explore 试探仓、Observe 状态由后续 P1 承载）。
- 个人数据红线：迁移脚本运行前必须 `backup.py`；portfolio.json 绝不入 Git。

## 5. 待用户确认

- [ ] active → verify 作为默认档位是否可接受
- [ ] overweight 从字段中移除、改由敞口层动态判定
- [ ] tier 字段是否彻底废弃（只保留 evidence_stage）
- [ ] observe 状态是否现在就加入 status 枚举（还是等证伪流程落地再引入）
