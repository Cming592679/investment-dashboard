# Rulebook v1.0 → Code → Data → UI 实现映射审计

> 审计日期：2026-08-17 · 性质：只读审计，不修改代码、不实现 v1.0 新功能、不修改投资规则、不重构 UI。
> 唯一基准：INVESTMENT_RULEBOOK_DRAFT.md v1.0（2026-08-17 冻结）。
> 范围：app.py / config.py / trading_rules.py / position_engine.py / record_trade.py / intraday_check.py / data_fetcher.py / fund_nav_fetcher.py / templates / static / portfolio.json / history / predictions / reviews / .claude skills。
>
> 状态图例：
> ✅ 已实现且符合 v1.0
> ⚠️ 已实现但语义不符合
> 🟡 部分实现
> 📦 仅数据存在（无逻辑）
> 🔗 代码存在但无调用链
> ❌ 完全缺失
> 🔥 与 v1.0 冲突的旧逻辑

---

## 0. 关键调用链事实（审计基础，已逐条核实）

| 事实 | 证据 |
|---|---|
| `/api/action` → `evaluate_daily_actions`（trading_rules.py）——**唯一调用链** | app.py:22, 1709 |
| `/api/intraday` → `intraday_check.run`（函数内 import） | app.py:1688 |
| `record_trade.py`：**app.py 不调用**，仅 CLI 入口 | rg 无命中 |
| `position_engine.py`：**app.py 不调用**，仅 CLI（`python3 position_engine.py [--save]`） | rg 无命中 |
| 快照 + 预测写入：`_save_daily_snapshot()`（18:00 调度）→ history/<date>.json + predictions/<date>.json + _index.json | app.py:499-606 |
| 预测文件**只写不回填实际结果** | app.py:558-583（无 actual 字段） |
| `weekly_surge` 配置存在但**无代码使用**（轨道 B 只实现 RSI+KDJ、Boll+MACD） | config.py:1208-1210；trading_rules.py 无引用 |
| `EXIT_LEVELS`（config.py:837）无任何 .py 引用（死代码） | rg 无命中 |
| `fund_weights.json` 无任何代码引用（HOLDING_WEIGHTS 才是生效源） | rg 无命中 |
| `portfolio.json.trade_rules` 无任何代码读取（死数据，但含用户实际使用的加权 RSI<50 规则） | rg 仅命中 position_config |
| 快照中 `score` 恒为 0（决策树返回 0），但仍被存储、复盘读取、UI 展示 | app.py compute_assessment；history/2026-08-14.json |
| 写接口 `/api/portfolio/update` 直接 `pf.update(request.json)`，无校验 | app.py:1799-1807 |
| skills（technical-check / serenity-bottleneck-hunter）是对话层调用链，非系统代码调用 | .claude/skills/ |

---

## 1. 规则逐项映射（按 v1.0 章节）

### 1.1 元规则（§0）

| v1.0 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| M1 账户回撤 ≠ 卖出；无熔断 | 无熔断逻辑 | ✅ | 现状即符合（无需实现）；回撤数据 📦 存在于 portfolio_history/snapshot |
| M2 损失最小化优先 | — | 🔗 | 原则层无代码承载；对应 P1-2 硬约束层（待建） |
| M3 Price–Fundamental Divergence | compute_assessment（Layer1-3 + 量能分支）、trading_rules L1-L4 | 🟡 | 有"信号分层"雏形，但无 v1.0 六类背离分类输出 |
| M4 禁止加仓 ≠ 必须卖出 | `_trend_filter_pass` 只影响买入 | ✅ | 符合（趋势过滤只禁买不触发卖） |
| M5 证伪 = 自动 Exit | BOTTLENECK_DISRUPTION → Structural → `_check_sell_stop` | 🟡 | 信号层有（结构性卖出建议）；无"事件驱动强制建议"承载（pending_plans 可扩展）；系统本就全人工，无自动交易 ✅ |
| M6 验证目的 = 为什么错了 | `_generate_monthly_review` | 🟡 | 有统计无归因（Beta/Alpha/仓位/纪律分类缺失） |
| M7 未验证不进核心仓 | portfolio `tier` 字段 | ⚠️ | tier 存在但语义是"角色/状态"，非"证据成熟度"；无档位机制 |
| M8 优先收敛已有规则 | — | ✅ | 方法论；本条即审计本身 |
| M9 不引入 optimizer 等 | 现状无 | ✅ | 无冲突 |
| M10 数字参数 Candidate | config/portfolio 数值 | ⚠️ | 部分已冻结数字（B6/B7）在 TRADING_CONFIG 存在但语义/来源不同，见 §2 |
| M11 背离处置分级 | — | ❌ | 无实现 |
| M12 Trend Gate 默认过滤器 | `_trend_filter_pass`（≥50% 成分股 MA20>MA60 才可买） | ⚠️ | **已实现但语义不符合**：当前是绝对硬否决，无默认过滤器/三档分级/人工豁免 |
| M13 总原则（机器发现/人解释/系统约束记录/证伪强制） | 健康检查/记录有部分 | 🟡 | 数据采集部分在；"发现与解释分离"无实现 |

### 1.2 Objective（10.1）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| 损失最小化优先 | — | 🔗 | 原则层 |
| 收益最大化在约束内 | — | 🔗 | 原则层 |
| 机会 = 背离 | — | ❌ | 无承载 |
| 把"何时重新认真思考"系统化 | 健康检查/事件倒计时 | 🟡 | 雏形在 |
| 衡量标准（候选） | review 有累计/对照统计 | 🟡 | 无 Sortino/Calmar |

### 1.3 Thesis / Edge（10.2 / 10.3）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| 每板块 Thesis 卡 | DESIGN.md 板块拆解 + CYCLE_COUNTER_HYPOTHESIS + portfolio notes | 📦 | 素材分散存在，无 thesis/ 目录承载 |
| 无 Thesis 不进档 | — | ❌ | 无档位机制 |
| Edge 可证伪机制 | BOTTLENECK_DISRUPTION（status: none/watching/breakthrough）+ LEADING_INDICATORS trend + KEY_DATES result | ✅ | 数据承载齐备，可机械检查 |
| 证伪条件命中 → 不可协商 Exit | Structural → sell_stop | 🟡 | 信号层有；无 Observe 状态 |

### 1.4 Signal（10.4）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| Signal = 领先指标 + 价格 + 背离组合 | LEADING_INDICATORS ✅ + 价格数据 ✅ | 🟡 | 组合分类（②~⑥）无实现 |
| RSI 仅作输入（B12） | `_get_rsi_tier_coefficient` 直接决定买入金额系数；`_weighted_rsi`（intraday_check）已有加权 RSI 计算 | ⚠️ | **已实现但语义不符合**：trading_rules 让 RSI 单独产出仓位系数；加权 RSI 计算承载 ✅ 可复用 |
| 指标过期提醒 | `check_indicator_staleness` + /api/health + UI 圆点 | ✅ | 符合 |
| 价格是输入 | 决策树 Layer1/量能分支 | 🟡 | 有雏形 |
| Daily 发现分类 | — | ❌ | 无 |
| 基本面明显改善人工判断（C19） | LEADING_INDICATORS trend 数据可支撑 | 📦 | 数据在，分类逻辑无 |
| 大幅回调提示（C20） | RSI/MA/回撤数据可计算 | 📦 | 数据在，提示逻辑无 |

### 1.5 Prediction（10.5）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| 方向+幅度+时间+证伪 | predictions/<date>.json：direction/label/confidence/timeframe/verify_date/watchpoints/indicator_predictions | ✅ | 承载齐备；**缺幅度区间**（🟡） |
| 背离场景记录（C18） | — | ❌ | 无 |
| 自动回填 | `_save_daily_snapshot` 只写不回填 | ❌ | 预测文件无 actual 字段 |
| 预测不进买卖 | 预测仅展示/复盘 | ✅ | 符合 |

### 1.6 Position Tier（10.6）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| Tier = 证据成熟度 | portfolio `tier` 字段（active/core/watch/overweight） | ⚠️ | 字段名存在但语义为"角色/状态"，且与 `status` 重叠混用（如 100055 status=core/tier=active） |
| 3/5/8/15 | holdings base/max（3%-20%） | 📦 | 数字存在但语义是"当前角色权重"，非档位上限 |
| Explore 试探仓 ≤3% | watch 档 base 3% | 📦 | 雏形数据在，无 Explore 概念、无"不因背离自动升级"约束 |
| 证伪→退档 | 结构性卖出建议 | 🟡 | 信号在，档位退出无 |
| 背离不改档位 | — | ❌ | 无档位机制 |

### 1.7 Position Sizing（10.7）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| 档内人工决定、不自动执行 | 系统无自动交易 | ✅ | 符合 |
| 禁 optimizer/协方差/连续权重 | 现状无 optimizer | ✅ | 符合 |
| 再平衡为主 + 涨幅透支 Reduce | 止盈轨道 A/B 存在；再平衡 ❌ | 🟡 | 轨道 A ✅；轨道 B 部分（RSI+KDJ、Boll+MACD ✅；weekly surge 🔗 未实现）；C 未实现 |
| RSI 仅输入 | 同上 S2 | ⚠️ | — |

### 1.8 Risk Limits（10.8）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| 单基金 15% / 板块 20% / 现金 10% | TRADING_CONFIG.position + `_check_buy_signals` 金额裁剪 + `_check_portfolio_health` | ✅ | 已实现于规则引擎 |
| 主题/瓶颈集群 30% | position_config.themes（35/25/15）+ BOTTLENECK_CLUSTERS（仅统计告警） | ⚠️ | 数据在，语义是"主题上限"且值不同；集群硬约束无 |
| 不设 Explore/Watch 合计上限 | 现状无 | ✅ | 符合 |
| 超限禁加仓 | 板块 20% 裁剪 ✅；主题无强制 | 🟡 | 板块/现金部分符合；主题缺 |
| 回撤 ≠ 卖出 | 无回撤卖出 | ✅ | 符合 |

### 1.9 Trend Gate（10.9）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| MA20<MA60 默认禁买 | `_trend_filter_pass`（≥50% 成分股） | ⚠️ | **绝对硬否决**，非默认过滤器 |
| 描述风险不判断 Thesis | 同上（机械否决） | ⚠️ | 冲突 |
| 三档分级（恶化/正常/改善+回调） | — | ❌ | 无 |
| 不触发卖出 | 趋势过滤只影响买入 | ✅ | 符合 |
| Reduce/Exit 不受限制 | 结构性卖出不检查趋势 | ✅ | 符合 |
| 证伪不受限制 | 同上 | ✅ | 符合 |
| 判据人工 | — | ❌ | 无 |

### 1.10 Divergence（10.10）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| ① Price-only 不行动 | Panic 卖出记录不执行；决策树对纯价格只记录 | 🟡 | 行为符合，无显式分类 |
| ②a 跌 + Thesis 完好 → Add 候选 | 决策树分支3/4（超卖观望/关注加仓）+ trading_rules RSI 超卖买入 | 🟡 | 雏形在；无候选队列 |
| ②b 涨 + Thesis 完好 → 观察 | 决策树默认安心持有 | 🟡 | 雏形 |
| ③a/③b 基本面恶化 → Reduce 候选 | L2 down → D 轨道卖出 | 🟡 | 雏形；无"价格×基本面"组合分类 |
| ④a 涨幅透支 → Reduce | 轨道 B（RSI+KDJ / Boll+MACD） | 🟡 | 部分；weekly surge 🔗 未实现 |
| ④b 深度回调 → Add 候选（C20） | — | ❌ | 无 |
| ⑤ 趋势背离三档（C15） | — | ❌ | 无 |
| ⑥ 证伪 → Exit | Structural → sell_stop | 🟡 | 信号层有；Observe 无 |
| 人工确认（D7） | 系统全人工 | ✅ | 符合 |
| 背离记录进验证（C18） | — | ❌ | 无 |

### 1.11 Invalidation / Add-Hold-Reduce-Exit / Verification / Cadence / Override（10.11-10.15）

| 规则 | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| 证伪→Exit→Observe（1 个月，A3） | Structural sell | 🟡 | 无 Observe 期承载 |
| 重评须重建 Thesis/Edge 证据 | — | ❌ | 无 |
| 部分证伪→Reduce | L2 down → 30% 减仓 | ✅ | 符合（比例按 B13 为 Candidate） |
| Add 条件链 | `_check_buy_signals`（叠层≥4 + L2≥0 + 趋势 + RSI + 上限） | 🟡 | 五项检查在 technical-check skill（🔗）；无档位/背离候选 |
| Hold 默认 | 无信号即不动 | ✅ | 符合 |
| Reduce 条件 | D 轨道 + 超限警告 | 🟡 | 符合雏形 |
| Exit 唯一证伪 | Structural sell | 🟡 | 建议层 |
| 验证四类归因 | — | ❌ | review 无归因 |
| 门禁 Candidate（B9） | `_check_tier1_gate`（90 天）作为 review 观察 | ✅ | 现状"观察非硬门禁"，符合 B9 |
| Daily 发现分类 | 健康检查/事件提醒 | 🟡 | 部分（提醒有，分类无） |
| Weekly 摘要（B11） | — | ❌ | 无 |
| Monthly 行动 + 再平衡 | review 自动生成 | 🟡 | 无行动候选队列、无再平衡 |
| 事件驱动 | pending_plans（部分硬编码日期） | 🟡 | 雏形 |
| Override 记录理由 | action_log.reason 字段 | 📦 | 字段可承载；机制无 |
| 月度点名 / 纪律风险提示 | — | ❌ | 无 |

---

## 2. 专项文件检查

### 2.1 trading_rules.py（978 行）——规则引擎
- **调用链**：仅 `/api/action`（app.py:1709）。🔗 之外无其他消费。
- **已实现**：Regime（Panic/Structural/Pre-Event）、L1-L4 叠层、买入链（叠层≥4 + L2≥0 + 趋势 + RSI 分级 + 板块/现金约束）、止盈 A/B、止损 D、冲突消解、portfolio_health。
- **与 v1.0 冲突（🔥）**：RSI 分级直接决定买入金额系数（B12 要求仅作 Signal 输入）；`_trend_filter_pass` 绝对否决（C15 要求默认过滤器）；L4 关键词判事件（B13 Candidate，未冻结）。
- **可复用（✅）**：Regime 判定、L2 瓶颈信号、结构性止损触发（Edge 证伪信号源）、板块/现金约束计算、冲突消解、L1-L4 作为 Signal 层输入。
- **需降级（⚠️）**：RSI 分级 → Signal 输入；趋势过滤 → 默认过滤器。

### 2.2 position_engine.py（224 行）——动态仓位模型
- **调用链**：仅 CLI。🔗 无 app 调用。
- **与 v1.0 冲突（🔥）**：输出**连续目标仓位**（v1.0 10.7.2 明确不引入连续权重）；RSI/趋势/基本面/波动率因子直接定仓位（RSI 应仅作输入）。
- **可复用（✅）**：theme exposure 计算 + 主题上限检查（可复用于 v1.0 R1/R3 集群硬约束）；因子思路可保留为研究工具（what-if）。
- **建议**：降级为研究工具，不进运行时；或删除连续权重输出。

### 2.3 record_trade.py（156 行）——交易记录
- **调用链**：仅 CLI。🔗 app.py 不使用。
- **冲突（🔥 P0-1）**：读 `DATA_DIR/portfolio.json`、写 `./portfolio.json`（当前目录）——CLI 从项目根运行会写错位置。
- **可复用（✅）**：记账逻辑（shares/cost_basis/pending_plans 同步、sector 重算）——P0-1 修复对象。
- **缺失**：交易唯一 ID、Override 字段（v1.0 10.15）。

### 2.4 config.py（1365 行）——配置/数据仓库
- **已实现（✅）**：FUNDS、LEADING_INDICATORS、KEY_DATES、CYCLE_ASSESSMENTS、BOTTLENECK_CLUSTERS、BOTTLENECK_DISRUPTION、SHARED_INDICATORS、TRADING_CONFIG、HOLDING_WEIGHTS、BOARD_FUND_MAP——v1.0 的 Signal/Edge/参数承载基本齐备。
- **死代码（🔥）**：EXIT_LEVELS（无引用）。
- **与 v1.0 需调整（⚠️ P1）**：TRADING_CONFIG 的 RSI tiers / trend filter / profit tiers（B12/C15/B13）；BOTTLENECK_CLUSTERS 可直接用作集群硬上限（复用）；`weekly_surge` 配置存在但轨道 B 未实现（C16，🔗）。
- **缺失**：档位参数、背离分类参数、Observe 期、涨幅透支阈值已有（C16，未使用）。

### 2.5 portfolio.json——持仓数据
- **已实现（✅）**：holdings（shares/cost_basis/amount/nav/status/tier/base/max/theme/notes）、cash、action_log（reason）、pending_plans、position_config。
- **语义不符合（⚠️）**：tier 与 status 重叠混用；position_config.themes（35/25/15）与 v1.0 集群 30% 语义不同。
- **死数据（📦）**：trade_rules——但其中"加权 RSI<50（early/mid）、<40（late）"是用户实际使用的规则（B12），应**转正**而非删除；其余成本/止盈条目按 B13 处理。
- **缺失（❌）**：evidence_stage（档位）、Explore 试探仓标记、背离记录、Override 记录、Observe 状态。

### 2.6 app.py（1848 行）——主应用
- **冲突（🔥）**：决策树"周期中后期 + 领先向好 + 暴跌 + 量能不明 → 安心持有"漏判；量能分支独立于主链且优先（结论被量能主导）；`score=0` 残留仍被快照/复盘/UI/预测 watchpoint 使用。
- **已实现（✅）**：健康检测、调度器、快照/预测写入框架（`_save_daily_snapshot`）、Tier-1 门禁（B9 观察）、复盘生成器骨架、API 层。
- **缺口（❌）**：背离分类、档位、Override、预测回填、写接口校验（⚠️）、storage 单写者（⚠️ P0-1）。

### 2.7 数据结构承载矩阵

| 载体 | 字段 | v1.0 承载 | 缺口 |
|---|---|---|---|
| history/<date>.json | date/fetched_at/funds{score(0),conclusion,emoji,details,fund_return_pct,stocks,indices}/predictions | 结论 + 价格（D1-D9 基础） | score 废弃字段 ⚠️；无背离/档位 ❌ |
| predictions/<date>.json | predictions{direction,label,confidence,timeframe,verify_date,reasons,watchpoints,indicator_predictions}+two_tier_predictions | Prediction（10.5.1）✅ | 无幅度区间、无 actual 回填 ❌ |
| reviews/*.md | Tier-1/Tier-2/对照/校准/板块走势 | 统计层 ✅ | 无归因（V1）❌ |
| portfolio.json | 见 2.5 | 持仓/日志 ✅ | 档位/背离/Override ❌ |
| .claude/skills | technical-check（五项检查）、serenity | 人工流程 ✅（对话层） | 非代码调用链 🔗 |

---

## 3. 最终重点输出

### 3.1 必须删除 / 降级的旧规则

**删除（死逻辑/死数据）：**
1. `EXIT_LEVELS`（config.py:837）——五级线性分级，无任何引用。
2. `fund_weights.json`——无引用，HOLDING_WEIGHTS 是生效源。
3. `score` 相关残留：index.html"逃跑指数"框、history chip 的 score/10、复盘评分表、`_generate_prediction` 的 score watchpoint（恒 0 导致"评分跌破 3"永远追加）。
4. portfolio.json `trade_rules` 死数据中除 B12 加权 RSI 外的条目（成本/止盈/入场清单未冻结部分）。

**降级（语义调整，非删除）：**
1. RSI 分级定买入金额（trading_rules）→ 仅作 Signal 输入（B12）。
2. 趋势过滤绝对否决 → 默认风险过滤器 + 三档分级（C15）。
3. position_engine 连续目标权重 → 研究工具（what-if），不进运行时（10.7.2）。
4. 量能分支（决策树）→ 从"主导结论"降为"调节信号"。
5. 止盈轨道 A/B → 从主止盈降为辅助（再平衡为主，10.7.3）；轨道 C 保持 Candidate 或删除（B13）。
6. L4 关键词判事件 → 保持 Candidate，后续由人工/AI 标注（B13）。

**修复（不是删除）：** 决策树"中后期暴跌 → 安心持有"漏判路径。

### 3.2 可直接复用的现有代码

1. **Regime 判定**（Panic/Structural/Pre-Event）——v1.0 Market/Portfolio/Thesis 风险分级的信号源。
2. **L2 瓶颈信号 + 结构性止损触发**——Edge 证伪信号源（10.3/10.11）。
3. **仓位约束计算**（板块 20% 裁剪、现金下限、¥100 门槛）——10.8 R3 骨架。
4. **健康检测 + 调度器 + `_save_daily_snapshot` 框架**——Daily 监控/快照/预测写入（P0-3 回填可扩展它）。
5. **BOTTLENECK_CLUSTERS / SHARED_INDICATORS / HOLDING_WEIGHTS / BOARD_FUND_MAP**——集群硬上限（10.8）、加权 RSI（B12）数据承载。
6. **LEADING_INDICATORS / KEY_DATES / CYCLE_ASSESSMENTS**——Signal/Edge 数据（10.3/10.4）。
7. **action_log.reason / pending_plans**——Override 与事件驱动的承载雏形（10.15/10.14）。
8. **复盘生成器骨架**（Tier-1 门禁、Tier-2 三档、对照、置信度校准）——10.13 统计层。
9. **intraday_check 加权 RSI + plan 检查**——B12 计算 + RC4 雏形。
10. **technical-check skill**——Add 候选人工检查流程（10.12），保留为对话层工具。

### 3.3 P0-1 数据修复是否影响现有交易逻辑

**结论：不影响交易决策逻辑；但有两个注意点。**

1. **record_trade 写路径修复**：只改保存目标（统一 DATA_DIR），shares/cost/plan 计算逻辑不变。已确认项目根目录无残留 portfolio.json → 无数据迁移负担。影响：低。
2. **storage 单写者 + 原子写**：涉及 app.py `_save_portfolio`、`/api/portfolio/update`、`/api/portfolio/action`、`_save_daily_snapshot`、`backfill_portfolio_history`、record_trade。改为统一写入函数（临时文件 + rename + 锁）后，**读写语义不变**，仅并发行为被正确串行化。影响：低。
3. **每日备份**：纯新增，无影响。
4. **portfolio.json schema 化 + 去重**：⚠️ 消费方多（app/trading_rules/position_engine/fund_nav_fetcher 读取 status/tier/base/max/theme/amount/cost/sector），**必须保持字段兼容**；建议 P0-1 只做"校验 + 去重 + 必填检查"，**tier/status 语义统一推迟到 P1**（与 v1.0 档位引入一起做），避免二次迁移。

### 3.4 v1.0 缺少数据承载结构的规则

| v1.0 规则 | 缺失承载 | 最小落点建议 |
|---|---|---|
| Thesis 卡（10.2） | thesis/ 目录（每板块 md） | 新目录 |
| Edge 状态/Observe 期（10.3/10.11） | 证伪命中与观察期状态 | BOTTLENECK_DISRUPTION.status 可扩展 + pending_plans.status |
| 档位 evidence_stage（10.6） | holdings 档位字段 | portfolio.json holdings 新增字段（P0-1 schema 预留） |
| Explore 试探仓（10.6） | 档位 + 标记 | 同上 |
| 背离分类/候选队列（10.10） | divergence 记录 | 新数据结构（snapshot 或独立 log） |
| Prediction 幅度区间 + 回填（10.5） | predictions 字段 | predictions/<date>.json 扩展（P0-3） |
| Override 记录（10.15） | ledger/overrides.json | 新数据结构（action_log 可扩展） |
| Weekly 摘要（10.14） | 摘要输出 | review 生成器扩展 |
| 验证归因（10.13） | review 结构化字段 | review schema 扩展 |
| "基本面明显改善"辅助分类（C19） | 无（可计算） | LEADING_INDICATORS trend 聚合即可，无需新存储 |
| "大幅回调"提示（C20） | 无（可计算） | 历史/RSI/MA 计算即可，无需新存储 |

### 3.5 P0/P1/P2 实际依赖关系

```
P0-1 数据地基（无前置）
  ├─ 修复 record_trade 写路径
  ├─ storage 单写者 + 原子写 + 每日备份
  └─ portfolio.json schema 校验/去重（字段兼容，tier 语义统一留给 P1）
        │
        ├──► P0-3 验证闭环（预测回填 + 命中率/偏差）
        │       依赖 P0-1 的原子写（回填写 predictions）
        │
        └──► P1-1 规则收敛（rules.yaml + RSI/趋势语义调整 + 档位字段）
                依赖 P0-1 schema（新增 evidence_stage）
                依赖 v1.0 已冻结 ✅
                   │
                   └──► P1-2 硬约束（主题集群 30% + 超限禁加仓）
                           建议在 P1-1 单一事实源之后
                              │
                              └──► P2 UI 收敛（行动计划视图 + 残留清理 + 复盘可读）
                                      依赖 P0-2（score 清理）+ P1-1（档位/背离输出）

P0-2 决策树漏判修复 + score 残留清理（独立支线，可与 P0-1 并行；不依赖数据层）
P1-3 Thesis 卡（纯文档，可随时开始，无代码依赖）
```

**关键判断：**
- P0-1 无前置，是唯一"先决"项；P0-2 与 P1-3 可并行。
- P0-3 依赖 P0-1 的原子写；P1-1 依赖 P0-1 的 schema 预留；P1-2 依赖 P1-1；P2 依赖 P0-2 + P1-1。
- **P0-1 的 schema 设计必须预留 v1.0 新字段（evidence_stage / divergence / override），避免二次迁移。**
- 不要跳序：先 P0-1 再 P0-3/P1-1；P0-2 可提前做（纯逻辑修复）。

---

## 4. 审计结论

1. **v1.0 规则中约 40% 有现成实现或数据承载可复用**（Regime、L2/结构性止损、仓位约束、健康检测、BOTTLENECK_CLUSTERS、加权 RSI、复盘骨架、action_log/pending_plans）。
2. **冲突集中在三处**：RSI 直接定金额（B12）、趋势过滤绝对否决（C15）、决策树漏判与 score 残留（P0-2）——都无需删除整体机制，只需语义调整。
3. **缺失集中在五类新承载**：档位、背离分类/候选、Thesis 卡、Override、验证归因——全部是 P1/P2 范围，不影响 P0-1。
4. **P0-1 是安全的**：不触碰任何交易决策逻辑；唯一要求是字段兼容与 schema 预留。

> 本审计只读完成。下一步实施顺序（待用户确认）：P0-1 数据地基 →（P0-2 决策树修复 + P1-3 Thesis 卡并行）→ P0-3 验证闭环 / P1-1 规则收敛 → P1-2 硬约束 → P2 UI。
