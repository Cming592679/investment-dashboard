"""Investment Dashboard — 全部基金/板块配置"""

from datetime import date

# ══════════════════════════════════════════════════════════
# 基金定义
# ══════════════════════════════════════════════════════════

FUNDS = {
    "019633": {
        "name": "国泰半导体材料设备ETF联接C",
        "short": "半导体设备",
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
}

# ══════════════════════════════════════════════════════════
# 领先指标体系（每板块独立，标 * 为自动抓取，其余手动更新）
# ══════════════════════════════════════════════════════════

LEADING_INDICATORS = {
    "019633": {
        "SEMI 北美设备 Billings": {
            "value": "2026年5月 $2.3B",
            "trend": "up",  # up / flat / down
            "note": "连续6个月环比增长，设备订单仍在扩张",
            "update_cycle": "每月中旬 SEMI 发布后更新",
        },
        "DRAM 合约价 QoQ": {
            "value": "Q2 +64% → Q3 预计 +8~13%",
            "trend": "flat",
            "note": "涨幅大幅收窄！存储器周期可能进入平台期",
            "update_cycle": "季末 TrendForce/DRAMeXchange 发布后更新",
        },
        "台积电月度营收 YoY": {
            "value": "5月 +30% YoY",
            "trend": "up",
            "note": "先进制程满产，CoWoS 产能仍是瓶颈",
            "update_cycle": "每月10日 TSMC 发布后更新",
        },
        "ASML EUV 积压订单": {
            "value": "Q1 新增 €3.6B 订单",
            "trend": "up",
            "note": "EUV 交期 18 月+，2028 年前产能已被锁定",
            "update_cycle": "季末 ASML 财报后更新",
        },
        "四大云厂 CapEx 合计 YoY": {
            "value": "Q1 合计 +44% YoY",
            "trend": "up",
            "note": "⚠ Q2 财报 7/27-8/1 发布，CapEx 指引是最大变量",
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
            "value": "2026年底CoWoS月产能目标50K片（+80% YoY）",
            "trend": "up",
            "note": "【②CoWoS单源】TSMC CoWoS=所有NVDA GPU必经之路。产能扩张速度=GPU出货上限。产能翻倍=供应瓶颈缓解→NVDA营收天花板打开",
            "update_cycle": "TSMC季报/法说会",
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
            "value": "Q1 EUV新增订单€3.6B，积压>€40B",
            "trend": "up",
            "note": "【⑥设备垄断→②的根源】EUV交期18月+→TSMC扩产受限→CoWoS扩产受限→GPU出货受限。ASML订单是AI硬件供应链最上游的6-18月领先指标",
            "update_cycle": "季报后",
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
            "value": "南通三期工厂（20层+）产能利用率>95%",
            "trend": "up",
            "note": "【③产能售罄】高层PCB产能紧张→深南/沪电有定价权。产能利用率>90%持续=扩产信号→设备投资→行业景气确认",
            "update_cycle": "季报后",
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
            "value": "2026年国网计划投资¥6300亿（+8% YoY），南网¥1200亿",
            "trend": "up",
            "note": "【⑧巨头依赖】国网+南网=电网设备行业唯一大客户。年度投资增速>5%=行业景气；<0%=收缩。2026年+8%仍在扩张区间",
            "update_cycle": "年初国网/南网工作会议（1月）",
        },
        "大型变压器交付周期【③产能售罄】": {
            "value": "全球大型变压器交期18-24月（正常12月），供给严重不足",
            "trend": "up",
            "note": "【③产能售罄→⑥设备瓶颈】全球变压器产能不足→交期拉长→涨价+扩产。变压器=电网的CPU，没有变压器新能源发的电送不出去。这是板块最强基本面支撑",
            "update_cycle": "季度（盯ABB/西门子能源/特变电工季报交期数据）",
        },
        "新能源装机增速→电网消纳压力": {
            "value": "2026年1-5月风光新增装机92GW（+28% YoY）",
            "trend": "up",
            "note": "新能源装机>电网消纳能力=弃风弃光=倒逼电网投资。装机增速越快→电网改造越紧迫→设备需求越确定",
            "update_cycle": "月度（国家能源局）",
        },
        "铜/硅钢价格 YoY【成本端】": {
            "value": "铜$9,800(+12%) 硅钢¥8,500/吨(+5%)",
            "trend": "flat",
            "note": "铜+硅钢占变压器/电缆成本50%+。当前温和上涨但未暴涨→成本压力可控。若铜价破$11,000=毛利显著承压→需警惕",
            "update_cycle": "日度（铜HG=F）+月度（硅钢）",
        },
    },
}

# ── 各板块关键事件日期 ─────────────────────

KEY_DATES = {
    "019633": [
        {"date": date(2026, 7, 10), "event": "台积电 6 月营收", "importance": "critical"},
        {"date": date(2026, 7, 17), "event": "ASML Q2 财报",     "importance": "critical"},
        {"date": date(2026, 7, 21), "event": "SEMI 6月 Billings", "importance": "critical"},
        {"date": date(2026, 7, 27), "event": "GOOGL Q2 财报",    "importance": "high"},
        {"date": date(2026, 7, 29), "event": "MSFT Q2 财报",     "importance": "high"},
        {"date": date(2026, 7, 30), "event": "META Q2 财报",     "importance": "high"},
        {"date": date(2026, 8, 1),  "event": "AMZN Q2 财报",     "importance": "high"},
    ],
    "014194": [
        {"date": date(2026, 7, 10),  "event": "台积电 6 月营收",        "importance": "high"},
        {"date": date(2026, 7, 15),  "event": "中国集成电路 6 月产量",    "importance": "high"},
        {"date": date(2026, 7, 20),  "event": "北方华创 H1 业绩预告(预计)", "importance": "critical"},
        {"date": date(2026, 8, 15),  "event": "中芯国际 Q2 财报(预计)",    "importance": "critical"},
        {"date": date(2026, 8, 25),  "event": "北方华创 Q2 财报(预计)",    "importance": "high"},
    ],
    "CPO": [
        {"date": date(2026, 7, 10), "event": "台积电 6 月营收", "importance": "high"},
        {"date": date(2026, 7, 25), "event": "中际旭创 H1 业绩预告(预计)", "importance": "critical"},
        {"date": date(2026, 8, 5),  "event": "Lumentum Q2 财报(光芯片)", "importance": "high"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "中际旭创 Q2 财报(预计)", "importance": "critical"},
    ],
    "024239": [
        {"date": date(2026, 7, 17), "event": "ASML Q2 财报(EUV订单)", "importance": "critical"},
        {"date": date(2026, 7, 25), "event": "SK海力士 Q2 财报(HBM)", "importance": "critical"},
        {"date": date(2026, 7, 27), "event": "GOOGL Q2(CapEx指引)", "importance": "critical"},
        {"date": date(2026, 7, 29), "event": "MSFT Q2(CapEx指引)", "importance": "critical"},
        {"date": date(2026, 7, 30), "event": "META Q2(CapEx指引)", "importance": "high"},
        {"date": date(2026, 8, 1),  "event": "AMZN Q2(CapEx指引)", "importance": "high"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报", "importance": "critical"},
    ],
    "021528": [
        {"date": date(2026, 7, 20), "event": "深南电路 H1 业绩预告(预计)", "importance": "critical"},
        {"date": date(2026, 8, 20), "event": "NVDA Q2 财报(服务器需求)", "importance": "high"},
        {"date": date(2026, 8, 25), "event": "沪电股份 Q2 财报(预计)", "importance": "high"},
    ],
    "015789": [
        {"date": date(2026, 7, 15), "event": "SpaceX H1 发射统计", "importance": "high"},
        {"date": date(2026, 8, 10), "event": "Rocket Lab Q2 财报", "importance": "critical"},
        {"date": date(2026, 10, 1), "event": "中国航天发射计划H2更新", "importance": "high"},
    ],
    "025856": [
        {"date": date(2026, 7, 15), "event": "6月新能源装机数据", "importance": "high"},
        {"date": date(2026, 7, 20), "event": "国网 H1 投资进度公告(预计)", "importance": "critical"},
        {"date": date(2026, 8, 25), "event": "特变电工 Q2 财报(预计)", "importance": "high"},
        {"date": date(2026, 8, 30), "event": "国电南瑞 Q2 财报(预计)", "importance": "critical"},
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
}

# ══════════════════════════════════════════════════════════
# P1-任务6：技术面/基本面背离强制降级阈值
# ══════════════════════════════════════════════════════════

DIVERGENCE_DOWNGRADE_WEEKS = 2  # 持续N周背离 → 自动降级
# 触发条件：技术面评分=0 但 领先指标+周期≥4 → 标记背离
# 持续满足条件超过 DIVERGENCE_DOWNGRADE_WEEKS → 强制降级到🟡
