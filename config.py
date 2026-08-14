"""Investment Dashboard — 全部基金/板块配置"""

import os
from datetime import date

# ══════════════════════════════════════════════════════════
# 基金定义
# ══════════════════════════════════════════════════════════

FUNDS = {
    "019633": {
        "name": "国泰半导体材料设备ETF联接C",
        "short": "半导体设备",
        "benchmark": "512760.SS",
        "market": "a",
        "stocks": {
            "002371.SZ": "北方华创",
            "688012.SS": "中微公司",
            "688072.SS": "拓荆科技",
            "688120.SS": "华海清科",
            "300604.SZ": "长川科技",
        },
        "indices": {
            "000688.SS": "科创50",
            "159995.SZ": "芯片ETF",
        },
        "specials": {
            "688981.SS": {"name": "中芯国际", "note": "国内Fab龙头，扩产节奏决定设备订单景气度"},
        },
        "exit_thresholds": {
            "rsi_overbought": 75, "rsi_oversold": 25,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -3, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "014194": {
        "name": "汇添富中证芯片指数增强C",
        "short": "芯片指数",
        "benchmark": "159995.SZ",
        "market": "a",
        "stocks": {
            "688981.SS": "中芯国际",
            "002371.SZ": "北方华创",
            "603501.SS": "韦尔股份",
            "688012.SS": "中微公司",
            "603986.SS": "兆易创新",
        },
        "indices": {
            "000688.SS": "科创50",
            "159995.SZ": "芯片ETF",
        },
        "specials": {
            "512480.SS": {"name": "半导体ETF", "note": "A股半导体板块整体温度计"},
            "688825.SS": {"name": "长鑫存储(CXMT)", "note": "国内唯一DRAM大厂，全球份额~8%。HBM3→2026量产。IPO 7/27市值3.28万亿。最大瓶颈：无EUV"},
        },
        "exit_thresholds": {
            "rsi_overbought": 75, "rsi_oversold": 25,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -3, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "CPO": {
        "name": "光模块(CPO)板块监测",
        "short": "CPO",
        "benchmark": "300308.SZ",
        "market": "a",
        "stocks": {
            "300308.SZ": "中际旭创",
            "300502.SZ": "新易盛",
            "688498.SS": "源杰科技",
            "688048.SS": "长光华芯",
            "600105.SS": "永鼎股份",
        },
        "indices": {
            "159997.SZ": "电子ETF",
            "399006.SZ": "创业板指",
        },
        "specials": {
            "NVDA": {"name": "英伟达", "note": "AI算力需求决定光模块订单景气度"},
        },
        "exit_thresholds": {
            "rsi_overbought": 75, "rsi_oversold": 25,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -3, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "024239": {
        "name": "华夏全球科技先锋QDII C",
        "short": "海外半导体",
        "benchmark": "SMH",
        "market": "us",
        "stocks": {
            "SNDK": "SanDisk(闪迪)",
            "MU":   "美光科技",
            "MRVL": "Marvell",
            "TSM":  "台积电",
            "LITE": "Lumentum(光芯片)",
        },
        "indices": {
            "SMH":  "VanEck半导体ETF",
            "SOX":  "费城半导体指数",
            "QQQ":  "纳指100ETF",
        },
        "specials": {
            "WDC": {"name": "西部数据", "note": "NAND Flash原厂，与铠侠合并进行中"},
        },
        "exit_thresholds": {
            "rsi_overbought": 70, "rsi_oversold": 30,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -2.5, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "021528": {
        "name": "财通成长优选C",
        "short": "电子材料",
        "benchmark": "159997.SZ",
        "market": "a",
        "stocks": {
            "300502.SZ": "新易盛",
            "688519.SS": "南亚新材",
            "688498.SS": "源杰科技",
            "300408.SZ": "三环集团",
            "301511.SZ": "德福科技",
        },
        "indices": {
            "159997.SZ": "电子ETF",
            "399006.SZ": "创业板指",
        },
        "specials": {
            "002436.SZ": {"name": "兴森科技", "note": "IC载板/PCB样板，PCB行业景气度风向标"},
        },
        "exit_thresholds": {
            "rsi_overbought": 75, "rsi_oversold": 25,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -3, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "015789": {
        "name": "永赢高端装备智选A",
        "short": "军工电子",
        "benchmark": "512660.SS",
        "market": "a",
        "stocks": {
            "300136.SZ": "信维通信",
            "600879.SS": "航天电子",
            "688002.SS": "睿创微纳",
            "688375.SS": "国博电子",
            "301232.SZ": "飞沃科技",
        },
        "indices": {
            "512660.SS": "军工ETF",
            "000300.SS": "沪深300",
        },
        "specials": {
            "RKLB": {"name": "Rocket Lab", "note": "美股商业航天风向标，全球发射市场情绪"},
        },
        "exit_thresholds": {
            "rsi_overbought": 75, "rsi_oversold": 25,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -3, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "025856": {
        "name": "华夏中证电网设备ETF联接A",
        "short": "电网设备",
        "benchmark": "159611.SZ",
        "market": "a",
        "stocks": {
            "600406.SS": "国电南瑞",
            "000400.SZ": "许继电气",
            "600089.SS": "特变电工",
            "601179.SS": "中国西电",
            "601126.SS": "四方股份",
        },
        "indices": {
            "159611.SZ": "电力ETF",
            "000300.SS": "沪深300",
        },
        "specials": {
            "600900.SS": {"name": "长江电力", "note": "电力板块定海神针，防御属性"},
        },
        "exit_thresholds": {
            "rsi_overbought": 75, "rsi_oversold": 25,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -3, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "020608": {
        "name": "南方中证机器人ETF联接C",
        "short": "机器人",
        "benchmark": "159258.SZ",
        "market": "a",
        "stocks": {
            "688017.SS": "绿的谐波",
            "601100.SS": "恒立液压",
            "603662.SS": "柯力传感",
            "002520.SZ": "日发精机",
            "300748.SZ": "金力永磁",
        },
        "indices": {
            "000688.SS": "科创50",
            "399006.SZ": "创业板指",
        },
        "specials": {
            "TSLA": {"name": "特斯拉(Optimus)", "note": "人形机器人最强催化剂。Optimus V3定型=产业链从0到1"},
        },
        "exit_thresholds": {
            "rsi_overbought": 75, "rsi_oversold": 25,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -3, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },

    "STORAGE": {
        "name": "存储芯片板块监测（A股+海外）",
        "short": "存储芯片",
        "benchmark": "SMH",
        "market": "mixed",
        "stocks": {
            # 海外存储原厂（定价者）
            "000660.KS": "SK海力士",
            "005930.KS": "三星电子",
            "MU":       "美光科技",
            # A股存储产业链
            "603986.SS": "兆易创新",
            "300223.SZ": "北京君正",
        },
        "specials": {
            "SNDK": {"name": "SanDisk(闪迪)", "note": "NAND Flash原厂，Q4被WDC收购中。100055真实重仓"},
        },
        "indices": {
            "SMH": "VanEck半导体ETF",
            "SOX": "费城半导体指数",
        },
        "specials": {
            "WDC": {"name": "西部数据", "note": "NAND Flash原厂，与铠侠合并进行中"},
        },
        "exit_thresholds": {
            "rsi_overbought": 70, "rsi_oversold": 30,
            "drop_red": -5, "drop_yellow": -3,
            "index_drop_red": -2.5, "index_drop_yellow": -1.5,
            "ma50_red_count": 2, "ma50_yellow_count": 1,
            "special_drop_red": -5, "special_drop_yellow": -3,
        },
    },
}

# ══════════════════════════════════════════════════════════
# 领先指标体系（每板块独立，标 * 为自动抓取，其余手动更新）
# ══════════════════════════════════════════════════════════

LEADING_INDICATORS = {
    "019633": {
        "北方华创合同负债 QoQ【⑥设备景气先行】": {
            "value": "Q1 合同负债 ¥42.03亿（环比-2.05%），研发投入+37%",
            "trend": "flat",
            "note": "【⑥设备订单先行】合同负债=Fab预付款=设备订单领先6-12月。环比微降需关注Q2是否回升。北方华创是国内半导体设备绝对龙头，其订单趋势代表行业Beta",
            "update_cycle": "季报后（4/8/10月底）",
        },
        "中芯国际 Capex/折旧比【⑧Fab扩产意愿】": {
            "value": "Q1 Capex/折旧=1.8x（激进扩张），Q2财报预计8/15发布",
            "trend": "up",
            "note": "【⑧Fab扩产→设备订单】中芯国际是国内最大Fab，Capex/折旧>1.5=激进扩产。其扩产直接转化为北方华创/中微/拓荆的订单。Q2财报是关键验证",
            "update_cycle": "季报后",
        },
        "CXMT 扩产→设备采购规模【②DRAM自主化】": {
            "value": "CXMT月产能30万片→2030年60万片。IPO募资579亿→设备采购加速。HBM3量产锁定2026",
            "trend": "up",
            "note": "【②DRAM自主化→设备最大增量客户】CXMT每扩1万片/月≈设备采购¥50亿。作为国内唯一DRAM大厂，其上市后的扩产计划是国内半导体设备行业未来3年最大的增量需求来源",
            "update_cycle": "季度（盯CXMT公告+季报）",
            "last_updated": "2026-07-29",
        },
        "大基金三期投放进度【政策CapEx确认】": {
            "value": "¥3000亿承诺 → Q2首批项目公告3个/¥180亿，投放率仅6%",
            "trend": "up",
            "note": "【⑨政策驱动】大基金三期是国家队真金白银。承诺≠落地——当前投放率偏低（6%），一旦加速投放→设备订单将显著放量。这是政策驱动的确定性底牌",
            "update_cycle": "季度/事件驱动",
        },
        "美国对华设备管制升级风险【②外部催化剂】": {
            "value": "MATCH法案酝酿中，可能进一步限制DUV出口。BIS实体清单新增频率上升",
            "trend": "up",
            "note": "【②外部制裁→倒逼国产替代】管制越紧→国产设备越迫切。每轮新制裁后3-6月是北方华创/中微订单高峰。这是'A股设备商的特有催化剂'——对海外设备商是利空，对国内是利好",
            "update_cycle": "事件驱动（盯BIS公告+联邦公报）",
        },
    },

    "014194": {
        # ── 瓶颈原型 → 指标 ──────────────────
        "北方华创合同负债 QoQ【⑥设备瓶颈】": {
            "value": "Q1 合同负债 ¥85亿（+18% QoQ）",
            "trend": "up",
            "note": "【⑥设备瓶颈】预收款增速=Fab下单节奏，领先设备收入6-12月。这是板块最核心领先指标",
            "update_cycle": "季报后（4/8/10月底）",
        },
        "SMIC Capex/折旧比【⑧巨头依赖】": {
            "value": "Q1 Capex/折旧=1.8x（激进扩张）",
            "trend": "up",
            "note": "【⑧巨头依赖】>1.5=激进扩产→国产设备订单↑；<1=收缩→危险信号",
            "update_cycle": "季报后",
        },
        "光刻胶进口依存度【①材料垄断】": {
            "value": "2026Q1 进口占比 78%（同比-5pp）",
            "trend": "up",
            "note": "【①材料垄断】进口占比下降=国产替代在推进。目标<50%才算突破。盯日本JSR/TOK财报中的中国收入变化做交叉验证",
            "update_cycle": "季度海关数据",
        },
        "BIS实体清单新增频率【②单源卡脖子】": {
            "value": "2026年6月新一轮酝酿中，涉及AI芯片+设备",
            "trend": "up",
            "note": "【②单源卡脖子催化剂】管制升级→短期利空（存量设备断供）、中期倒逼国产设备订单。每轮新管制后3-6月是北方华创订单高峰",
            "update_cycle": "事件驱动（盯BIS公告+联邦公报）",
        },
        "大基金三期实际投放率": {
            "value": "¥3000亿承诺 → Q2首批项目公告3个/¥180亿",
            "trend": "up",
            "note": "【CapEx确定性验证】承诺≠落地。实际公告项目数/金额 = 真金白银进场速度。当前投放率偏低（6%），需加速",
            "update_cycle": "季度/事件驱动",
        },
        "长鑫存储 DRAM 产能扩张【②DRAM自主化→设备订单】": {
            "value": "月产能30-32万片→2026底35万片→2030年60万片。Q1营收+719% YoY。7/27科创板上市募资579亿",
            "trend": "up",
            "note": "【②DRAM三寡头→国产替代突围】CXMT是全球第四大DRAM厂(份额~8%)。HBM3量产2026年、HBM3E 2027年、HBM4 2028年。每扩产1万片/月→设备采购约¥50亿，国产设备商直接受益。最大瓶颈是EUV设备管制→影响HBM良率",
            "update_cycle": "季度（盯CXMT季报+扩产公告）",
            "last_updated": "2026-07-29",
        },
    },

    # ═══ CPO · 光模块（Bottleneck：带宽瓶颈） ═══
    # 5层链：AI算力→NVDA GPU→800G/1.6T光模块→光芯片/DSP→InP衬底
    # 瓶颈原型：②DSP双垄断 ③产能售罄 ①InP衬底垄断
    "CPO": {
        "中际旭创 800G 订单积压【③产能售罄】": {
            "value": "2026年800G产能已售罄，1.6T Q3量产",
            "trend": "up",
            "note": "【③产能售罄】全球800G光模块龙头，订单可见度6-12月。产能售罄=需求>供给=光模块公司定价权强",
            "update_cycle": "季报后更新",
        },
        "NVDA GPU→光模块速率升级节奏【②DSP瓶颈】": {
            "value": "Blackwell→800G标配，Rubin→1.6T/CPO 2027",
            "trend": "up",
            "note": "【②DSP芯片双垄断】Marvell/Broadcom的DSP是800G/1.6T核心卡点。NVDA推下一代GPU→必须配更快光模块→DSP升级节奏决定光模块迭代速度",
            "update_cycle": "NVDA GTC/季报后",
        },
        "InP 衬底供应【①材料垄断】": {
            "value": "AXTI/IQE占全球InP衬底>70%，无国产替代",
            "trend": "flat",
            "note": "【①材料垄断】光芯片（EML/CW激光器）必须用InP衬底，AXTI/IQE垄断。衬底供应紧张=光芯片涨价=光模块成本压力。仕佳光子/源杰科技在追赶",
            "update_cycle": "季度（盯AXTI/IQE季报）",
        },
        "800G→1.6T 渗透率": {
            "value": "2026年800G占数据中心光模块>60%，1.6T刚起步",
            "trend": "up",
            "note": "速率升级=光模块ASP提升。800G→1.6T过渡期，先发者吃利润最厚的阶段",
            "update_cycle": "季度（LightCounting报告）",
        },
        "数据中心内部带宽增速": {
            "value": "AI集群东西向流量年增3-5x，远超摩尔定律",
            "trend": "up",
            "note": "AI训练/推理的东西向流量爆炸=光互联需求增速>GPU增速。这是CPO板块最根本的需求驱动力",
            "update_cycle": "年度（盯NVDA/Google集群架构白皮书）",
        },
    },

    # ═══ 海外半导体 · 存储+代工（真实持仓：SNDK/MU/MRVL/TSM/LITE） ═══
    # 瓶颈原型：②存储寡头+②TSMC代工单源+①光芯片材料
    "024239": {
        "美光 DRAM/NAND 出货均价 QoQ【②存储定价】": {
            "value": "Q3 FY2026(Nov)指引DRAM位元出货+15% QoQ，HBM3e爬坡中",
            "trend": "up",
            "note": "【②存储寡头定价】美光是全球第三大存储厂，其出货均价趋势=存储周期温度计。Q4 FY2026财报(9/25)是关键验证",
            "update_cycle": "季报后",
        },
        "SanDisk/WDC NAND Flash 产能利用率【③产能售罄】": {
            "value": "WDC H1产能利用率回升至85%，NAND Flash合约价Q2 +8% QoQ",
            "trend": "up",
            "note": "【③产能售罄】NAND Flash比DRAM周期更短(6-12月)。产能利用率85%→供给在追赶需求。若利用率突破90%→价格加速；若跌破70%→过剩信号",
            "update_cycle": "季度（盯WDC+SanDisk季报）",
        },
        "台积电 先进制程产能利用率【⑧代工单源】": {
            "value": "Q2法说会：3nm/5nm产能利用率100%，CoWoS年底月产能14万片→2027年17万片",
            "trend": "up",
            "note": "【⑧代工单源】TSMC先进制程满载=全球半导体需求强劲。产能利用率掉头→最可靠的反转信号。Capex上修至$600-640亿=扩产周期加速",
            "update_cycle": "TSMC月度营收(每月10日)+季报/法说会",
        },
        "Lumentum 光芯片订单→数据中心光互联需求【①光芯片】": {
            "value": "Q4 FY2026财报(8/11)待发布。Q3营收$517M(+12% YoY)，光芯片订单积压创历史新高",
            "trend": "up",
            "note": "【①光芯片材料】Lumentum是数据中心光芯片（EML/CW激光器）核心供应商。订单积压=下游光模块需求持续超预期。与CPO板块共享瓶颈",
            "update_cycle": "季报后（8/11 Q4 FY2026）",
        },
        "Marvell 数据中心营收→ASIC+网络芯片需求": {
            "value": "Q1 FY2027数据中心营收$1.4B(+67% YoY)，定制ASIC+交换机芯片双轮驱动",
            "trend": "up",
            "note": "Marvell数据中心营收=AI定制芯片+高速网络需求。AWS Trainium/Google TPU等定制ASIC绕开NVDA GPU→开辟第二赛道",
            "update_cycle": "季报后（8/28 Q2 FY2027）",
        },
    },

    # ═══ 电子材料 · 电子上游+光通信（真实持仓：新易盛/南亚新材/源杰/三环/德福） ═══
    # 瓶颈原型：③铜箔/CCL产能紧张 ①光芯片衬底 ⑧下游AI服务器→材料需求
    "021528": {
        "南亚新材 CCL出货量+价格【③CCL产能】": {
            "value": "Q2 CCL出货量环比+8%，高端高频CCL占比提升至35%",
            "trend": "up",
            "note": "【③CCL产能瓶颈】南亚新材是国内高频高速CCL龙头，直接受益AI服务器PCB层数升级(8→20层→CCL用量3-5x)。高频CCL毛利率>40%远超普通FR-4",
            "update_cycle": "季报后",
        },
        "德福科技 电子铜箔加工费【④上游材料】": {
            "value": "Q2锂电铜箔加工费企稳18,000/吨，电子铜箔维持25,000/吨",
            "trend": "flat",
            "note": "【④BOM普适+成本信号】铜箔加工费=PCB成本关键变量。电子铜箔(低轮廓)技术壁垒高→加工费更稳定。锂电铜箔过剩→可能转产电子铜箔→供给增加",
            "update_cycle": "季报后",
        },
        "源杰科技 CW激光器送样验证【①光芯片衬底】": {
            "value": "100G CW激光器已送样中际旭创/新易盛，预计Q3完成验证",
            "trend": "up",
            "note": "【①光芯片国产替代】CW激光器是800G/1.6T光模块核心光芯片（InP衬底）。目前全球90%+由Lumentum/住友供应。源杰科技若通过验证→国产替代0→1突破",
            "update_cycle": "季报后+送样进度跟踪",
        },
        "三环集团 MLCC/陶瓷封装基座出货【④BOM普适】": {
            "value": "Q2 MLCC出货量+15% YoY，高容MLCC占比提升。陶瓷封装基座满产",
            "trend": "up",
            "note": "【④BOM普适+电子周期品】MLCC是电子行业'大米'——所有电路板都需要。出货量增速=电子行业景气度温度计。陶瓷封装基座→芯片封装需求",
            "update_cycle": "季报后",
        },
    },

    # ═══ 军工电子 · 国防+电子（真实持仓：信维/航天电子/睿创/国博/飞沃） ═══
    # 瓶颈原型：②军用射频/红外芯片进口替代 ⑨国防预算驱动 ⑥特种元器件产线
    "015789": {
        "睿创微纳 红外探测器出货【②军用红外芯片】": {
            "value": "H1营收+35% YoY，非制冷红外探测器全球份额>15%。军用+民用双线增长",
            "trend": "up",
            "note": "【②军用红外芯片国产替代】睿创微纳是国内非制冷红外探测器龙头，全球第三。国防信息化→红外制导/侦察需求↑。民用→车载红外/工业检测打开第二增长曲线",
            "update_cycle": "季报后",
        },
        "国博电子 射频芯片订单【②军用射频芯片】": {
            "value": "有源相控阵T/R组件订单饱满，GaN射频芯片产线满产",
            "trend": "up",
            "note": "【②军用射频芯片进口替代】国博电子是国内军用GaN/GaAs射频芯片核心供应商。有源相控阵雷达→每个阵元需要1颗T/R组件→战斗机/驱逐舰/预警机需求刚性",
            "update_cycle": "季报后",
        },
        "信维通信 军工+消费电子双轮【④BOM普适】": {
            "value": "Q2军工天线订单环比+20%，消费电子天线受益AI手机换机潮",
            "trend": "up",
            "note": "【④BOM普适+军工电子】信维通信是天线/射频连接器龙头。军工→相控阵天线/卫通天线；消费电子→AI手机天线升级(LCP/MPI)。双轮驱动降低单一周期风险",
            "update_cycle": "季报后",
        },
        "国防预算增速→军工电子订单前瞻【⑨政策驱动】": {
            "value": "2026年国防预算¥1.87万亿(+7.2% YoY)，装备采购占比持续提升",
            "trend": "up",
            "note": "【⑨政府国防CapEx】国防预算增速7.2%→装备采购增速>10%(结构优化)。电子化/信息化是装备采购最大增量方向。和电网板块共享政府预算驱动的确定性",
            "update_cycle": "年度(两会)+半年度(国防白皮书)",
        },
    },

    # ═══ 电网设备 · 电力基建（Evolution：政策驱动+产能瓶颈） ═══
    # 5层链：新能源消纳→电网升级→变压器/开关→IGBT/电缆→铜/硅钢
    # 瓶颈原型：③变压器产能售罄 ⑧国网单一大客户 ⑥设备产能
    "025856": {
        "国网/南网年度投资计划【⑧单一大客户】": {
            "value": "Q1固投1290亿(+37% YoY)。H1物资招标>2500亿(+17%)。7月特高压第三批招标108.7亿",
            "trend": "up",
            "note": "【⑧巨头依赖】国网H1投资进度超预期(+37%→远超年初+8%计划)。特高压+配电网双轮驱动。若H2维持节奏→全年固投可能上修至7000亿+",
            "update_cycle": "月度跟踪（国网电子商务平台+基建部公告）",
            "last_updated": "2026-07-21",
        },
        "大型变压器交付周期【③产能售罄】": {
            "value": "全球大型变压器交期18-24月（正常12月），供给严重不足",
            "trend": "up",
            "note": "【③产能售罄→⑥设备瓶颈】全球变压器产能不足→交期拉长→涨价+扩产。变压器=电网的CPU，没有变压器新能源发的电送不出去。这是板块最强基本面支撑",
            "update_cycle": "季度（盯ABB/西门子能源/特变电工季报交期数据）",
        },
        "新能源装机增速→电网消纳压力": {
            "value": "6月新增3825个新能源项目(风电32+光伏3787)。截至5月底全国装机突破40.1亿kW(非化石62%)",
            "trend": "up",
            "note": "新能源装机>电网消纳能力=弃风弃光=倒逼电网投资。装机增速越快→电网改造越紧迫→设备需求越确定。煤电占比已降至32%(2010年>60%)",
            "update_cycle": "月度（国家能源局，每月15日前后）",
            "last_updated": "2026-07-21",
        },
        "铜/硅钢价格 YoY【成本端】": {
            "value": "铜$9,800(+12%) 硅钢¥8,500/吨(+5%)",
            "trend": "flat",
            "note": "铜+硅钢占变压器/电缆成本50%+。当前温和上涨但未暴涨→成本压力可控。若铜价破$11,000=毛利显著承压→需警惕",
            "update_cycle": "日度（铜HG=F）+月度（硅钢）",
        },
    },

    # ═══ 机器人 · 人形机器人产业链（Bottleneck：核心零部件卡脖子） ═══
    # 5层链：人形机器人量产→执行器总成→减速器/丝杠/传感器→精密磨床/绕线机→钕铁硼/特种钢
    # 瓶颈原型：②HD谐波减速器垄断 ②行星滚柱丝杠进口垄断 ②六维力传感器进口垄断 ⑥螺纹磨床设备瓶颈 ①稀土磁材垄断
    "020608": {
        "绿的谐波 谐波减速器订单积压【②HD垄断→国产替代】": {
            "value": "H1营收同比+42%，出货创新高。墨西哥工厂设备调试中，2027年满产目标100万台/年",
            "trend": "up",
            "note": "【②单源卡脖子】H1业绩超预期验证需求强劲。日本HD占全球>60%，绿的谐波是国内唯一量产厂商。三次谐波新技术传动精度<10弧秒。Tesla Optimus Q2确认年内Fremont投产→下游需求确定性增强",
            "update_cycle": "季报后（4/8/10月底）+ 特斯拉季报",
            "last_updated": "2026-07-28",
        },
        "行星滚柱丝杠 国产良率突破【②进口垄断+③产能售罄】": {
            "value": "国产良率~60%（海外>85%），全球年产能仅120万套，缺口>400万套",
            "trend": "flat",
            "note": "【②+③叠加=最强瓶颈】行星滚柱丝杠占整机BOM 14-19%，单台Optimus需10-14根，是价值量最高的单一零部件。瑞士Rollvis/GSA/Ewellix垄断全球>80%。国产恒立液压已获特斯拉小批量订单，良率从40%→60%是关键突破。五洲新春反向丝杠规划100万套/年。若良率突破80%→国产替代拐点确认",
            "update_cycle": "季报后 + 特斯拉供应链动态",
        },
        "六维力传感器 送样验证进度【②进口垄断→精度追赶】": {
            "value": "国产化率<30%，是核心零部件中最低品类。柯力传感已获特斯拉盐雾测试通过",
            "trend": "up",
            "note": "【②传感器瓶颈】ATI/OnRobot占全球>70%。技术差距在精度(国产0.5-1%FS vs 海外0.2%FS)和良率(40-60% vs 90%+)。但国产价格仅为进口1/3。柯力传感月出货突破1000只、送样70+客户。工信部2026年将其纳入专项支持。2028-2029年国产化率预计60-70%",
            "update_cycle": "季报后 + 柯力传感月度出货跟踪",
        },
        "日发精机 数控螺纹磨床出货【⑥设备瓶颈+⑦前机构冷门】": {
            "value": "SK76系列已交付五洲新春/贝斯特/领益智造，丝杠装配线2026年10月交付",
            "trend": "up",
            "note": "【⑥⑦=被忽视的卖铲人】行星滚柱丝杠疯狂扩产→但加工丝杠的精密螺纹磨床本身也产能有限！日发精机是国内唯一量产数控螺纹磨床的公司（精度微米级）。欧洲/日本设备交期12-18月→国产设备替代窗口打开。当前市值小、卖方覆盖少，是真正的'卖铲子'冷门标的",
            "update_cycle": "季度（盯日发精机公告+合同签署）",
        },
        "钕铁硼出口管制→海外产能转移【①材料垄断→结构重构】": {
            "value": "2026年初对日稀土出口清零，日企高端产线关停，中国承接75%转移订单",
            "trend": "up",
            "note": "【①上游材料垄断】一台Optimus消耗3.2-4.5kg高性能钕铁硼(N52-UH级)。中国垄断全球90%稀土加工+出口管制=永久性结构重构。日本信越/Proterial/TDK断供→订单流向金力永磁/中科三环。金力永磁是特斯拉Optimus独家磁材供应商，墨西哥基地规避关税",
            "update_cycle": "季度（盯稀土出口数据+金力永磁季报）",
        },
    },

    # ═══ 存储芯片 · 全球存储产业链（Bottleneck：②HBM三寡头+③产能售罄） ═══
    # 5层链：AI服务器→NVDA GPU→HBM→存储原厂→设备/材料
    # 瓶颈原型：②SK海力士/三星/美光三寡头 ③HBM产能售罄 ①EMC材料垄断
    "STORAGE": {
        "DRAM合约价 QoQ【②寡头定价→③产能售罄】": {
            "value": "Q2 DDR5合约价+12% QoQ，HBM3e+18% QoQ。2026H2预计+8~13%",
            "trend": "up",
            "note": "【②→③核心指标】DRAM合约价=全球存储周期温度计。价格涨幅收窄(从+18%→+12%)=周期从加速进入匀速，但绝对值仍在涨。关键：涨幅减速≠下跌。若连续2季涨幅<5%→警惕见顶",
            "update_cycle": "月度（TrendForce/集邦，每月上旬）",
        },
        "HBM产能扩张→供需缺口【③产能售罄→供给刚性】": {
            "value": "SK海力士HBM3e 2026产能售罄，2027预购>60%。三星HBM4 2026Q4试产。美光HBM3e爬坡中。三家合计产能不足满足AI需求",
            "trend": "up",
            "note": "【③供给刚性】HBM扩产需要18-24月（建洁净室+TC键合机交期），短期供给完全刚性。需求增速(GPU出货×HBM配置量)远超供给增速→价格只涨不跌。若三家同时宣布大规模扩产(2028达产)→警惕供给过剩",
            "update_cycle": "季度（盯SK海力士/三星/美光季报+法说会）",
        },
        "NAND Flash合约价 QoQ【②寡头→库存周期】": {
            "value": "Q2 NAND合约价+8% QoQ，涨幅收窄。铠侠/WDC产能利用率回升至85%",
            "trend": "flat",
            "note": "【②库存周期】NAND比DRAM周期更短(6-12月)。涨幅收窄=供给在追赶。若NAND先于DRAM转跌→是DRAM周期的早期预警。铠侠/WDC合并影响供给格局",
            "update_cycle": "月度（TrendForce）",
        },
        "CXMT HBM量产进度【②国产替代→打破三寡头】": {
            "value": "7/27科创板上市募资579亿。HBM3量产锁定2026年，HBM3E 2027年。月产能30万片→2026底35万片→2030年60万片",
            "trend": "up",
            "note": "【②国产替代】CXMT(长鑫存储)中国唯一DRAM大厂(全球份额~8%)。HBM3量产=中国进入HBM赛道→利好A股存储模组(国产替代订单)。对海外原厂短期威胁有限(技术差2-3年)。CXMT最大瓶颈:无EUV→HBM良率受限",
            "update_cycle": "季度（盯CXMT季报+扩产公告）",
            "last_updated": "2026-07-29",
        },
        "全球存储原厂CapEx→供给前瞻【⑥设备→②扩产→价格】": {
            "value": "SK海力士$28B(+40% YoY)+三星$42B(+25%)+美光$14B(+30%)=合计$84B",
            "trend": "up",
            "note": "【⑥设备→供给前瞻】存储厂CapEx→设备采购→18-24月后产能释放→价格见顶信号。当前仍在加速=需求预期好。若CapEx增速>30%持续2年+→往往预示供给过剩。尚早",
            "update_cycle": "季报后（盯SK海力士/三星/美光CapEx指引）",
        },
    },
}

# ── 各板块关键事件日期 ─────────────────────

KEY_DATES = {
    "019633": [
        {"date": date(2026, 7, 10), "event": "台积电 6 月营收", "importance": "critical",
         "result": "6月营收 NT$2,484亿（+32% YoY），Q2合计 NT$6,735亿（+31% YoY），双超预期。CoWoS 满载，3nm/5nm 产能利用率 100%"},
        {"date": date(2026, 7, 16), "event": "台积电 Q2 法说会 ⚠", "importance": "critical",
         "result": "Q2营收1.27兆NTD(+36% YoY)创新高，毛利率67.7%超预期。CoWoS年底月产能14万片(2027→17万)。Capex上调至$600-640亿。全年美元营收上修至+40%。魏哲家：2030年前产能仍难满足AI需求"},
        {"date": date(2026, 7, 17), "event": "ASML Q2 财报",     "importance": "critical",
         "result": "营收€93.27亿(+21% YoY)超预期，EUV出货16台。全年指引上修至€430-450亿。2027年EUV产能+30%至~85台。High-NA EUV已用于Intel 18A量产"},
        {"date": date(2026, 7, 21), "event": "SEMI 6月 Billings", "importance": "critical",
         "result": "B/B值0.98(连续两月<1)。6月订单$15.1B(-2.6% MoM, +3.5% YoY)，出货$15.4B(+16.2% YoY)。H1维持正增长，但短期订单动能放缓"},
        {"date": date(2026, 7, 28), "event": "SK海力士 Q2 财报(HBM)", "importance": "critical",
         "result": "营收$54.55B(+257% YoY), 营业利润$60.5T KRW(+557% YoY)均略低于预期。HBM4 Q2开始量产，HBM4E 2027年量产。与NVDA签$500B战略协议。盘后跌9%→V型反转"},
        {"date": date(2026, 7, 27), "event": "GOOGL Q2 财报",    "importance": "high",
         "result": "营收$119.8B(+24% YoY)超预期。云业务+82%至$24.77B。Capex $44.9B(翻倍)，全年指引上调至$195-205B。FCF首次转负(-$5.9B)。盘后跌7%后回稳"},
        {"date": date(2026, 7, 29), "event": "MSFT Q2 财报",     "importance": "high",
         "result": "Azure+43%加速超预期，Capex$41B(+70%)。全年指引微调至$175B(会计变更)。签署$130B数据中心租约。云增速打消AI投入回报疑虑→盘后+9%"},
        {"date": date(2026, 7, 30), "event": "META Q2 财报",     "importance": "high",
         "result": "营收$60.8B(+28%)超预期但EPS$6.18不及预期。Capex$31.1B翻倍，FCF骤降91%至$0.78B。全年Capex上调至$130-145B。Q3指引偏弱→盘后-10%"},
        {"date": date(2026, 8, 1),  "event": "AMZN Q2 财报",     "importance": "high",
         "result": "营收$200.6B(+20% YoY)超预期。AWS $42.2B(+37%)创四年新高，运营利润率39.4%刷新纪录。全年Capex上调至$220B(原$200B)。盘后+10%→AI投入回报全面验证"},
        {"date": date(2026, 8, 15), "event": "中芯国际 Q2 财报 ⚠", "importance": "critical"},
        {"date": date(2026, 8, 15), "event": "中国集成电路 7月产量", "importance": "high"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报(CapEx风向标)", "importance": "critical"},
        {"date": date(2026, 8, 21), "event": "SEMI 7月 Billings", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "中微公司 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 26), "event": "北方华创 Q2 财报(预计) ⚠", "importance": "critical"},
        {"date": date(2026, 8, 28), "event": "拓荆科技 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 9, 10), "event": "中国集成电路 8月产量", "importance": "high"},
        {"date": date(2026, 9, 20), "event": "SEMI 8月 Billings", "importance": "high"},
        {"date": date(2026, 9, 25), "event": "美光 Q4 FY2026 财报(存储→设备)", "importance": "high"},
        {"date": date(2026, 10, 15), "event": "台积电 Q3 法说会(预计) ⚠", "importance": "critical"},
        {"date": date(2026, 10, 15), "event": "ASML Q3 财报(EUV订单)", "importance": "critical"},
    ],
    "014194": [
        {"date": date(2026, 7, 10),  "event": "台积电 6 月营收",        "importance": "high",
         "result": "6月营收 +32% YoY，先进制程满产，利好国产设备订单预期"},
        {"date": date(2026, 7, 15),  "event": "中国集成电路 6 月产量",    "importance": "high",
         "result": "6月517亿块(+18.8% YoY)。H1累计2798亿块(+23.1% YoY)，日均>15亿块。AI高端芯片+存储需求爆发是主驱动力"},
        {"date": date(2026, 7, 16),  "event": "台积电 Q2 法说会 ⚠",     "importance": "critical",
         "result": "CoWoS年底月产能14万片→2027年17万片，3nm/5nm满载。先进制程+先进封装持续供不应求→国产设备替代窗口延长"},
        {"date": date(2026, 7, 17),  "event": "ASML Q2 财报(EUV订单)",   "importance": "critical",
         "result": "全年营收指引€430-450亿(上调16%)，2027 EUV产能+30%。中国占比降至14%(前期采购消化)。EUV交期18月+=供给刚性"},
        {"date": date(2026, 7, 20),  "event": "北方华创 H1 业绩预告(预计)", "importance": "critical",
         "result": "未发布正式预告。Q1营收103.23亿(+25.8%)，归母净利16.35亿(+3.4%)。研发投入+37%压制利润。半年报预计8/26披露"},
        {"date": date(2026, 7, 27),  "event": "长鑫存储(CXMT)科创板上市 ⚠", "importance": "critical",
         "result": "IPO募资579亿，首日+466%收49元，市值3.28万亿成A股最大。DRAM月产能30万片→2026底35万片→2030年60万片。HBM3量产锁定2026"},
        {"date": date(2026, 8, 15),  "event": "中芯国际 Q2 财报 ⚠",    "importance": "critical"},
        {"date": date(2026, 8, 15),  "event": "中国集成电路 7月产量",    "importance": "high"},
        {"date": date(2026, 8, 20),  "event": "NVDA Q2 财报(全球芯片风向标)", "importance": "critical"},
        {"date": date(2026, 8, 21),  "event": "SEMI 7月 Billings",    "importance": "critical"},
        {"date": date(2026, 8, 25),  "event": "韦尔股份 Q2 财报(预计)",   "importance": "high"},
        {"date": date(2026, 8, 25),  "event": "兆易创新 Q2 财报(预计)",   "importance": "high"},
        {"date": date(2026, 8, 25),  "event": "中微公司 Q2 财报(预计)",   "importance": "high"},
        {"date": date(2026, 8, 26),  "event": "北方华创 Q2 财报(预计) ⚠", "importance": "critical"},
        {"date": date(2026, 9, 10),  "event": "中国集成电路 8月产量",    "importance": "high"},
        {"date": date(2026, 9, 20),  "event": "SEMI 8月 Billings",    "importance": "high"},
        {"date": date(2026, 10, 15), "event": "台积电 Q3 法说会(预计) ⚠", "importance": "critical"},
        {"date": date(2026, 10, 15), "event": "ASML Q3 财报(EUV订单)",  "importance": "critical"},
    ],
    "CPO": [
        {"date": date(2026, 7, 16), "event": "台积电 Q2 法说会 ⚠", "importance": "critical",
         "result": "Q2营收+36% YoY创新高，CoWoS年底14万片/月。AI算力需求持续爆炸→800G/1.6T光模块需求确定性极强"},
        {"date": date(2026, 7, 25), "event": "中际旭创 H1 业绩预告", "importance": "critical",
         "result": "未发布正式预告。公司7/13澄清：对H1经营和行业需求'非常有信心'，在手订单覆盖全年。半年报预计8/24披露"},
        {"date": date(2026, 8, 11), "event": "Lumentum Q4 FY2026 财报(光芯片)", "importance": "high",
         "result": "今日盘后发布。市场预期营收$987M(+105% YoY)，EPS $2.97。关键看点：1.6T光模块CW激光器出货量、EML供需缺口(>30%)。前季EPS $2.37超预期$0.10"},

        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报", "importance": "critical"},
        {"date": date(2026, 8, 24), "event": "中际旭创 半年报(预计) ⚠", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "新易盛 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "天孚通信 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 28), "event": "Marvell Q2 FY2027 财报(DSP芯片)", "importance": "critical"},
        {"date": date(2026, 9, 5),  "event": "Broadcom Q3 FY2026 财报(DSP+交换芯片)", "importance": "critical"},
        {"date": date(2026, 10, 15), "event": "台积电 Q3 法说会(CoWoS进度)", "importance": "high"},
    ],
    "024239": [
        {"date": date(2026, 7, 16), "event": "台积电 Q2 法说会 ⚠", "importance": "critical",
         "result": "CoWoS年底14万片/月(2027→17万)。Capex上调至$600-640亿。2030年前产能仍难满足AI需求→GPU出货瓶颈短期无解"},
        {"date": date(2026, 7, 17), "event": "ASML Q2 财报(EUV订单)", "importance": "critical",
         "result": "全年指引上修至€430-450亿。2027 EUV产能+30%。EUV交期18月+=GPU产能扩张的最上游硬约束"},
        {"date": date(2026, 7, 28), "event": "SK海力士 Q2 财报(HBM)", "importance": "critical",
         "result": "HBM4 Q2量产，HBM4E 2027量产。10家客户签长协。HBM营收占比持续提升→设备+材料需求刚性确认"},
        {"date": date(2026, 7, 27), "event": "GOOGL Q2(CapEx指引)", "importance": "critical",
         "result": "Capex翻倍至$44.9B，全年$195-205B(上调)。云业务+82%→AI投资回报开始兑现。⚠ FCF首次转负"},
        {"date": date(2026, 7, 29), "event": "MSFT Q2(CapEx指引)", "importance": "critical",
         "result": "Capex$41B(+70%), 下季>$50B。Azure+43%验证AI投入回报。云容量仍受限至少到2026底→AI硬件需求刚性"},
        {"date": date(2026, 7, 30), "event": "META Q2(CapEx指引)+三星Q2", "importance": "high",
         "result": "META Capex$31.1B翻倍, 全年上调至$130-145B。FCF骤降91%引发担忧但AI投入未减速。盘后-10%"},
        {"date": date(2026, 8, 1),  "event": "AMZN Q2(CapEx指引)", "importance": "high",
         "result": "AWS+37%加速→运营利润率39.4%创新高。全年Capex上调至$220B。四云厂Q2 Capex合计~$170B→年化$680B+。AI投资回报疑虑彻底打消"},
        {"date": date(2026, 8, 10), "event": "SMCI Q4 FY2026 财报(AI服务器)", "importance": "high",
         "result": "今日盘后发布。Q4营收指引$11-12.5B近下限，但毛利率意外上调至15-17%(翻倍)。Q4新订单>$60B创纪录。Q3营收$10.2B(+123% YoY)"},

        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报 ⚠", "importance": "critical"},
        {"date": date(2026, 9, 5),  "event": "AVGO Q3 FY2026 财报(ASIC+网络)", "importance": "high"},
        {"date": date(2026, 9, 10), "event": "台积电 8月营收", "importance": "high"},
        {"date": date(2026, 9, 25), "event": "美光 Q4 FY2026 财报(HBM→GPU)", "importance": "high"},
        {"date": date(2026, 10, 15), "event": "台积电 Q3 法说会(预计) ⚠", "importance": "critical"},
        {"date": date(2026, 10, 15), "event": "ASML Q3 财报(EUV订单)", "importance": "critical"},
        {"date": date(2026, 10, 15), "event": "SK海力士 Q3 财报(HBM)", "importance": "critical"},
        {"date": date(2026, 10, 27), "event": "GOOGL Q3 财报(CapEx指引)", "importance": "high"},
        {"date": date(2026, 10, 29), "event": "MSFT Q3 财报(CapEx指引)", "importance": "high"},
    ],
    "021528": [
        {"date": date(2026, 7, 20), "event": "深南电路 H1 业绩预告(预计)", "importance": "critical",
         "result": "归母净利21-23亿(+54-69% YoY)，扣非+64-80%。AI算力+存储双驱动。无锡AI算力PCB项目(投资45亿)预计2027H1量产"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报(服务器需求)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "沪电股份 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "深南电路 半年报(预计)", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "东山精密 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "胜宏科技 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "生益科技 Q2 财报(CCL上游)", "importance": "high"},
        {"date": date(2026, 9, 10), "event": "台积电 8月营收(服务器需求)", "importance": "high"},
        {"date": date(2026, 10, 15), "event": "台积电 Q3 法说会(AI服务器展望)", "importance": "high"},
    ],
    "015789": [
        {"date": date(2026, 7, 15), "event": "SpaceX H1 发射统计", "importance": "high",
         "result": "H1完成75次发射(59次Starlink)，部署1589颗卫星。年化150次+。全球发射占比>60%，垄断地位稳固"},
        {"date": date(2026, 8, 10), "event": "Rocket Lab Q2 财报", "importance": "high",
         "result": "Q2营收$156M(+37% YoY)，Electron发射9次。Neutron首飞推迟至2026Q4。积压订单$1.3B。注意：当前015789已改为军工电子映射，RKLB财报对基金影响有限"},

        {"date": date(2026, 8, 25), "event": "中国卫星 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "航天电子 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "中科星图 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 9, 1),  "event": "SpaceX 7-8月发射统计", "importance": "high"},
        {"date": date(2026, 10, 1), "event": "中国航天发射计划H2更新", "importance": "high"},
        {"date": date(2026, 10, 15), "event": "中国星网 第二批卫星发射(预计)", "importance": "critical"},
    ],
    "025856": [
        {"date": date(2026, 7, 15), "event": "6月新能源装机数据", "importance": "high",
         "result": "6月新增3825个项目(风电32+光伏3787)。截至5月底全国装机突破40.1亿kW，非化石能源占62%"},
        {"date": date(2026, 7, 20), "event": "国网 H1 投资进度公告(预计)", "importance": "critical",
         "result": "Q1固投1290亿(+37% YoY)。H1物资招标>2500亿(+17%)。110kV+工程投产完成年度53%。7月特高压第三批招标108.7亿"},
        {"date": date(2026, 8, 15), "event": "7月新能源装机数据", "importance": "high"},
        {"date": date(2026, 8, 20), "event": "国网 7月物资招标数据(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "许继电气 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "中国西电 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "四方股份 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "特变电工 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 30), "event": "国电南瑞 Q2 财报(预计) ⚠", "importance": "critical"},
        {"date": date(2026, 9, 15), "event": "8月新能源装机数据", "importance": "high"},
        {"date": date(2026, 9, 15), "event": "国网 H2 投资计划修订(预计)", "importance": "critical"},
        {"date": date(2026, 10, 15), "event": "9月新能源装机数据", "importance": "high"},
    ],
    "020608": [
        {"date": date(2026, 7, 15), "event": "6月工业机器人产量", "importance": "high",
         "result": "6月11.07万套(+28.1% YoY)，H1累计+28.0%。连续多月>25%高增，制造业自动化加速"},
        {"date": date(2026, 7, 22), "event": "Tesla Q2 财报(Optimus进度) ⚠", "importance": "critical",
         "result": "营收$28.24B(+26% YoY)超预期但EPS$0.33不及预期。Optimus按计划年内Fremont投产，先内部使用('Optimus Academy')。2026 Capex>$25B"},
        {"date": date(2026, 7, 25), "event": "绿的谐波 H1 业绩预告(预计)", "importance": "critical",
         "result": "H1营收同比+42%，谐波减速器出货创新高。墨西哥工厂进入设备调试阶段，2027年满产目标100万台/年"},
        {"date": date(2026, 8, 5),  "event": "柯力传感 Q2 财报(六维力出货) ⚠", "importance": "critical",
         "result": "H1预告净利润同比+76~132%。六维力传感器出货近千套，部分客户已获批量订单(含特斯拉盐雾测试通过)。Q1归母净利-45.65%(研发投入加大)，Q2显著反转。处于商业化关键推进期"},

        {"date": date(2026, 8, 15), "event": "7月工业机器人产量", "importance": "high"},
        {"date": date(2026, 8, 15), "event": "世界机器人大会(北京) ⚠", "importance": "critical"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报(机器人平台)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "恒立液压 Q2 财报(丝杠进度)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "绿的谐波 Q2 财报 ⚠", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "金力永磁 Q2 财报(磁材出货)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "日发精机 Q2 财报(磨床出货)", "importance": "high"},
        {"date": date(2026, 9, 1),  "event": "日发精机 丝杠装配线交付节点", "importance": "high"},
        {"date": date(2026, 9, 15), "event": "8月工业机器人产量", "importance": "high"},
        {"date": date(2026, 9, 15), "event": "Tesla AI Day 2026(预计) ⚠", "importance": "critical"},
    ],
    "STORAGE": [
        {"date": date(2026, 7, 28), "event": "SK海力士 Q2 财报(HBM)", "importance": "critical",
         "result": "HBM4 Q2量产，HBM4E 2027量产。营收$54.55B(+257% YoY)。与NVDA签$500B战略协议。盘后跌9%→V型反转"},
        {"date": date(2026, 7, 30), "event": "三星 Q2 财报(存储)", "importance": "critical",
         "result": "存储营收$38.2B(+89% YoY)。HBM4 2026Q4试产。DRAM位元增长率12%。盘后+3%"},
        {"date": date(2026, 8, 10), "event": "TrendForce 7月DRAM合约价 ⚠", "importance": "critical",
         "result": "Q3服务器DRAM合约价+13~18% QoQ(较Q2的~50%显著放缓)。消费端需求疲软，买方抵触涨价。HBM产能挤压仍在持续→供给偏紧。关键信号：涨幅从加速→匀速，周期进入mid阶段"},

        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报(HBM需求)", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "兆易创新 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "北京君正 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 9, 10), "event": "TrendForce 8月DRAM合约价", "importance": "high"},
        {"date": date(2026, 9, 25), "event": "美光 Q4 FY2026 财报 ⚠", "importance": "critical"},
        {"date": date(2026, 10, 10), "event": "TrendForce 9月DRAM合约价", "importance": "high"},
        {"date": date(2026, 10, 15), "event": "SK海力士 Q3 财报(HBM) ⚠", "importance": "critical"},
        {"date": date(2026, 10, 15), "event": "三星 Q3 财报(存储)", "importance": "critical"},
    ],
}

# ── 各板块周期位置判断（手动评估）───────────

CYCLE_ASSESSMENTS = {
    "019633": {
        "stage": "early",
        "label": "国产替代早期（设备自主化加速期）",
        "note": "【国产替代主题】外部制裁收紧+CXMT上市扩产+SMIC Capex扩张→国产设备订单确定性高。全球半导体设备周期波动对A股设备商影响有限——国内Fab扩产节奏才是核心变量。关键指标：北方华创合同负债、CXMT扩产进度、中芯国际Capex。",
        "risk": "green",
    },
    "014194": {
        "stage": "early",
        "label": "国产替代早期（独立于全球周期）",
        "note": "【Bottleneck主题】被卡脖子→必须自己造。政策驱动而非周期性，CapEx确定性来自国家安全而非商业回报率。核心瓶颈在Layer2设备（北方华创/中微）和Layer1材料（光刻胶/大硅片），已识别的瓶颈原型：①②⑥⑧。当前合同负债+18%、Capex/折旧1.8x=扩张中，但光刻胶进口依存度仍78%说明替代还在早期。",
        "risk": "green",
    },
    "CPO": {
        "stage": "early",
        "label": "800G→1.6T过渡期（Bottleneck主题）",
        "note": "【Bottleneck】AI集群带宽需求爆炸→光互联是数据中心的神经系统。核心瓶颈在②DSP芯片（Marvell/Broadcom双垄断）+①InP衬底（AXTI/IQE >70%）。当前800G产能售罄、1.6T刚起步=早期扩张阶段。NVDA Rubin架构(2027)将推动1.6T/CPO大规模部署，届时中际旭创/新易盛是直接受益者。",
        "risk": "green",
    },
    "024239": {
        "stage": "mid-to-late",
        "label": "存储+代工周期中后期（Bottleneck主题）",
        "note": "【Bottleneck存储+代工】基金真实持仓：SanDisk+美光+Marvell+TSMC+Lumentum。核心逻辑：①存储周期(HBM/DDR5涨价)②TSMC代工产能紧张③光芯片需求(Lumentum)。三重驱动力都是AI基础设施的'卖铲人'。H2关键变量：①美光Q4 FY2026(9/25)→存储价格拐点确认 ②TSMC Q3法说会(10/15)→3nm/5nm产能利用率 ③NVDA Rubin架构HBM需求(8/20 Q2)。",
        "risk": "yellow",
    },
    "021528": {
        "stage": "mid",
        "label": "电子上游扩张期（Evolution+Bottleneck）",
        "note": "【电子材料+光通信】基金真实持仓：新易盛+南亚新材(CCL)+源杰科技(光芯片)+三环集团(陶瓷)+德福科技(铜箔)。电子上游材料+光芯片双重逻辑：①CCL/铜箔→AI服务器PCB上游 ②光芯片→800G/1.6T光模块核心卡点。关注：南亚新材产能利用率、源杰科技CW激光器送样验证、铜箔加工费趋势。",
        "risk": "green",
    },
    "015789": {
        "stage": "mid",
        "label": "军工电子景气期（国防+电子双驱动）",
        "note": "【国防电子】基金真实持仓：信维通信+航天电子+睿创微纳(红外)+国博电子(射频芯片)+飞沃科技。军工电子双逻辑：①国防预算增长→红外/射频芯片订单确定 ②商业航天发射→航天电子配套。不同于纯航天卫星（发射产能瓶颈），军工电子更侧重元器件国产化+国防信息化。关注：睿创微纳红外探测器出货、国博电子射频芯片订单。",
        "risk": "green",
    },
    "025856": {
        "stage": "mid",
        "label": "电网改造扩张期（Evolution主题）",
        "note": "【Evolution】新能源装机暴增→电网消纳能力不足→电网投资确定性高。核心瓶颈在③变压器产能（全球交期18-24月）。不同于科技板块的情绪驱动，电网设备是政策+物理需求驱动：变压器不够就是不够，没有替代方案。关注：国网H1投资进度、特高压项目批复、铜/硅钢价格。风险在成本端而非需求端。",
        "risk": "green",
    },
    "020608": {
        "stage": "early",
        "label": "人形机器人量产前夜（Bottleneck主题，5瓶颈原型交叉）",
        "note": "【Bottleneck密集区】人形机器人是当前瓶颈密度最高的赛道之一：①钕铁硼磁材中国垄断+出口管制→结构重构 ②HD谐波减速器→绿的谐波突破 ②行星滚柱丝杠进口垄断→恒立液压/五洲新春追赶 ②六维力传感器<30%国产化 ⑥精密螺纹磨床被忽视的卖铲人。Tesla Q2(7/22)确认Optimus年内Fremont投产，年底目标稳定2000-2500台/周，产业链各层级的瓶颈紧张度将逐层暴露。最适合埋伏的是【⑥⑦设备层(日发精机)+①材料层(金力永磁)】——机构覆盖少、但产能扩张绕不开。关键变量：①绿的谐波/恒立液压H1→验证订单放量(✅绿的+42%已确认) ②行星滚柱丝杠良率突破60%→80%是关键阈值 ③8月机器人大会+9月Tesla AI Day。",
        "risk": "green",
    },
    "STORAGE": {
        "stage": "early",
        "label": "存储周期上行早期（HBM扩张+DRAM涨价双轮驱动）",
        "note": "【Bottleneck双瓶颈】②HBM三寡头+③产能售罄。2024年底DRAM走出周期底部→2025-2026涨价加速→HBM更是独立于DRAM周期的超级赛道(每代GPU配更多HBM→需求不可逆增长)。当前DRAM涨幅从'加速'进入'匀速'(+18%→+12%)表明仍在上行但斜率放缓→early而非mid。真正的mid信号:涨幅连续2季<5%。关键变量:①NVDA Rubin架构HBM配置量(8/20 Q2) ②三家HBM扩产是否如期 ③DRAM合约价月度变化",
        "risk": "green",
    },
}

# ══════════════════════════════════════════════════════════
# 通用配置
# ══════════════════════════════════════════════════════════

# 逃跑等级映射
EXIT_LEVELS = [
    (2,  "安心持有", "🟢", "当前无异常信号，按计划持有"),
    (4,  "继续持有", "🟢", "有轻微信号但无需操作，保持关注"),
    (6,  "提高警惕", "🟡", "部分信号触发，减少新开仓"),
    (8,  "考虑减仓", "🟠", "多项警告触发，建议减仓 30-50%"),
    (10, "果断逃跑", "🔴", "强烈建议大幅减仓或清仓"),
]

# ══════════════════════════════════════════════════════════
# P0-任务1：共享瓶颈簇定义
# ══════════════════════════════════════════════════════════

# 每个瓶颈标签的描述 + 依赖它的板块列表
BOTTLENECK_CLUSTERS = {
    "euv": {
        "label": "ASML EUV 垄断",
        "desc": "全球唯一 EUV 供应商，交期 18 月+",
        "funds": ["014194", "024239"],  # 芯片指数 / AI硬件
    },
    "cowos": {
        "label": "TSMC CoWoS 先进封装",
        "desc": "所有 AI GPU 必经之路，产能紧张",
        "funds": ["019633", "024239"],  # 半导体设备 / AI硬件
    },
    "hbm": {
        "label": "HBM 内存三寡头",
        "desc": "SK 海力士/三星/美光垄断，2026 产能售罄",
        "funds": ["019633", "024239"],  # 半导体设备 / AI硬件
    },
    "cloud_capex": {
        "label": "云厂 CapEx 周期",
        "desc": "四大 Hyperscaler 资本开支决定全链需求",
        "funds": ["019633", "024239", "CPO", "021528"],  # 半导体+AI硬件+CPO+PCB
    },
    "dsp_duopoly": {
        "label": "DSP 芯片双垄断",
        "desc": "Marvell/Broadcom 垄断 800G/1.6T DSP",
        "funds": ["CPO"],  # CPO
    },
    "inp_substrate": {
        "label": "InP 衬底垄断",
        "desc": "AXTI/IQE 占全球 >70% InP 衬底",
        "funds": ["CPO"],  # CPO
    },
    "launch_capacity": {
        "label": "发射产能单源",
        "desc": "SpaceX 占全球发射 >60%",
        "funds": ["015789"],  # 航天卫星
    },
    "transformer_capacity": {
        "label": "变压器产能售罄",
        "desc": "全球大型变压器交期 18-24 月",
        "funds": ["025856"],  # 电网设备
    },
    "gov_budget": {
        "label": "政府/国防预算驱动",
        "desc": "航天+电网受政策预算周期影响",
        "funds": ["015789", "025856"],  # 航天卫星 / 电网设备
    },
    "harmonic_reducer": {
        "label": "谐波减速器 HD 垄断",
        "desc": "日本 HD 占全球 >60%，绿的谐波国内唯一量产替代",
        "funds": ["020608"],
    },
    "planetary_roller_screw": {
        "label": "行星滚柱丝杠进口垄断",
        "desc": "瑞士 Rollvis/GSA/Ewellix 垄断 >80%，国产良率仅 60%",
        "funds": ["020608"],
    },
    "six_axis_force_sensor": {
        "label": "六维力传感器进口垄断",
        "desc": "ATI/OnRobot 占全球 >70%，国产化率 <30%，最大短板",
        "funds": ["020608"],
    },
    "thread_grinder_equipment": {
        "label": "精密螺纹磨床设备瓶颈",
        "desc": "日发精机国内唯一量产，欧洲/日本设备交期 12-18 月",
        "funds": ["020608"],
    },
    "ndfeb_magnet_monopoly": {
        "label": "钕铁硼稀土磁材垄断",
        "desc": "中国垄断全球 90% 加工 + 出口管制 → 永久结构重构",
        "funds": ["020608"],
    },
    "optimus_catalyst": {
        "label": "Tesla Optimus 量产催化剂",
        "desc": "Optimus V3 定型 + 周产目标 2000-2500 台 = 最强情绪驱动",
        "funds": ["020608"],
    },
    "hbm_triopoly": {
        "label": "HBM 内存三寡头",
        "desc": "SK海力士(53%)+三星(35%)+美光(12%)垄断，2026产能售罄",
        "funds": ["STORAGE"],
    },
    "dram_oligopoly": {
        "label": "DRAM/NAND 寡头垄断",
        "desc": "全球存储供给高度集中(>90%)，定价权在海外原厂",
        "funds": ["STORAGE"],
    },
}

# 共享瓶颈阈值：依赖同一标签的板块数≥3且全部🟢时触发警告
BOTTLENECK_CONCENTRATION_WARN = 3

# ══════════════════════════════════════════════════════════
# P0-任务2：核心共享指标 & 联动降级规则
# ══════════════════════════════════════════════════════════

# key = 共享指标在 LEADING_INDICATORS 中的显示名关键词（用于匹配）
SHARED_INDICATORS = {
    "四大云厂 CapEx": {
        "tag": "cloud_capex",
        "funds": ["019633", "024239", "CPO", "021528"],
        "cascade_weight": 2,  # 恶化时扣几分
    },
    "台积电月度营收": {
        "tag": "cowos",
        "funds": ["019633", "014194", "CPO"],
        "cascade_weight": 2,
    },
    "DRAM 合约价": {
        "tag": "hbm",
        "funds": ["019633", "024239"],
        "cascade_weight": 1,
    },
    "SEMI 北美设备 Billings": {
        "tag": "euv",
        "funds": ["019633", "024239"],
        "cascade_weight": 1,
    },
    "CoWoS 产能": {
        "tag": "cowos",
        "funds": ["019633", "024239"],
        "cascade_weight": 2,
    },
    "HBM 产能/DRAM合约价": {
        "tag": "hbm",
        "funds": ["STORAGE", "019633"],
        "cascade_weight": 2,
    },
}

# ══════════════════════════════════════════════════════════
# P0-任务4：瓶颈破坏条件清单
# ══════════════════════════════════════════════════════════

# 每个核心瓶颈的"破坏条件" + 当前进度
# status: "none"(无进展) / "watching"(有苗头) / "breakthrough"(实质突破→硬触发)
BOTTLENECK_DISRUPTION = {
    "euv": {
        "label": "ASML EUV 垄断",
        "conditions": [
            {"desc": "中国自研 EUV 光刻机量产", "status": "none", "note": "暂无公开突破，SMEE 仍卡在 DUV"},
            {"desc": "纳米压印技术 (NIL) 商用化替代 EUV", "status": "none", "note": "Canon NIL 仍在研发，未进入量产"},
        ],
        "affected_funds": ["014194", "024239"],
    },
    "cowos": {
        "label": "TSMC CoWoS 垄断",
        "conditions": [
            {"desc": "三星/Intel 先进封装达到同等良率", "status": "watching", "note": "三星 I-Cube 在验证中，但良率落后 TSMC"},
            {"desc": "NVDA 自研封装方案绕过 CoWoS", "status": "none", "note": "暂无公开信息"},
        ],
        "affected_funds": ["024239"],
    },
    "hbm": {
        "label": "HBM 三寡头垄断",
        "conditions": [
            {"desc": "中国 CXMT 量产 HBM2e 及以上", "status": "breakthrough", "note": "CXMT 7/27科创板上市募资579亿。HBM3量产锁定2026年，HBM3E目标2027年。DRAM自主化实质性突破",
             "positive_for": ["014194", "019633"]},
            {"desc": "新型存储 (CXL/存算一体) 替代 HBM", "status": "none", "note": "学术阶段，无商用时间表"},
        ],
        "affected_funds": ["019633"],
    },
    "launch_capacity": {
        "label": "SpaceX 发射产能垄断",
        "conditions": [
            {"desc": "Rocket Lab Neutron 首飞成功 + 常态化发射", "status": "watching", "note": "Neutron 2026H2 首飞，若成功将打破垄断"},
            {"desc": "中国商业航天公司实现可回收火箭", "status": "none", "note": "多家在研，尚无成功回收案例"},
        ],
        "affected_funds": ["015789"],
    },
    "transformer_capacity": {
        "label": "变压器产能瓶颈",
        "conditions": [
            {"desc": "全球变压器厂大规模扩产完成", "status": "none", "note": "扩产周期 3-5 年，短期内难以缓解"},
        ],
        "affected_funds": ["025856"],
    },
    "harmonic_reducer": {
        "label": "谐波减速器日本 HD 垄断",
        "conditions": [
            {"desc": "绿的谐波全球份额突破 30%（当前~25%）", "status": "watching", "note": "墨西哥工厂独家配套特斯拉，三次谐波技术差异化"},
            {"desc": "HD 在中国建厂降价反击", "status": "none", "note": "HD 当前策略是高端垄断而非价格战"},
            {"desc": "行星减速器等低成本方案部分替代谐波", "status": "watching", "note": "广发证券提示行星减速器可能替代部分谐波场景"},
        ],
        "affected_funds": ["020608"],
    },
    "planetary_roller_screw": {
        "label": "行星滚柱丝杠进口垄断",
        "conditions": [
            {"desc": "恒立液压/五洲新春良率突破 80%", "status": "watching", "note": "当前国产良率~60%，突破80%可规模替代进口"},
            {"desc": "国产丝杠进入特斯拉 Optimus 批量供应", "status": "watching", "note": "恒立液压已获小批量订单，五洲新春在验证中"},
            {"desc": "Rollvis/GSA 大规模扩产打破供给瓶颈", "status": "none", "note": "欧洲扩产保守，12-18月内难以改变格局"},
        ],
        "affected_funds": ["020608"],
    },
    "six_axis_force_sensor": {
        "label": "六维力传感器进口垄断",
        "conditions": [
            {"desc": "柯力传感精度达 0.2%FS（ATI同级）", "status": "watching", "note": "当前国产精度 0.5-1%FS，差距在缩小"},
            {"desc": "国产传感器进入特斯拉批量供应", "status": "watching", "note": "柯力传感已通过特斯拉盐雾测试，待批量定点"},
            {"desc": "工信部专项支持落地→国产替代加速", "status": "watching", "note": "2026年已纳入专项，宁波推出\"机智保\"降低试用门槛"},
        ],
        "affected_funds": ["020608"],
    },
    "thread_grinder_equipment": {
        "label": "精密螺纹磨床设备瓶颈",
        "conditions": [
            {"desc": "日发精机获主流丝杠厂批量订单", "status": "watching", "note": "已交付五洲新春/贝斯特，但尚未大规模量产"},
            {"desc": "欧洲/日本设备商扩产或缩短交期", "status": "none", "note": "高端磨床扩产周期长，短期无解"},
        ],
        "affected_funds": ["020608"],
    },
    "ndfeb_magnet_monopoly": {
        "label": "钕铁硼中国垄断+出口管制",
        "conditions": [
            {"desc": "海外建成稀土分离产能（Lynas/MP Materials）", "status": "watching", "note": "海外仅能分离轻稀土，镝铽仍100%依赖中国"},
            {"desc": "无重稀土配方突破→降低镝铽需求", "status": "watching", "note": "金力永磁晶界渗透已降镝铽50-70%，但在极限推进"},
        ],
        "affected_funds": ["020608"],
    },
    "optimus_catalyst": {
        "label": "Tesla Optimus 量产进度",
        "conditions": [
            {"desc": "Optimus 宣布对外销售时间表", "status": "watching", "note": "Q2财报(7/22)确认Optimus年内Fremont投产，先内部使用('Optimus Academy')。对外销售目标仍为2027年"},
            {"desc": "特斯拉周产稳定>2000台", "status": "watching", "note": "马斯克红线：2026年底稳定2000-2500台/周。Fremont产线建设是H2最关键跟踪指标"},
            {"desc": "Optimus 获得外部客户订单", "status": "none", "note": "目前仅有特斯拉内部使用计划，外部客户需等V3定型后"},
        ],
        "affected_funds": ["020608"],
    },
    "hbm_triopoly": {
        "label": "HBM三寡头垄断",
        "conditions": [
            {"desc": "CXMT HBM3量产+良率>70%→威胁三寡头", "status": "breakthrough",
             "note": "CXMT 7/27上市募资579亿，HBM3锁定2026。对海外原厂短期威胁有限(技术差2-3年)，但对A股存储模组是重大利好(国产替代订单)",
             "positive_for": ["STORAGE"]},
            {"desc": "CXL/存算一体替代HBM架构", "status": "none", "note": "学术阶段，无商用时间表"},
            {"desc": "三星/美光HBM市占率大幅提升→打破SK海力士独大", "status": "watching", "note": "三星HBM4 2026Q4试产，若良率突破→供给增加→价格上涨放缓"},
        ],
        "affected_funds": ["STORAGE"],
    },
}

# ══════════════════════════════════════════════════════════
# P1-任务5：周期判断反方假设
# ══════════════════════════════════════════════════════════

# 每个板块的周期判断补充"如果我错了"字段
# 从 CYCLE_ASSESSMENTS 中提取，作为补充字段
CYCLE_COUNTER_HYPOTHESIS = {
    "019633": "如果北方华创合同负债连续2季下滑+CXMT扩产进度延迟→国产替代逻辑松动，当前判断偏乐观",
    "014194": "如果光刻胶国产化突然加速(进口占比跌破60%) → 周期可能已入中期而非早期，当前判断偏保守",
    "CPO": "如果 NVDA Rubin 延迟到 2028 → 1.6T/CPO 大规模部署后移，当前\"早期\"判断可能需要等更久兑现",
    "024239": "如果 Q2 CapEx >+35% YoY → 三重瓶颈利润故事延续，中后期判断可能偏早",
    "021528": "如果铜价暴涨至 $12,000 → 成本端严重恶化，当前 mid 判断需要重新评估",
    "015789": "如果 Neutron 首飞失败 → 发射垄断短期内无解，早期阶段可能持续更久（利空商业航天板块）",
    "025856": "如果国网投资增速降至 <3% → 需求端逻辑弱化，当前 mid 判断偏高",
    "020608": "如果 Tesla Optimus 对外销售推迟到 2028+ 或量产良率持续<50% → 整条供应链的量产故事短期无法兑现，核心零部件厂商的机器人业务收入占比可能停滞在<10%，板块可能回调 30-50%",
    "STORAGE": "如果DRAM合约价连续2季涨幅<3%+三大原厂同时宣布2028年大规模扩产→存储周期从'涨价'变为'过剩预期'，当前early判断需要修正为mid-to-late",
}

# ══════════════════════════════════════════════════════════
# P1-任务6：技术面/基本面背离强制降级阈值
# ══════════════════════════════════════════════════════════

DIVERGENCE_DOWNGRADE_WEEKS = 2  # 持续N周背离 → 自动降级

# ══════════════════════════════════════════════════════════
# 复盘配置（Review Methodology 优化）
# ══════════════════════════════════════════════════════════

# 动态阈值：周涨跌标准差系数
DYNAMIC_THRESHOLD_COEFFICIENT = 0.5
DYNAMIC_THRESHOLD_LOOKBACK_DAYS = 60

# 小样本警告阈值
MIN_SAMPLE_SIZE_WARNING = 30

# 对照组：各板块对应的基准指数（用于计算超额收益）
CONTROL_BENCHMARKS = {
    "019633": "159995.SZ",  # 半导体设备 → 芯片ETF
    "014194": "000688.SS", # 芯片指数 → 科创50
    "CPO":     "159997.SZ", # CPO → 电子ETF
    "024239":  "^NDX",     # AI硬件 → 纳斯达克100
    "021528":  "159997.SZ", # PCB → 电子ETF
    "015789":  "512660.SS", # 航天卫星 → 军工ETF
    "025856":  "159611.SZ", # 电网设备 → 电力ETF
    "020608":  "000688.SS", # 机器人 → 科创50
    "STORAGE": "SMH",       # 存储芯片 → VanEck半导体ETF
}

# ══════════════════════════════════════════════════════════
# 叠层信号交易系统配置
# ══════════════════════════════════════════════════════════

TRADING_CONFIG = {
    # ── 仓位基础参数 ──
    "position": {
        "standard_size_pct": 10,       # 单只基金标准仓 = 总资产 × 10%
        "max_sector_pct": 20,          # 单板块上限
        "max_single_fund_pct": 15,     # 单只基金上限
        "min_cash_pct": 10,            # 现金下限
        "min_position_funds": 5,       # 最少持仓数
        "max_position_funds": 8,       # 最多持仓数
    },

    # ── Regime 判定阈值 ──
    "regime": {
        "panic_daily_drop_pct": -5,    # 单日跌幅 >5% → Panic
        "panic_rsi_count": 3,          # RSI<30 的成分股 ≥3 只 → Panic
        "panic_rsi_threshold": 30,
        "pre_event_hours": 48,         # 关键事件前 48h → Pre-Event
    },

    # ── 信号叠层权重 ──
    "signal_weights": {
        "L1_technical": 1.0,           # 技术面权重
        "L2_bottleneck": 2.0,          # 瓶颈面权重（核心）
        "L3_cycle": 1.5,               # 周期面权重
        "L4_event": 1.0,               # 事件面权重
    },

    # ── 买入阈值 ──
    "buy": {
        "signal_threshold": 4,         # 叠层得分 ≥4 才能买入
        "L2_minimum": 0,               # L2 瓶颈面不能为负
        "trend_filter": True,           # MA20 > MA60 趋势过滤
    },

    # ── 卖出阈值 ──
    "sell": {
        "signal_threshold": -4,        # 叠层得分 ≤-4 才能卖出
        "L2_required_negative": True,   # L2 必须为负才能基本面卖出
    },

    # ── RSI 分级加仓系数 ──
    "rsi_tiers": [
        {"rsi_max": 45, "rsi_min": 40, "coefficient": 0.3, "label": "轻度关注"},
        {"rsi_max": 40, "rsi_min": 35, "coefficient": 0.5, "label": "适度加仓"},
        {"rsi_max": 35, "rsi_min": 30, "coefficient": 0.8, "label": "积极加仓"},
        {"rsi_max": 30, "rsi_min": 0,  "coefficient": 1.0, "label": "重仓买入"},
    ],

    # ── 止盈三档（按周期调节） ──
    "profit_tiers": {
        "early":       [25, 40, 60],   # Tier 1/2/3 盈利%阈值
        "mid":         [20, 30, 45],
        "mid-to-late": [15, 22, 30],
        "late":        [10, 15, 20],
    },
    "profit_sell_pct": [25, 25, 50],    # Tier 1/2/3 分别卖出%

    # ── 技术过热阈值 ──
    "overheat": {
        "rsi": {
            "early": 80, "mid": 75, "mid-to-late": 70, "late": 65,
        },
        "kdj": 80,
        "sell_pct_rsi_kdj": 15,         # RSI+KDJ过热 → 卖15%
        "sell_pct_bollinger_macd": 15,  # Bollinger上轨+MACD死叉 → 卖15%
        "sell_pct_weekly_surge": 20,    # 单周涨>15%(A)/>10%(美股) → 卖20%
        "weekly_surge_a": 15,           # A股单周涨幅阈值
        "weekly_surge_us": 10,          # 美股单周涨幅阈值
    },

    # ── 时间止盈/止损 ──
    "time_based": {
        "idle_months": 6,               # 持仓>6月 收益±5% → 标记无效
        "idle_return_range": 5,         # ±5%
        "logic_weaken_months": 3,       # 持仓>3月 + 指标 up→flat
        "logic_weaken_sell_pct": 20,    # 减仓20%
        "force_review_months": 12,      # 持仓>12月 → 强制全面复盘
    },

    # ── 基本面止损比例 ──
    "structural_stop": {
        "indicators_down_1_2": 0.3,     # 领先指标1-2个转down → 减30%
        "breakthrough_negative": 0.5,   # 瓶颈破坏 negative → 减50%
        "full_liquidation": 1.0,        # 指标≥2 down + 瓶颈破坏 → 清仓
    },

    # ── 信号取值映射 ──
    "signal_points": {
        "L1": {
            "rsi_oversold": 1,          # RSI<30
            "rsi_overbought": -1,       # RSI>overheat阈值
            "ma50_repair": 1,           # above_ma50回升至≥30%
            "ma50_break": -1,           # above_ma50降至<30%
            "macd_golden": 1,           # MACD金叉
            "macd_death": -1,           # MACD死叉
            "kdj_oversold": 1,          # KDJ<20
            "kdj_overbought": -1,       # KDJ>80
            "bollinger_lower": 1,       # 触及下轨
            "bollinger_upper": -1,      # 触及上轨
            "volume_up_heavy": 2,       # 放量上涨(>1.5x均量)
            "volume_up_light": -1,      # 缩量上涨(<0.6x均量)
            "volume_down_heavy": 1,     # 放量下跌(恐慌出清)
            "volume_down_light": -2,    # 缩量下跌(阴跌)
        },
        "L2": {
            "leading_up": 2,            # 领先指标 up（加权）
            "leading_down": -3,         # 领先指标 down
            "breakthrough_positive": 3, # 瓶颈突破利好
            "breakthrough_negative": -4,# 瓶颈突破利空
            "cascade_upgrade": 1,       # 联动升级
            "cascade_downgrade": -2,    # 联动降级
        },
        "L3": {
            "early": 2,
            "mid": 1,
            "mid-to-late": -1,
            "late": -2,
        },
        "L4": {
            "beat": 2,                  # 财报超预期
            "inline": 0,                # 符合预期
            "miss": -2,                 # 不及预期
        },
    },
}


# ══════════════════════════════════════════════════════════
# 持仓权重（来自天天基金季报，用于代理加权）
# ══════════════════════════════════════════════════════════

# 板块ID → 真实基金代码（查权重用）
BOARD_FUND_MAP = {
  "CPO": "011370",
  "021528": "021528",
  "015789": "015789",
  "STORAGE": "025209",
  "019633": "019633",
  "020608": "020608",
  "025856": "025856"
}

# 各基金的前十大持仓权重（ticker → 占净值比例%）
HOLDING_WEIGHTS = {
  "011370": {
    "300308.SZ": 7.13,
    "300502.SZ": 6.64,
    "688498.SS": 3.84,
    "688048.SS": 3.35,
    "600105.SS": 3.6
  },
  "015789": {
    "300136.SZ": 6.43,
    "600879.SS": 6.18,
    "688002.SS": 5.54,
    "688375.SS": 5.18,
    "301232.SZ": 5.23
  },
  "021528": {
    "300502.SZ": 9.47,
    "688519.SS": 8.75,
    "688498.SS": 8.63,
    "300408.SZ": 7.93,
    "301511.SZ": 7.92
  },
  "025209": {
    "603986.SS": 7.92,
    "300223.SZ": 7.56,
    "001309.SZ": 7.16,
    "301308.SZ": 7.06,
    "688766.SS": 6.99
  },
  "019633": {
    "002371.SZ": 6.67,
    "688012.SS": 6.05,
    "688072.SS": 2.77,
    "300604.SZ": 2.59
  },
  "020608": {
    "688017.SS": 4.58,
    "601100.SS": 4.93
  },
  "025856": {
    "000400.SZ": 1,
    "600089.SS": 1,
    "600406.SS": 1,
    "601126.SS": 1,
    "601179.SS": 1
  }
}


# ══════════════════════════════════════════════════════════
# 个人数据目录（与代码分离，不进入 git）
# ══════════════════════════════════════════════════════════

# 个人数据（portfolio.json / history / predictions / reviews 等）
# 默认在项目目录，可通过环境变量 PERSONAL_DATA_DIR 指向外部目录。
DATA_DIR = os.environ.get("PERSONAL_DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
