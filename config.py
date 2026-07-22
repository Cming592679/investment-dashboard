"""Investment Dashboard — 全部基金/板块配置"""

from datetime import date

# ══════════════════════════════════════════════════════════
# 基金定义
# ══════════════════════════════════════════════════════════

FUNDS = {
    "019633": {
        "name": "国泰半导体材料设备ETF联接C",
        "short": "半导体设备",
        "benchmark": "512760.SS",
        "market": "us",
        "stocks": {
            "AMAT":  "应用材料",
            "LRCX":  "泛林研究",
            "ASML":  "阿斯麦",
            "KLAC":  "科磊",
            "TOELY": "东京电子",
        },
        "indices": {
            "SOXX": "iShares半导体ETF",
            "SMH":  "VanEck半导体ETF",
            "^SOX": "费城半导体指数",
        },
        "specials": {
            "MU": {"name": "美光(内存代理)", "note": "存储是半导体领先指标，MU 暴跌预警设备需求放缓"},
        },
        "exit_thresholds": {
            "rsi_overbought": 70, "rsi_oversold": 30,
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
            "300394.SZ": "天孚通信",
            "002281.SZ": "光迅科技",
            "688313.SS": "仕佳光子",
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
        "short": "AI硬件",
        "benchmark": "QQQ",
        "market": "us",
        "stocks": {
            "NVDA": "英伟达",
            "AMD":  "超威",
            "AVGO": "博通",
            "ANET": "Arista",
            "SMCI": "超微电脑",
        },
        "indices": {
            "^NDX": "纳斯达克100",
            "SMH":  "VanEck半导体ETF",
            "QQQ":  "纳指100ETF",
        },
        "specials": {
            "DELL": {"name": "戴尔", "note": "AI服务器出货量风向标"},
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
        "short": "PCB",
        "benchmark": "159997.SZ",
        "market": "a",
        "stocks": {
            "002916.SZ": "深南电路",
            "002384.SZ": "东山精密",
            "002463.SZ": "沪电股份",
            "300476.SZ": "胜宏科技",
            "603228.SS": "景旺电子",
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
        "short": "航天卫星",
        "benchmark": "512660.SS",
        "market": "a",
        "stocks": {
            "600118.SS": "中国卫星",
            "600879.SS": "航天电子",
            "688568.SS": "中科星图",
            "600391.SS": "航发科技",
            "603698.SS": "航天工程",
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
}

# ══════════════════════════════════════════════════════════
# 领先指标体系（每板块独立，标 * 为自动抓取，其余手动更新）
# ══════════════════════════════════════════════════════════

LEADING_INDICATORS = {
    "019633": {
        "SEMI 北美设备 Billings": {
            "value": "6月 B/B值0.98(连续两月<1)，订单$15.1B(-2.6% MoM)，出货$15.4B(+16.2% YoY)",
            "trend": "flat",
            "note": "H1维持正增长但短期订单动能放缓。B/B连续<1是黄灯，但出货仍同比+16%，非收缩信号。关注7-8月是否回升至>1",
            "update_cycle": "每月下旬 SEMI 发布后更新",
            "last_updated": "2026-07-21",
        },
        "DRAM 合约价 QoQ": {
            "value": "Q2 +64% → Q3 预计 +8~13%",
            "trend": "flat",
            "note": "涨幅大幅收窄！存储器周期可能进入平台期。Q2法说会台积电确认HBM需求仍极强→SK海力士Q2(7/25)是关键验证",
            "update_cycle": "季末 TrendForce/DRAMeXchange 发布后更新",
        },
        "台积电月度营收 YoY": {
            "value": "Q2营收1.27兆NTD(+36% YoY)创新高，Q3指引季增11-15%。全年美元营收上修至+40%",
            "trend": "up",
            "note": "Q2法说会(7/16)确认：CoWoS年底14万片/月→2027年17万片。Capex上调至$600-640亿。魏哲家：2030年前产能仍难满足AI需求。先进制程+封装持续供不应求",
            "update_cycle": "每月10日 TSMC 发布后更新 + 季报法说会",
            "last_updated": "2026-07-21",
        },
        "ASML EUV 积压订单": {
            "value": "Q2营收€93.27亿(+21% YoY)，全年指引上修至€430-450亿。2027年EUV产能+30%至~85台",
            "trend": "up",
            "note": "EUV交期18月+，2027年产能已被锁定。High-NA EUV已用于Intel 18A量产(酷睿Ultra 3)。2028年评估再扩30%至~110台",
            "update_cycle": "季末 ASML 财报后更新",
            "last_updated": "2026-07-21",
        },
        "四大云厂 CapEx 合计 YoY": {
            "value": "Q1合计$730亿(+44% YoY)，Q2财报7/27-8/1密集发布",
            "trend": "up",
            "note": "⚠ Q2 CapEx指引是当前最大变量。台积电Q2 Capex上修至$600-640亿→正向先行信号。若云厂CapEx>+30%=继续扩张；<+20%=警惕",
            "update_cycle": "季末 Hyperscaler 财报后更新",
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

    # ═══ AI硬件 · 美股（Bottleneck：GPU/CoWoS/HBM三重瓶颈） ═══
    # 5层链：AI应用→NVDA GPU→TSMC CoWoS→ASML EUV→HBM
    # 瓶颈原型：②NVDA单源 ②CoWoS单源 ②HBM三寡头 ⑥EUV设备垄断
    "024239": {
        "NVDA 数据中心营收 QoQ【②单源卡脖子】": {
            "value": "Q1 数据中心 $42B（+18% QoQ），Q2指引$48B",
            "trend": "up",
            "note": "【②NVDA垄断】数据中心营收增速=AI算力需求温度计。增速>15%QoQ=需求仍在加速；<10%=增速放缓→警惕",
            "update_cycle": "季报后（8月底Q2）",
        },
        "TSMC CoWoS 产能扩张【②先进封装瓶颈】": {
            "value": "Q2法说会确认：2026年底CoWoS月产能14万片，2027年底目标17万片",
            "trend": "up",
            "note": "【②CoWoS单源】TSMC CoWoS=所有NVDA GPU必经之路。产能仍在快速扩张但需求增长更快→2030年前仍难满足AI需求。魏哲家：乐见更多先进封装方案协助解决瓶颈",
            "update_cycle": "TSMC季报/法说会",
            "last_updated": "2026-07-21",
        },
        "HBM3e 供应紧张度【②存储瓶颈】": {
            "value": "SK海力士HBM3e 2026产能全部售罄，2027已预订>60%",
            "trend": "up",
            "note": "【②HBM三寡头】每颗GPU必须配HBM。SK海力士(53%)+三星(35%)+美光(12%)垄断。HBM售罄=GPU出货被存储卡住=AI硬件瓶颈短期无解",
            "update_cycle": "季度（盯SK海力士/三星/MU季报）",
        },
        "Hyperscaler CapEx 指引 QoQ": {
            "value": "Q1合计$730亿（+44% YoY），Q2指引7月底见分晓",
            "trend": "up",
            "note": "⚠ 四大云厂Q2财报(7/27-8/1)是当前最大变量。CapEx指引增速>30%=继续扩张；<20%=AI投资节奏放缓→AI硬件板块承压",
            "update_cycle": "季报后（7月底/1月底/4月底/10月底）",
        },
        "ASML EUV 订单→GPU产能前置【⑥设备垄断】": {
            "value": "Q2营收€93.27亿超预期。全年指引上修至€430-450亿。2027年EUV产能+30%至~85台",
            "trend": "up",
            "note": "【⑥设备垄断→②的根源】EUV交期18月+→TSMC扩产受限→CoWoS扩产受限→GPU出货受限。ASML Q2指引上修=AI硬件2-3年扩张周期确认。High-NA EUV已量产(Intel 18A)",
            "update_cycle": "季报后",
            "last_updated": "2026-07-21",
        },
    },

    # ═══ PCB · 服务器PCB（Evolution+Bottleneck：高层数产能） ═══
    # 5层链：AI服务器→ODM→高层PCB→CCL覆铜板→铜箔/玻纤
    # 瓶颈原型：③高层数产能售罄 ④BOM普适 ⑧巨头供应链
    "021528": {
        "AI服务器PCB层数升级【④BOM普适+⑧供应链】": {
            "value": "传统服务器8-12层→AI服务器20-30层，单价3-5x",
            "trend": "up",
            "note": "【④BOM普适+⑧巨头依赖】NVDA DGX/华为昇腾服务器必须用高层PCB。层数↑=单价↑=进入壁垒↑。深南/沪电已进NVDA/华为供应链",
            "update_cycle": "季度（盯服务器ODM出货数据）",
        },
        "深南电路高层PCB产能利用率【③产能售罄】": {
            "value": "H1归母净利21-23亿(+54-69% YoY)，无锡AI算力PCB项目(投资45亿)预计2027H1量产",
            "trend": "up",
            "note": "【③产能售罄→扩产验证】H1业绩超预期，AI服务器+存储双驱动。南通三期满产+泰国/南通四期爬坡。无锡新项目专注AI服务器高层PCB(20-30层)，2027年投产=长期增长确认",
            "update_cycle": "季报后",
            "last_updated": "2026-07-21",
        },
        "铜价 YoY【成本压力】": {
            "value": "LME铜 $9,800/吨（+12% YoY），Q2小幅回落",
            "trend": "flat",
            "note": "铜占PCB原材料成本30%+。铜价↑=毛利承压；铜价↓=毛利释放。当前高位震荡但未加速上涨→成本端压力可控",
            "update_cycle": "日度自动（yfinance: HG=F）",
        },
        "CCL覆铜板价格【上游传导】": {
            "value": "生益科技Q2 CCL报价环比持平，涨价预期减弱",
            "trend": "flat",
            "note": "CCL是PCB直接上游。CCL涨价=PCB成本压力；CCL降价=毛利扩张。当前走平=PCB毛利稳定",
            "update_cycle": "月度/季报",
        },
    },

    # ═══ 航天卫星 · 商业航天（Bottleneck：发射产能） ═══
    # 5层链：卫星互联网→卫星制造→发射服务→火箭发动机→特种材料
    # 瓶颈原型：②发射产能单源 ⑨政府预算二阶 ①特种材料
    "015789": {
        "SpaceX 发射频次【②发射产能单源】": {
            "value": "2026 H1已完成89次发射（年化178次），全球占比>60%",
            "trend": "up",
            "note": "【②单源垄断】全球发射产能被SpaceX垄断→其他发射商（中国航天/Rocket Lab）产能不足→卫星排队等发射=星座部署延迟。SpaceX频次↑=行业加速",
            "update_cycle": "月度（SpaceX官网+spaceflightnow）",
        },
        "中国星网卫星发射进度【⑨政策驱动】": {
            "value": "星网首批试验星已发12颗，2026年目标108颗",
            "trend": "up",
            "note": "【⑨政府CapEx】星网=中国版Starlink，计划发射1.3万颗卫星。发射进度=产业链订单释放节奏。108颗只是开始，加速期在2027-28",
            "update_cycle": "季度（盯航天科技集团公告）",
        },
        "全球航天经济总量增速": {
            "value": "2025年$570B→2030年预计$1T+（CAGR 12%）",
            "trend": "up",
            "note": "SpaceX+星网+Kuiper三巨头驱动，航天从政府市场变成商业市场。增速>10%=赛道确定性强",
            "update_cycle": "年度（Space Foundation报告）",
        },
        "Rocket Lab 发射+订单【商业航天风向标】": {
            "value": "Neutron火箭2026H2首飞，积压订单$1.2B",
            "trend": "up",
            "note": "Rocket Lab是全球唯二有规模发射能力的商业公司。Neutron首飞成功→打破SpaceX垄断→利好整个商业航天板块",
            "update_cycle": "季度（盯RKLB季报+首飞日期）",
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
            "value": "在手订单排至2027年底，产能利用率>90%，全球份额~25%。6月工业机器人产量+28.1% YoY→下游需求旺盛",
            "trend": "up",
            "note": "【②单源卡脖子】日本HD占全球>60%，绿的谐波是国内唯一量产厂商。三次谐波新技术传动精度<10弧秒、刚性3x，已独家供货特斯拉墨西哥工厂。产能从50万→100万台/年扩产中。Tesla Q2财报(7/22)是近期最大催化剂",
            "update_cycle": "季报后（4/8/10月底）+ 特斯拉季报",
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
        {"date": date(2026, 7, 25), "event": "SK海力士 Q2 财报(HBM)", "importance": "critical"},
        {"date": date(2026, 7, 27), "event": "GOOGL Q2 财报",    "importance": "high"},
        {"date": date(2026, 7, 29), "event": "MSFT Q2 财报",     "importance": "high"},
        {"date": date(2026, 7, 30), "event": "META Q2 财报",     "importance": "high"},
        {"date": date(2026, 8, 1),  "event": "AMZN Q2 财报",     "importance": "high"},
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
         "result": "H1正式预告尚未发布。Q1合同负债42.03亿(环比-2.05%)，研发投入+37%。关注H1订单质量和存货周转"},
        {"date": date(2026, 8, 15),  "event": "中芯国际 Q2 财报(预计)",    "importance": "critical"},
        {"date": date(2026, 8, 25),  "event": "北方华创 Q2 财报(预计)",    "importance": "high"},
    ],
    "CPO": [
        {"date": date(2026, 7, 16), "event": "台积电 Q2 法说会 ⚠", "importance": "critical",
         "result": "Q2营收+36% YoY创新高，CoWoS年底14万片/月。AI算力需求持续爆炸→800G/1.6T光模块需求确定性极强"},
        {"date": date(2026, 7, 25), "event": "中际旭创 H1 业绩预告(预计)", "importance": "critical"},
        {"date": date(2026, 8, 5),  "event": "Lumentum Q2 财报(光芯片)", "importance": "high"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "中际旭创 Q2 财报(预计)", "importance": "critical"},
    ],
    "024239": [
        {"date": date(2026, 7, 16), "event": "台积电 Q2 法说会 ⚠", "importance": "critical",
         "result": "CoWoS年底14万片/月(2027→17万)。Capex上调至$600-640亿。2030年前产能仍难满足AI需求→GPU出货瓶颈短期无解"},
        {"date": date(2026, 7, 17), "event": "ASML Q2 财报(EUV订单)", "importance": "critical",
         "result": "全年指引上修至€430-450亿。2027 EUV产能+30%。EUV交期18月+=GPU产能扩张的最上游硬约束"},
        {"date": date(2026, 7, 25), "event": "SK海力士 Q2 财报(HBM)", "importance": "critical"},
        {"date": date(2026, 7, 27), "event": "GOOGL Q2(CapEx指引)", "importance": "critical"},
        {"date": date(2026, 7, 29), "event": "MSFT Q2(CapEx指引)", "importance": "critical"},
        {"date": date(2026, 7, 30), "event": "META Q2(CapEx指引)+三星Q2", "importance": "high"},
        {"date": date(2026, 8, 1),  "event": "AMZN Q2(CapEx指引)", "importance": "high"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报", "importance": "critical"},
    ],
    "021528": [
        {"date": date(2026, 7, 20), "event": "深南电路 H1 业绩预告(预计)", "importance": "critical",
         "result": "归母净利21-23亿(+54-69% YoY)，扣非+64-80%。AI算力+存储双驱动。无锡AI算力PCB项目(投资45亿)预计2027H1量产"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报(服务器需求)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "沪电股份 Q2 财报(预计)", "importance": "high"},
    ],
    "015789": [
        {"date": date(2026, 7, 15), "event": "SpaceX H1 发射统计", "importance": "high",
         "result": "H1完成75次发射(59次Starlink)，部署1589颗卫星。年化150次+。全球发射占比>60%，垄断地位稳固"},
        {"date": date(2026, 8, 10), "event": "Rocket Lab Q2 财报", "importance": "critical"},
        {"date": date(2026, 10, 1), "event": "中国航天发射计划H2更新", "importance": "high"},
    ],
    "025856": [
        {"date": date(2026, 7, 15), "event": "6月新能源装机数据", "importance": "high",
         "result": "6月新增3825个项目(风电32+光伏3787)。截至5月底全国装机突破40.1亿kW，非化石能源占62%"},
        {"date": date(2026, 7, 20), "event": "国网 H1 投资进度公告(预计)", "importance": "critical",
         "result": "Q1固投1290亿(+37% YoY)。H1物资招标>2500亿(+17%)。110kV+工程投产完成年度53%。7月特高压第三批招标108.7亿"},
        {"date": date(2026, 8, 25), "event": "特变电工 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 30), "event": "国电南瑞 Q2 财报(预计)", "importance": "critical"},
    ],
    "020608": [
        {"date": date(2026, 7, 15), "event": "6月工业机器人产量", "importance": "high",
         "result": "6月11.07万套(+28.1% YoY)，H1累计+28.0%。连续多月>25%高增，制造业自动化加速"},
        {"date": date(2026, 7, 22), "event": "Tesla Q2 财报(Optimus进度) ⚠", "importance": "critical"},
        {"date": date(2026, 7, 25), "event": "绿的谐波 H1 业绩预告(预计)", "importance": "critical"},
        {"date": date(2026, 8, 5),  "event": "柯力传感 Q2 财报(六维力出货)", "importance": "critical"},
        {"date": date(2026, 8, 15), "event": "世界机器人大会(北京)", "importance": "critical"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报(机器人平台)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "恒立液压 Q2 财报(丝杠进度)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "绿的谐波 Q2 财报", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "金力永磁 Q2 财报(磁材出货)", "importance": "high"},
        {"date": date(2026, 9, 1),  "event": "日发精机 丝杠装配线交付节点", "importance": "high"},
        {"date": date(2026, 9, 15), "event": "Tesla AI Day 2026(预计) ⚠", "importance": "critical"},
    ],
}

# ── 各板块周期位置判断（手动评估）───────────

CYCLE_ASSESSMENTS = {
    "019633": {
        "stage": "mid-to-late",
        "label": "增速峰值区",
        "note": "AI CapEx 仍在增长但增速可能见顶。Q2 云厂财报的 CapEx 指引决定下半年方向。DRAM 涨幅收窄是黄灯。",
        "risk": "yellow",  # green / yellow / red
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
        "label": "AI算力扩张中后期（Bottleneck主题）",
        "note": "【Bottleneck三重卡点】②NVDA GPU单源+②TSMC CoWoS单源+②HBM三寡头。三重瓶颈叠加=供给严重落后于需求=AI硬件公司利润丰厚但增速见顶风险在积累。H2关键变量：①Hyperscaler Q2 CapEx指引(7月底) ②NVDA Blackwell ramp进度 ③TSMC CoWoS扩产是否如期。若CapEx指引<+20%→警惕周期见顶。",
        "risk": "yellow",
    },
    "021528": {
        "stage": "mid",
        "label": "AI服务器PCB升级期（Evolution+Bottleneck）",
        "note": "【Evolution+Bottleneck】AI服务器PCB从传统8-12层升级到20-30层→单价3-5x→龙头深度受益。核心瓶颈在③高层PCB产能（深南/沪电>95%利用率）。不同于半导体设备的强周期，PCB是BOM普适器件（④），需求更分散更稳定。关注：深南H1业绩、铜价趋势、AI服务器出货量。",
        "risk": "green",
    },
    "015789": {
        "stage": "early",
        "label": "商业航天萌芽期（Bottleneck主题）",
        "note": "【Bottleneck】全球发射产能被SpaceX垄断（②单源），中国星网+Starlink+Kuiper三巨头驱动卫星互联网。当前处于早期基建阶段——卫星还没发完，应用还没落地。核心变量：①SpaceX发射频次是否持续攀升 ②星网2026年108颗目标完成度 ③Rocket Lab Neutron首飞(2026H2)能否打破垄断。政府/国防CapEx驱动，节奏慢但确定性强。",
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
        "note": "【Bottleneck密集区】人形机器人是当前瓶颈密度最高的赛道之一：①钕铁硼磁材中国垄断+出口管制→结构重构 ②HD谐波减速器→绿的谐波突破 ②行星滚柱丝杠进口垄断→恒立液压/五洲新春追赶 ②六维力传感器<30%国产化 ⑥精密螺纹磨床被忽视的卖铲人。当前Optimus V3定型在即、特斯拉年底目标稳定2000-2500台/周，产业链各层级的瓶颈紧张度将逐层暴露。最适合埋伏的是【⑥⑦设备层(日发精机)+①材料层(金力永磁)】——机构覆盖少、但产能扩张绕不开。关键变量：①7/20 Tesla Q2→Optimus量产时间表 ②绿的谐波/恒立液压H1业绩→验证订单放量 ③行星滚柱丝杠良率突破60%→80%是关键阈值。",
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
        "funds": ["019633", "014194", "024239"],  # 半导体设备 / 芯片指数 / AI硬件
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
        "affected_funds": ["019633", "014194", "024239"],
    },
    "cowos": {
        "label": "TSMC CoWoS 垄断",
        "conditions": [
            {"desc": "三星/Intel 先进封装达到同等良率", "status": "watching", "note": "三星 I-Cube 在验证中，但良率落后 TSMC"},
            {"desc": "NVDA 自研封装方案绕过 CoWoS", "status": "none", "note": "暂无公开信息"},
        ],
        "affected_funds": ["019633", "024239"],
    },
    "hbm": {
        "label": "HBM 三寡头垄断",
        "conditions": [
            {"desc": "中国 CXMT 量产 HBM2e 及以上", "status": "watching", "note": "CXMT 在研发 HBM2，距量产尚远"},
            {"desc": "新型存储 (CXL/存算一体) 替代 HBM", "status": "none", "note": "学术阶段，无商用时间表"},
        ],
        "affected_funds": ["019633", "024239"],
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
            {"desc": "Optimus 宣布对外销售时间表", "status": "watching", "note": "2027年目标对外销售，7/20 Q2财报是近期关键节点"},
            {"desc": "特斯拉周产稳定>2000台", "status": "watching", "note": "马斯克红线：2026年底稳定2000-2500台/周"},
            {"desc": "Optimus 获得外部客户订单", "status": "none", "note": "目前仅有特斯拉内部使用计划"},
        ],
        "affected_funds": ["020608"],
    },
}

# ══════════════════════════════════════════════════════════
# P1-任务5：周期判断反方假设
# ══════════════════════════════════════════════════════════

# 每个板块的周期判断补充"如果我错了"字段
# 从 CYCLE_ASSESSMENTS 中提取，作为补充字段
CYCLE_COUNTER_HYPOTHESIS = {
    "019633": "如果 Q2 云厂 CapEx 指引 >+40% YoY → 周期可能还在中期而非中后期，当前判断偏悲观",
    "014194": "如果光刻胶国产化突然加速(进口占比跌破60%) → 周期可能已入中期而非早期，当前判断偏保守",
    "CPO": "如果 NVDA Rubin 延迟到 2028 → 1.6T/CPO 大规模部署后移，当前\"早期\"判断可能需要等更久兑现",
    "024239": "如果 Q2 CapEx >+35% YoY → 三重瓶颈利润故事延续，中后期判断可能偏早",
    "021528": "如果铜价暴涨至 $12,000 → 成本端严重恶化，当前 mid 判断需要重新评估",
    "015789": "如果 Neutron 首飞失败 → 发射垄断短期内无解，早期阶段可能持续更久（利空商业航天板块）",
    "025856": "如果国网投资增速降至 <3% → 需求端逻辑弱化，当前 mid 判断偏高",
    "020608": "如果 Tesla Optimus 对外销售推迟到 2028+ 或量产良率持续<50% → 整条供应链的量产故事短期无法兑现，核心零部件厂商的机器人业务收入占比可能停滞在<10%，板块可能回调 30-50%",
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
    "019633": "SOXX",      # 半导体设备 → SOXX
    "014194": "000688.SS", # 芯片指数 → 科创50
    "CPO":     "159997.SZ", # CPO → 电子ETF
    "024239":  "^NDX",     # AI硬件 → 纳斯达克100
    "021528":  "159997.SZ", # PCB → 电子ETF
    "015789":  "512660.SS", # 航天卫星 → 军工ETF
    "025856":  "159611.SZ", # 电网设备 → 电力ETF
    "020608":  "000688.SS", # 机器人 → 科创50
}
