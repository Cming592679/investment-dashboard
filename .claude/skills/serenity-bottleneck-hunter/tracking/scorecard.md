# Scorecard — 样本外 Alpha 打分(2026-06-16)

> ⚠️ **样本期太短(picks 多为 2-3 周)+ N 不足 → 本表只装仪表、不下结论。**
> **种子/校准集(光子学等 10 只,record_date ≤ 2026-02-01)已从样本外剔除**——
> 它是 skill 逆向建出来的 in-sample 赢家(SIVE +1918% 之类),算进来就是循环论证 + 幸存者偏差。
> 用 **median** 而非 mean 看 🟢(抗单只 10-bagger 拉偏);最硬的是 🟢-vs-🔴 内部对照(主题 beta 对消)。
> 样本外已打分 402 | 种子 10(单列) | 拉价失败 6

## ① 🟢 vs 🔴 内部对照(样本外 · 最硬 · 主题 beta 对消)

| 桶 | N | median raw | mean raw | 命中率(raw>0) |
|---|---|---|---|---|
| 🟢候选 | 36 | -7.9% | -5.0% | 25% |
| 🟡观望 | 220 | -2.8% | -3.2% | 37% |
| 🔴排除 | 132 | -4.6% | -4.5% | 29% |

**🟢−🔴 价差(median)= -3.3%**(>0 = 过滤器有选股信号;<0 = 反指 ⚠)。
⚠️ 样本外 picks 才 2-3 周,这个数 = 噪音,**现在只装表、等 3-6 个月再读**。

## ② Alpha vs 主题 ETF(样本外 · 次要 · naive β=1)

| 桶 | N | median Alpha | 命中率(α>0) |
|---|---|---|---|
| 🟢候选 | 36 | -4.3% | 22% |
| 🔴排除 | 132 | -0.2% | 48% |

## ③ 各主题 🟢 候选表现(样本外,raw median,N 小慎读)

| 主题 | 🟢 N | 🟢 median raw | benchmark |
|---|---|---|---|
| 800VDC电源半导体 | 1 | +13.7% | SOXX |
| AIAgent中国 | 4 | -16.2% | 2800.HK |
| AIAgent经济 | 3 | -12.8% | IGV |
| AIAgent美国 | 2 | -8.7% | IGV |
| AMR无人机视觉 | 4 | -8.7% | 510300.SHG |
| MLCC | 1 | +30.7% | 510300.SHG |
| MLCC美股 | 1 | +9.4% | SOXX |
| 个人AIPC | 4 | +4.9% | SOXX |
| 人形机器人A股 | 1 | -8.0% | 510300.SHG |
| 低空经济A股 | 1 | +0.5% | 510300.SHG |
| 商业航天美股 | 1 | +1.3% | ITA |
| 物理AI | 3 | -7.3% | 510300.SHG |
| 物理AI中国 | 1 | -22.6% | 2800.HK |
| 物理AI美国 | 1 | -15.9% | BOTZ |
| 网络安全 | 2 | -15.6% | CIBR |
| 自动驾驶L4 | 6 | -7.5% | DRIV |

## ⑤ 种子/校准集(in-sample · **非样本外 · 仅参考**)

光子学等 10 只,record_date ≤ 2026-02-01(约 5.5 个月前)。这是 skill 逆向建模的 in-sample 赢家,**不能当业绩**。

| 标的 | 主题 | raw |
|---|---|---|
| SIVE.ST | 光子学 | +1917.5% |
| IQE.LSE | 光子学 | +1001.0% |
| AXTI.US | 光子学 | +560.7% |
| SOI.PA | 光子学 | +458.1% |
| AEHR.US | 光子学 | +422.9% |
| ARM.US | AI算力 | +259.6% |
| NBIS.US | AI算力 | +189.1% |
| LITE.US | 光子学 | +147.9% |
| TSEM.US | 光子学 | +135.6% |
| RKLB.US | 商业航天 | +43.8% |

## ④ 证伪条件触发(默认规则:跌幅>15% 且 1m 转负)

本次 33 个 pick 触发证伪 → thesis 已被价格证否,应复盘:

- 688120.SHG (A股半导体) raw -32% · 别追/观察
- EHGO.US (AMR无人机视觉) raw -29% · 🔴排除[ticker错位修复:此行3m+787%
- EHGO.US (物理AI美国) raw -29% · 🔴排除[ticker错位修复:此行3m+787%
- AMPX.US (物理AI美国) raw -27% · 🔴排除[已ext+硅负极niche]
- HXGBY.US (物理AI美国) raw -26% · 🟡观望[ext+测量ADR]
- INVZ.US (自动驾驶L4) raw -25% · 🟡观望[trigger:订单 visibilit
- WOLF.US (800VDC电源半导体) raw -25% · 🟡观望[trigger:回$40或下季营收/产能
- HXGBY.US (自动驾驶L4) raw -24% · 🟡观望[trigger:1m转正]
- 688333.SHG (低空经济A股) raw -24% · 🟡观望[deep 金属3D打印]
- 0268.HK (AIAgent中国) raw -23% · 🟢候选[企业 SaaS 苍穹 Agent+深度回
- 9868.HK (物理AI中国) raw -23% · 🟢候选[真ModeA港股小鹏off-22+1m+
- IPWR.US (800VDC电源半导体) raw -22% · AVOID-chase
- INVZ.US (物理AI美国) raw -22% · 🟡观望[deepRange+1m持平]
- DOCU.US (AIAgent美国) raw -20% · 🔴排除[已ext+签名垄断 + IAM 转型]
- JOBY.US (AMR无人机视觉) raw -19% · 🟡观望[trigger:回\]
- INDI.US (物理AI美国) raw -19% · 🔴排除[已ext+车规模拟+RF]
- XPEV.US (物理AI美国) raw -19% · 🟡弱ModeA观望[1m+5中概折价]
- ACHR.US (AMR无人机视觉) raw -19% · 🟡观望[trigger:商业化里程碑]
- JOBY.US (物理AI美国) raw -19% · 🔴排除[已ext+eVTOL]
- 688111.SHG (AIAgent中国) raw -18% · 🟢候选[WPS AI 国产 Copilot+深度
- CRM.US (AIAgent经济) raw -18% · 🟡观望[trigger:Agentforce A
- ACHR.US (物理AI美国) raw -18% · 🟡观望[deepRange eVTOL]
- FIVN.US (AIAgent美国) raw -17% · 🔴排除[已ext+客服 SaaS 红海]
- AUR.US (物理AI美国) raw -17% · 🟡观望[已ext+3m+52/1m-6]
- 0020.HK (AIAgent中国) raw -17% · 🟡观望[trigger:商量大模型 B 端订单]
- SOUN.US (AIAgent经济) raw -17% · 🟡观望[trigger:营收兑现]
- 9988.HK (AIAgent中国) raw -17% · 🔴排除[下游巨头-但 rng9% 历史底-非 S
- AKAM.US (AIAgent美国) raw -16% · 🔴排除[已ext+边缘+微分段]
- VNP.TO (商业航天) raw -16% · 观察/小仓(非低位)
- ZM.US (AIAgent美国) raw -16% · 🔴排除[已ext+会议 Agent niche]