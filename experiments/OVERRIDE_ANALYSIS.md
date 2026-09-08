# Override / 非正式规则操作分析（框架）

## 分类体系

| 类 | 含义 |
|---|---|
| CORE | 事前规则/计划内的执行 |
| TACTICAL | 有预定义规则的动态调整（网格/RSI 计划等） |
| INTUITION | 主观判断，未伪装成规则，进直觉日志 |
| OVERRIDE_PRICE | 纯价格驱动 |
| OVERRIDE_MARKET | 对市场环境的临时判断 |
| OVERRIDE_THESIS | 对 Thesis/基本面的临时判断 |
| OVERRIDE_EXECUTION | 执行/节奏违规（如未到决策点、同日反向换仓） |

分类方法：先问“当时客观数据是什么、原规则是否允许、若按规则会怎样、实际结果怎样”，
禁止用结果反推“这条规则当时其实合理”。

完整台账（含逐笔）在 `PERSONAL_DATA_DIR/experiments/OVERRIDE_ANALYSIS.md`，不入 Git。
首批已分类：8/21、8/27“踢利润”、8/24-25“搏反弹”、9/7 减仓 1/4 + 云计算加仓。
