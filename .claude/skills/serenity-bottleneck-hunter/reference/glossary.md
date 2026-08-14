# Glossary — Serenity Bottleneck Hunter 术语库

> **维护策略**:**预填 + LLM 自动 enrich**(用户决策:宁滥勿缺,允许膨胀)
>
> 每次跑新主题时,LLM 在报告里第一次使用专业缩写/术语必须:
> 1. 检查本文件 — 若已有,直接用 `<abbr title="{中文解释}">{术语}</abbr>` 包裹
> 2. 若没有 — **必须立即追加到本文件对应分类**,然后再回到报告使用
>
> **写作风格**:每条 20-50 字,**人话**(避免循环定义,不堆缩写),含来源/上下文。

---

## 业务 / 技术(半导体 + 电源 + 显示 + 散热)

### 半导体材料 / 工艺

- **SiC** = 碳化硅(Silicon Carbide),新一代功率半导体材料;开关频率 / 耐压 / 效率比传统硅 IGBT 高 5-10 倍,**800V 数据中心电源 / EV 车规** 关键。
- **GaN** = 氮化镓(Gallium Nitride),功率半导体材料,适合高频快充与 800V 中等功率,与 SiC 竞争互补。
- **IGBT** = 绝缘栅双极晶体管,传统硅基功率器件,被 SiC 替代中。
- **InP** = 磷化铟,光通信 / 激光雷达衬底材料,AXTI 占全球 ~40% 供应。
- **SOI** = Silicon On Insulator,绝缘体上硅衬底,光子学 / RF / CPO 用,SOITEC 寡头。
- **SiPh** = Silicon Photonics 硅光子学,把光器件做在硅基上,降本提速,2026 AI 数据中心主线之一。
- **CPO** = Co-Packaged Optics,光器件与 ASIC 共封装,取代可拔插光模块,带宽密度暴涨。
- **III-V** = 第三类与第五类元素化合物半导体(如 GaAs / InP / GaN),非硅基。
- **MEMS** = 微机电系统,把机械 + 电子集成到芯片上(惯性传感 / 加速度 / 麦克风等)。
- **GOES** = Grain-Oriented Electrical Steel 取向硅钢,高效变压器铁芯材料,$CLF 等供应。

### 内存 / 存储

- **HBM** = 高带宽内存(High Bandwidth Memory),3D 堆叠 DRAM,AI GPU 必备;SK Hynix / Samsung / Micron 三家。
- **LPDDR5X** = 低功耗 DDR 第 5 代 X,AI PC / 移动设备主流内存,三星 / SK 海力士 / 美光供应。
- **DDR5** = Double Data Rate 5,主流台式机 / 服务器 DRAM。
- **NAND** = 闪存存储颗粒,SSD 的核心。
- **SSD** = 固态硬盘。
- **SSD 主控** = SSD 内部的控制器芯片,管理读写擦除,Silicon Motion / Phison 等小盘卖铲子。

### 先进封装 / 代工

- **CoWoS** = Chip-on-Wafer-on-Substrate,TSMC 主导的 2.5D 先进封装,AI GPU(NVDA H100/Blackwell)必用。
- **SoIC** = System on Integrated Chips,TSMC 的 3D 先进封装(芯片堆叠)。
- **InFO** = Integrated Fan-Out,TSMC 中端先进封装(Apple A 系列用)。
- **TCB** = Thermal Compression Bonding 热压键合,高端封装设备,ASMPT 寡头。
- **混合键合** = Hybrid Bonding,DRAM 3D 堆叠工艺,拓荆等设备厂参与。
- **fab** = 晶圆制造厂(fabrication plant),如台积电、Intel Fab、SMIC。
- **foundry** = 代工厂(替别人造芯片),TSMC / Samsung / Global Foundries / SMIC。
- **wafer** = 晶圆,半导体基板,直径常见 200mm / 300mm。
- **EUV** = 极紫外光刻,7nm 以下制程必需,ASML 独家。

### 芯片设计 / 计算

- **NPU** = 神经处理器(Neural Processing Unit),AI 推理专用单元;微软 Copilot+ 要求 ≥40 TOPS。
- **GPU** = 图形处理器(Graphics Processing Unit),AI 训练 / 推理通用算力。
- **ASIC** = 定制专用集成电路(Application-Specific IC),如 AVGO 给 Google 做的 TPU。
- **SoC** = System on Chip 系统级芯片,CPU+GPU+NPU+ 等集成。
- **TOPS** = 每秒万亿次运算(Tera Operations Per Second),NPU 算力单位。
- **EDA** = 电子设计自动化(Electronic Design Automation),芯片设计软件;CDNS / SNPS / Siemens 三家,双寡头垄断。
- **IP**(芯片业)= Intellectual Property 知识产权;指 CPU / GPU / NPU 等架构授权(ARM / RISC-V / Imagination)。
- **ARM** = ARM Holdings 英国 IP 公司,每片 ARM 架构 SoC 必交版税 + 授权费;跨 AI PC / 数据中心 / 手机 / 汽车 / IoT 多个 capex cycle。
- **RISC-V** = 开源指令集架构,ARM 的潜在替代,目前在高性能 PC 远未成熟。
- **x86** = Intel / AMD 主导的 PC 指令集架构,与 ARM 竞争。
- **B-TRAN** = Bi-directional TRIAC,Ideal Power 专利的双向晶体管技术。

### AI PC 专有

- **Copilot+ PC** = 微软 AI PC 认证标准(2024 发布),要求 ≥40 TOPS NPU 才能跑 Recall / Live Captions 等本地 AI 功能。
- **Lunar Lake** = Intel 第二代 Core Ultra,2024 末发布,NPU 48 TOPS。
- **Panther Lake** = Intel 下一代 AI PC SoC(2025 末)。
- **Strix Halo** = AMD 高端 AI PC SoC,集成大 NPU + 强 GPU。
- **Ryzen AI 300** = AMD 主流 AI PC SoC 系列,XDNA 2 NPU。
- **Snapdragon X Elite/Plus** = Qualcomm AI PC SoC,Oryon CPU(ARM)+ Hexagon NPU 45 TOPS。
- **M 系列** = Apple 自研芯片(M1/M2/M3/M4),原生 ARM。
- **Apple Neural Engine** = Apple SoC 内的 NPU 单元。

### 数据中心 / AI 算力

- **Grace** = NVIDIA 数据中心 ARM CPU(NVL72 等服务器用)。
- **Graviton** = AWS 自研数据中心 ARM CPU。
- **Ampere Computing** = 第三方数据中心 ARM CPU 厂(被 SoftBank 并购)。
- **Rubin Ultra** = NVIDIA 下一代 AI GPU 平台(2027 量产),目标 1 MW per rack,需 800V HVDC。
- **Kyber** = NVIDIA rack-scale 整机柜方案。
- **OAM** = Open Accelerator Module,加速卡标准。
- **Hyperscaler** = 超大规模数据中心运营商(MSFT/META/GOOGL/AMZN/AAPL/ORCL)。
- **Neocloud** = 新云算力公司(NBIS/CIFR/WULF/CRWV/IREN 等)。

### 800V / 电源 / 散热

- **800V HVDC** = 800 伏高压直流配电,AI 服务器机柜从 48V 升级,降低铜缆截面。
- **48V** = 旧一代数据中心 DC 配电电压。
- **PMIC** = Power Management IC 电源管理芯片(MPWR/QRVO/SWKS 等)。
- **PDU** = Power Distribution Unit 配电单元(VRT/ETN 中游系统)。
- **UPS** = 不间断电源。
- **DC-DC** = 直流-直流转换器(Vicor 龙头)。
- **AC-DC** = 交流-直流转换(Power Integrations 强项)。
- **Vapor Chamber** = 蒸汽腔 / 均温板,高端笔电 + AI 服务器散热模组,Auras / 双鸿 / 力致台股玩家。
- **CDU** = Cooling Distribution Unit 冷却液分配单元。
- **DLC** = Direct Liquid Cooling 直接液冷。

### 显示 / 触控

- **OLED** = 有机发光二极管显示屏。
- **MiniLED** = 微米级 LED 背光显示。
- **AMOLED** = 主动矩阵 OLED。
- **Touch IC** = 触控芯片(Synaptics 等)。

### 测试 / 量测

- **burn-in** = 老化测试,在高温/高压下连续运行筛掉早期失效器件;AEHR 在 SiC 功率器件领域寡头。
- **wafer probe** = 晶圆探针测试。
- **AOI** = Automated Optical Inspection 光学自动检测。

### MLCC 专有

- **MLCC** = Multi-Layer Ceramic Capacitor 多层陶瓷电容,AI 服务器板/手机/车规普适,村田 / 三星 / TDK / Murata 龙头。
- **钛酸钡** = BaTiO₃,MLCC 介质粉核心,Sakai Chemical 全球 #1,国瓷材料 #2。
- **纳米镍粉** = MLCC 内电极材料,博迁新材专长。
- **离型膜** = MLCC 制造流程中的关键耗材,洁美 / 斯迪克 / Lintec 等。
- **ESL** = Effective Series Inductance 等效串联电感,影响 AI GPU 板 MLCC 选型,京瓷 AVX 扩产一倍。

### 商业航天 / 防务

- **rad-hard** = Radiation-Hardened 抗辐照,空间 / 军用必需;VORAGO 等私有公司。
- **ROSA** = Roll-Out Solar Array 卷出式柔性太阳能阵,Redwire 主力产品。
- **III-V 空间太阳能电池** = AZUR / SolAero / Spectrolab 三家垄断。
- **SDA** = Space Development Agency 美军空间发展局。
- **NRO** = National Reconnaissance Office 美军侦察办公室。

### A 股半导体 / 韬定律

- **3D NAND** = 三维堆叠闪存,层数越多需求"韬定律"扩散到上游。
- **韬定律** = 黄仁韬(NVDA CEO)提出的"NAND 层数每提一倍,设备需求非线性"。
- **CMP** = Chemical Mechanical Polishing 化学机械抛光,华海清科国产领先。
- **PECVD** = Plasma-Enhanced Chemical Vapor Deposition 等离子化学气相沉积,拓荆设备方向。

---

## 金融 / 估值术语

- **P/E** = 市盈率(Price-to-Earnings),股价 / 每股收益。
- **P/B** = 市净率(Price-to-Book),股价 / 每股净资产。
- **P/S** = 市销率(Price-to-Sales),股价 / 每股营收。
- **MC** = Market Cap 市值。
- **EV** = Enterprise Value 企业价值(市值 + 净债务)。
- **EBITDA** = 息税折旧摊销前利润。
- **FCF** = Free Cash Flow 自由现金流。
- **DCF** = Discounted Cash Flow 现金流折现估值法。
- **EPS** = Earnings Per Share 每股收益。
- **远期 PE** = Forward P/E,基于未来 12 月预期 EPS 的市盈率。
- **GF** = GuruFocus.com 估值评分(我们偶尔用作参考)。
- **ATH** = All-Time High 历史最高价。
- **ATL** = All-Time Low 历史最低价。
- **YTD** = Year-to-Date 年初至今。
- **MoM / QoQ / YoY** = 月度 / 季度 / 年度对比。
- **NTM** = Next Twelve Months 未来 12 月。
- **TTM** = Trailing Twelve Months 过去 12 月。
- **DD** = Due Diligence 尽职调查。
- **DD&A** = Depreciation, Depletion & Amortization 折旧+耗损+摊销。

### 稀释 / 增发

- **ATM**(发行)= At-the-Market 增发,公司在二级市场连续小额发新股,**Serenity 重要红旗**(BKKT 反复以 70% 折价 ATM 是典型)。
- **PIPE** = Private Investment in Public Equity 上市公司定向增发。
- **EPFA** = Equity Purchase Facility Agreement 股权购买便利协议(类 ATM 的变种)。
- **shelf** = Shelf Registration 上架增发(SEC 424B5),允许公司未来 N 天内随时发新股。
- **lockup** = 解禁期,IPO 后内部人/早期投资人锁定期(常见 90 / 180 / 365 天)。
- **dilution** = 稀释。

### 期权 / 仓位

- **LEAPS** = Long-term Equity AnticiPation Securities,长期看涨期权(2 年+)。
- **CC** = Covered Call 备兑看涨。
- **CSP** = Cash-Secured Put 现金担保看跌。
- **put / call** = 看跌 / 看涨期权。
- **OTM / ITM / ATM**(期权)= Out-/In-/At-The-Money 虚值/实值/平值。
- **IV** = Implied Volatility 隐含波动率。

### SEC 文件

- **8-K** = 重大事项即时披露(增发 / 高管变动 / 合同等)。
- **10-K** = 美股年报。
- **10-Q** = 美股季报。
- **13F** = 季度持仓申报(>$100M AUM 机构必报,显示前机构持仓)。
- **424B5** = 增发说明书(常意味着新股稀释)。
- **Form 4** = 内部人交易申报(高管买卖)。

---

## Serenity 框架核心术语

### 9 大瓶颈原型(本框架核心)

- **① 上游材料/衬底垄断** — 某材料/代工节点被 1-2 家西方公司垄断(如 5N+ 锗镓铟)。
- **② 单一来源卡脖子** — 某关键芯片/器件就一家能供,合规壁垒高(如 XFAB 美国唯一高产能 SiC 代工)。
- **③ 产能售罄/已锁定** — 未来产能已被超大单锁完,等于"远期现金流去风险"(如 TSEM 70% 产能锁到 2028)。
- **④ 进每个设计的 BOM / 普适卖铲子** — 不是单一客户的供应商,是"每个客户都得用"(如 LITE 几乎进每个超大规模厂商 ASIC)。
- **⑤ 估值对标套利 / 跨主题复用** — 对标公司有可比指标 mispriced;或同一标的同时服务多个 capex cycle(跨主题 ⭐ 节点)。
- **⑥ 测试/设备瓶颈** — 测试/量产环节就 1-2 家能做,认证 18 个月+(如 AEHR SiC burn-in)。
- **⑦ 冷门/前机构** — 卖方未覆盖 / 机构持股 <30% / 媒体骂"meme"(反向信号)。
- **⑧ 巨头依赖护城河** — Mag7 不得不用它,且短期内绕不过(如 ALAB Astera Labs 被 AWS 锁定)。
- **⑨ 宏观二阶/地缘错杀** — 不买大路货,顺着供应链找被错杀的二阶受益者(如委内瑞拉链条 → CF 化肥)。

### 三道闸门

- **🔒 真瓶颈** — 产能受限/有定价权/短期无法绕过("别人能 1-2 年内绕过吗?")。
- **👁️ 前机构** — 卖方研报少、机构持仓低、市值小。
- **💰 便宜+已去风险** — 估值压抑 + 产能/订单锁定或现金充足。

### 三档分级

- **🟢 候选** — 过三道闸门 + 当前 stage 合理(模式 A 早期上行)。
- **🟡 暂时观望(条件性)** — 业务/瓶颈逻辑成立但现价过热或有红旗,**必填重估触发条件**。
- **🔴 永久排除** — 商业模式作假/欺诈/业务死亡/个人原则;**严禁历史事件式硬排除**。
- **⭐ 跨主题节点** — 同一只标的同时出现在 ≥2 个主题(see ⑤跨 capex cycle)。⭐⭐ = ≥3 主题。

### 两套择时模式

- **模式 A(主题瓶颈早期动量)** — 主题刚点燃 + 早期上行/突破 + 仍前机构就进,**主动放弃抄底**;本 skill 默认。
- **模式 B(成熟大票超跌反弹)** — 买恐慌性非实质性回调(增发/稀释类回避)。

### Stage 启发式标签(由 `scripts/price.py` 输出)

- **early-uptrend** = 早期上行,可入场(模式 A 的合理 setup)。
- **extended / parabolic** = 已抛物线,**别追**(1m > 40% 或 3m > 120% 或 区间位 ≥95% + 3m > 30%)。
- **range / basing** = 横盘/筑底,等突破。
- **downtrend** = 下跌中(区间位 < 30%)。

### 价格 / 动量字段(price.py 输出)

- **1m / 3m / 6m** = 过去 1 / 3 / 6 个月的总回报率。
- **rng_pos**(range_pos_6mo_pct)= 当前价在过去 6 月最高-最低区间的位置(0 = 最低,100 = 最高)。
- **off_high**(pct_off_6mo_high)= 距过去 6 月最高点的距离(负值 = 已回调)。
- **SMA50 / SMA200** = 50 / 200 日简单移动平均线。

### 框架专有

- **bottleneck / chokepoint** = 瓶颈 / 卡脖子点,本框架核心猎物类型。
- **capex cycle** = 资本开支周期(主题的"花钱必然性")。
- **dogfood** = "吃自己的狗粮" — 工具开发者自己用工具,用实战暴露盲点。
- **forward_picks** = 向前承诺记录;每条标的写入时间戳 + 入场价,几月后 score_tracker 自动打分,**亏的不删**(向前/样本外验证唯一可信形式)。
- **score_tracker** = 跑分脚本,重拉价格,算入场以来涨跌,验证"别追"纪律。
- **cross_theme_scan** = 跨主题节点扫描,自动统计同一只标的跨多少个主题。

---

## 政策 / 地缘

- **CHIPS Act** = 美国/欧盟芯片法案,补贴半导体本土产能。
- **EU CHIPS Act 2** = 欧盟第二轮(2026-05),锁定 SiC 三家:SIVE / SOI / XFAB。
- **US Commerce Dept** = 美国商务部,出口管制 + CHIPS 资金分配。
- **ITAR** = International Traffic in Arms Regulations 国际武器贸易条例,限制军事技术出口。
- **BIS** = Bureau of Industry and Security 美国商务部工业安全局,执行出口管制。
- **Entity List** = 美国出口管制黑名单(华为 / 中芯等被列入)。
- **国产替代** = 中国本土取代进口的产业政策(对应韬定律链条)。
- **China 出口管制**(锗/镓/铟等)= 2023+ 中国对关键金属出口实施许可证管理,触发 5N+ 等西方供应商 alpha。

---

## 标的代码后缀(交易所)

- **.US** = 美国证券交易所(NYSE / NASDAQ / OTC,综合)。
- **.TO** = 多伦多证交所(加拿大)。
- **.HK** = 香港交易所。
- **.LSE** = 伦敦证券交易所。
- **.PA** = 巴黎泛欧交易所(Euronext Paris)。
- **.AS** = 阿姆斯特丹(Euronext)。
- **.BR** = 布鲁塞尔(Euronext)。
- **.ST** = 斯德哥尔摩。
- **.DE / .F / .XETRA / .STU** = 德国交易所(法兰克福 / Xetra / 斯图加特)。
- **.T** = 东京证券交易所。
- **.KS / .KO** = 韩国交易所(KOSPI)。
- **.TW** = 台湾证交所(主板)。
- **.TWO** = 台湾柜买中心(OTC 创柜板)。
- **.SHG** = 上海证交所(科创板 / 沪 A)。
- **.SHE** = 深圳证交所(创业板 / 深 A)。

---

## 公司 / 子部门(常被简称)

- **Mag7** = 美股七巨头:AAPL / MSFT / GOOGL / AMZN / META / NVDA / TSLA。
- **SDC** = Samsung Display Corporation 三星显示(未单独上市,在 005930 里)。
- **AVX** = 京瓷的 MLCC 子部门(Kyocera AVX)。
- **TPU** = Google 自研 AI 加速器(Tensor Processing Unit),AVGO 代工。
- **Trainium / Inferentia** = AWS 自研 AI 加速器。
- **Maia** = 微软自研 AI 加速器。

---

## 编辑日志

- **2026-06-01 创建**:初始预填 120+ 条,覆盖 5 个 dogfood 主题(商业航天/A 股半导体/800VDC/MLCC/个人 AI PC)+ 光子学/AI 算力种子。
- **后续 LLM 自动 enrich**:每次报告中出现 glossary 未收录的术语 → LLM 必须先 append 到本文件,再用 `<abbr>` 包裹。
