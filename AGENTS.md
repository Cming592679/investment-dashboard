# Investment Dashboard — Agent 指令

本文件是项目级指令，每次会话自动加载。

## 先读

- `PROJECT_CONTEXT.md` —— 项目的完整工作体系（项目认知 / 产品目标 / 用户工作流 / 投资体系 / 技术架构 / 当前问题 / 长期目标 / Agent 工作原则）。这是本项目的"认知层"文档，开始任何任务前先阅读相关章节。

## 核心红线

1. **个人数据不入 Git**：`portfolio.json`、`history/`、`predictions/`、`reviews/`、`portfolio_history/`、`position_snapshots/`、`.env.local` 全部位于 `PERSONAL_DATA_DIR` 或已被 .gitignore 覆盖，严禁提交。
2. **基金视角**：所有投资结论基于领先指标/瓶颈分析，不因单日涨跌给出操作建议。
3. **建议必须有数据**：回答"能不能买/该不该加仓"时，执行 `technical-check` 的五项入场检查并列出统计结果。
4. **诚实标注不确定性**：预测置信度、数据过期、验证样本不足都要如实说明，不假装确定。

## 常用入口

- 启动：`python3 app.py` → http://localhost:5000
- 数据目录：由 `.env.local` 的 `PERSONAL_DATA_DIR` 指定（绝对路径仅存在于本机 `.env.local`，不入库）
- 交易记录：`python3 record_trade.py buy|sell|plan <fund_code> <amount> <note>`
- 盘中检查：`python3 intraday_check.py [--json]`
- 仓位模型：`python3 position_engine.py [--save]`
- 方法论：`DESIGN.md` / `TRADING_METHODOLOGY.md` / `REVIEW_METHODOLOGY.md` / `serenity-bottleneck-hunter` skill

全局规则（工程流程 / Git 规范 / Superpowers 技能）见全局 AGENTS.md，与本文件冲突时以用户明确要求 > 项目规则 > 全局规则为准。
