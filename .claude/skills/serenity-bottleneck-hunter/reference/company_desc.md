# Company Desc — 公司业务描述库(永久可复用)

> **设计原则(2026-06-02 用户挑战驱动)**:本文件只存 **business 描述**(主营/产业链位置/技术/客户),**严禁包含 price/stage/跨主题数/市值/估值** 等动态数据 — 后者每月都变,会过期或误导。
>
> **拆分对照**:
> - 🟢 **business 描述(本文件,static)**:5 年不变的事实 — 公司是干啥的、在产业链什么位置、关键技术、主要客户
> - 🔴 **status 描述(dynamic,每份报告 LLM 现写,带日期标签)**:price/stage/跨主题数/估值/动量 — 报告生成时刻的快照,过期就过期
>
> 在 `.cnode` 里:
> - `data-desc="<business 静态>"` — 从本文件取
> - `data-status="<dynamic 动态>[YYYY-MM-DD]"` — LLM 每次报告时写,带日期
>
> HTML hover tooltip 同时显示两段:business(上,无日期)+ status(下,带日期)
>
> **维护**:每跑新主题,LLM 检查 company_desc.md,若标的没收录 → **必须先 append business 描述**(只写永久部分),再回报告写 data-status。

---

## IP / EDA / 标准

- **ARM.US** [2026-06-02] = ARM Holdings,英国芯片 IP 授权龙头。设计 CPU/GPU/NPU 架构授权给 SoC 厂(高通/苹果/NVDA Grace 都基于 ARM)。每片 ARM-based SoC 必交版税。
- **CDNS.US** [2026-06-02] = Cadence Design Systems,EDA(芯片设计软件)双寡头之一。SoC/ASIC 设计必用,与 Synopsys 双寡头垄断。
- **SNPS.US** [2026-06-02] = Synopsys,EDA 另一寡头(与 Cadence 并列)。设计自动化工具 + IP 核库,所有先进制程 SoC 设计必用。

## 半导体 / 上游材料

- **STM.US** [2026-06-02] = STMicroelectronics,欧洲半导体综合龙头(法意合资)。SiC 功率器件 + MEMS 传感器领先,汽车 + 800V 电源主供。
- **WOLF.US** [2026-06-02] = Wolfspeed,美国 SiC 衬底+器件公司。150mm → 200mm 转产中。
- **XFAB.PA** [2026-06-02] = X-FAB Silicon Foundries,欧洲半导体代工厂。美国 Commerce 点名的高产能 SiC 代工,EU + US CHIPS Act 双背书。
- **ON.US** [2026-06-02] = onsemi(安森美),美国 SiC 综合大厂。自家 fab + Treo 800V 汽车平台。
- **IFX.DE** [2026-06-02] = Infineon Technologies,德国功率半导体大厂。SiC + GaN 综合,与 NVDA 联合开发 800V 电源。
- **MPWR.US** [2026-06-02] = Monolithic Power Systems,美国高效 PMIC 电源管理芯片厂。专注高效率 buck/boost/LDO,服务数据中心 + AI PC + 机器人 + 车载电源。
- **MU.US** [2026-06-02] = Micron Technology,美国 DRAM/NAND/HBM 三大件存储厂。LPDDR5X / HBM 主要供应商之一。
- **TSM.US** [2026-06-02] = 台积电,全球最大芯片代工。InFO/SoIC/CoWoS 先进封装主导,2nm 制程领先。
- **NVDA.US** [2026-06-02] = NVIDIA,AI GPU 主流(H100/Blackwell/Rubin)。Drive Thor 自动驾驶 + NIM/Jetson 物理 AI 平台。
- **AVGO.US** [2026-06-02] = Broadcom,半导体 + 软件综合大厂。定制 ASIC(代工 Google TPU)+ 网络芯片龙头。
- **AMD.US** [2026-06-02] = Advanced Micro Devices,Ryzen CPU + Radeon GPU + MI300X AI 加速器。Ryzen AI 300 是 AI PC SoC。
- **INTC.US** [2026-06-02] = Intel,x86 CPU 巨头。Lunar Lake / Panther Lake 是 AI PC NPU SoC 主流之一。
- **QCOM.US** [2026-06-02] = Qualcomm,Snapdragon 移动 SoC 龙头。Snapdragon X Elite/Plus 是 ARM 阵营 AI PC 旗舰。

## 半导体 / 上游设备

- **AEHR.US** [2026-06-02] = AEHR Test Systems,SiC 功率器件 burn-in 老化测试设备小盘。跨光子学 + 800VDC 测试。
- **0522.HK** [2026-06-02] = ASMPT,先进封装设备(TCB 热压键合)主供。CoWoS 等 2.5D/3D 封装核心装备。
- **ONTO.US** [2026-06-02] = Onto Innovation,先进封装/AI 衬底计量设备公司。封装产能扩张必用其测量设备。
- **AMAT.US** [2026-06-02] = Applied Materials,半导体设备综合大厂(沉积/刻蚀/CMP/计量)。
- **AMKR.US** [2026-06-02] = Amkor Technology,全球封装代工厂(ASE 之后第 2)。CoWoS 等先进封装的核心合作伙伴。
- **0522.HK** [2026-06-02] = ASMPT 同上。
- **TRMB.US** [2026-06-02] = Trimble Inc,高精度 GNSS + 测绘综合大厂。业务覆盖自动驾驶 + 农业 + 建筑测量。
- **HXGBY.US** [2026-06-02] = Hexagon AB ADR(瑞典),测绘 + 工业自动化综合。
- **RSW.LSE** [2026-06-02] = Renishaw,英国高精度编码器全球龙头。业务覆盖医疗 + 工业 + 航天。

## MLCC / 被动元件

- **300285.SHE** [2026-06-02] = 国瓷材料,A 股 MLCC 介质粉(钛酸钡)主要供应商。中国市场份额领先,服务三星电机等。
- **605376.SHG** [2026-06-02] = 博迁新材,纳米镍粉(MLCC 内电极材料)技术领先。
- **4078.T** [2026-06-02] = Sakai Chemical,日本钛酸钡领先供应商,水热法工艺。
- **002859.SHE** [2026-06-02] = 洁美科技,MLCC 离型膜 / 载带 国产替代领跑。
- **KN.US** [2026-06-02] = Knowles Corporation,美股特种高可靠陶瓷电容(医疗/国防/半导设备用)。MLCC 细分领域。
- **VSH.US** [2026-06-02] = Vishay Intertechnology,被动元件综合大厂(MLCC + 二极管 + 电阻)。
- **6981.T** [2026-06-02] = Murata Manufacturing,日本 MLCC 全球龙头。垂直整合自制材料 + 设备。
- **TTDKY.US** [2026-06-02] = TDK ADR,日本 TDK 公司 ADR。MLCC + HDD 磁头 + 电池 + InvenSense MEMS 综合。

## 半导体 / 中游器件

- **POWI.US** [2026-06-02] = Power Integrations,AC-DC 集成芯片中游(800V 链稳健)。
- **NVTS.US** [2026-06-02] = Navitas Semiconductor,GaN 功率半导体小盘公司。
- **VICR.US** [2026-06-02] = Vicor Corporation,DC-DC 模块产品龙头。
- **IPWR.US** [2026-06-02] = Ideal Power,B-TRAN 双向晶体管技术微盘公司。
- **MBLY.US** [2026-06-02] = Mobileye Global,Intel 拆分的 ADAS 芯片公司。EyeQ ASIC 全球辅助驾驶主流。
- **AMBA.US** [2026-06-02] = Ambarella,边缘视觉 SoC 公司。机器人 / 自动驾驶 / 安防视觉芯片。
- **NXPI.US** [2026-06-02] = NXP Semiconductors,荷兰车规 MCU 主供。汽车电子核心元件。
- **MXL.US** [2026-06-02] = MaxLinear,美国 Wi-Fi 7 + 连接芯片厂。
- **SIMO.US** [2026-06-02] = Silicon Motion,SSD 主控芯片公司。本地 AI 推理对大 SSD 需求拉动。
- **SYNA.US** [2026-06-02] = Synaptics,触控芯片 + 边缘 AI。
- **INDI.US** [2026-06-02] = Indie Semiconductor,车规模拟 + RF 芯片公司。

## 物理 AI / 机器人零部件

- **688017.SHG** [2026-06-05] = **绿的谐波(Leader Harmonious Drive)**,A 股谐波减速器主要供应商。全球第 3 梯队(Harmonic Drive 日 / Nabtesco 日 之后),人形机器人关节核心。**注意**:此前 v3 报告把 ticker 错标为 603297,2026-06-05 用户挑战驱动修复。
- **603297.SHG** [2026-06-05] = **永新光学(Ningbo Yongxin Optics)**,车载镜头 + 显微镜光学元件 + 激光元件。物理 AI 上游材料(车载视觉/机器人视觉镜头),但不是真单源(舜宇/水晶光电同业)。**注意**:此前 v3 报告把这只错当成"绿的谐波"用了,2026-06-05 修正名称(真绿的谐波是 688017.SHG)。
- **603667.SHG** [2026-06-02] = 五洲新春,行星滚柱丝杠潜力公司。Tesla Optimus 线性执行器关键零件。
- **603009.SHG** [2026-06-02] = 北特科技,行星滚柱丝杠双 player 之一(与五洲新春并列)。
- **002338.SHE** [2026-06-02] = 奥普光电,A 股光电编码器纯 play。机器人关节角度精度元件。
- **603728.SHG** [2026-06-02] = 鸣志电器,空心杯电机 A 股龙头。Maxon 风格精细电机,人形机器人手指等执行器。
- **688160.SHG** [2026-06-02] = 步科股份,无框力矩电机 + 伺服。人形机器人大型关节直驱。
- **6324.T** [2026-06-02] = Harmonic Drive Systems,日本谐波减速器全球龙头。
- **6268.T** [2026-06-02] = Nabtesco,日本 RV 减速器全球龙头。
- **6954.T** [2026-06-02] = Fanuc,日本工业机器人四大家族之一。
- **6506.T** [2026-06-02] = Yaskawa Electric,日本伺服 + 工业机器人本体大厂。
- **002747.SHE** [2026-06-02] = 埃斯顿,A 股工业机器人本体龙头。
- **AVAV.US** [2026-06-02] = AeroVironment,美军主要军用无人机供应商(Switchblade 巡飞弹 + Puma 战术 + JUMP 20)。
- **KTOS.US** [2026-06-02] = Kratos Defense,XQ-58 协同战斗机 + Mako 高超音速靶机。美军 NGAD/CCA 项目承包商。
- **002415.SHE** [2026-06-02] = 海康威视,全球安防监控 / 机器视觉龙头。
- **002236.SHE** [2026-06-02] = 大华股份,全球安防第 2(海康之后)。
- **SYM.US** [2026-06-02] = Symbotic,仓储自动化公司,Walmart 长期合同。
- **AUTO.OL** [2026-06-02] = AutoStore,挪威仓储立体库自动化公司。
- **CGNX.US** [2026-06-02] = Cognex Corporation,美国机器视觉龙头(工业精密检测)。
- **6861.T** [2026-06-02] = Keyence,日本机器视觉全球第 2,以高毛利率著称。
- **ISRG.US** [2026-06-02] = Intuitive Surgical,da Vinci 手术机器人全球龙头。
- **SYK.US** [2026-06-02] = Stryker,MAKO 骨科手术机器人 + 综合医疗器械。
- **DE.US** [2026-06-02] = Deere & Company,农业机械精准化龙头。See & Spray 智能耕作。
- **AGCO.US** [2026-06-02] = AGCO Corporation,农机第 2 梯队(Fendt 品牌)。
- **CAT.US** [2026-06-02] = Caterpillar,建筑机械龙头。
- **ABBNY.US** [2026-06-02] = ABB ADR(瑞士),工业机器人 + 电气化"四大家族"之一。
- **AMZN.US** [2026-06-02] = Amazon,AWS Bedrock Agents + 自营机器人(Kiva 仓储/Astro 家用)。

## 自动驾驶 / 车载

- **HSAI.US** [2026-06-02] = Hesai Group 禾赛科技,中国 LiDAR 出货量领先(车规 + Robotaxi 双线)。
- **LAZR.US** [2026-06-02] = Luminar Technologies,美国 LiDAR 公司(Velodyne 后合并体)。
- **AEVA.US** [2026-06-02] = Aeva Inc,FMCW LiDAR 技术路线。
- **OUST.US** [2026-06-02] = Ouster,美国数字 LiDAR 厂(与 Velodyne 合并)。
- **INVZ.US** [2026-06-02] = Innoviz Technologies,以色列小盘 LiDAR。
- **603501.SHG** [2026-06-02] = 韦尔股份,A 股 CMOS 图像传感器(CIS)龙头,旗下 OmniVision 车规 CIS 全球前列。
- **AUR.US** [2026-06-02] = Aurora Innovation,美国自动驾驶卡车 L4 上市纯 play。
- **CRNC.US** [2026-06-02] = Cerence,车载语音 AI(Nuance 拆分)。
- **TSLA.US** [2026-06-02] = Tesla,FSD 自动驾驶 + Optimus 人形机器人。
- **LI.US** [2026-06-02] = 理想汽车,中国新势力 EV,L2+ 智驾。
- **XPEV.US** [2026-06-02] = 小鹏汽车,中国新势力 EV,XNGP 智驾。
- **NIO.US** [2026-06-02] = 蔚来,中国新势力 EV。
- **GM.US** [2026-06-02] = General Motors,美国传统车企(Cruise Robotaxi 子公司)。
- **F.US** [2026-06-02] = Ford Motor Company,美国传统车企。
- **688256.SHG** [2026-06-02] = 寒武纪,中国 AI 芯片公司。

## AI 算力 / AI Agent 经济

- **NBIS.US** [2026-06-02] = Nebius Group,GPU 算力出租新云公司。
- **DDOG.US** [2026-06-02] = Datadog,云监控 + APM 综合龙头,延伸到 LLM observability。
- **MDB.US** [2026-06-02] = MongoDB,Atlas Vector 是企业 RAG 主流向量数据库。NoSQL 文档数据库 + 向量搜索。
- **NET.US** [2026-06-02] = Cloudflare,CDN + 边缘计算 + AI Gateway。
- **CFLT.US** [2026-06-02] = Confluent,Kafka 流式数据平台(Apache Kafka 商业版)。
- **SNOW.US** [2026-06-02] = Snowflake,云数据仓库 + Cortex AI Agent 集成。
- **ESTC.US** [2026-06-02] = Elastic NV,Elasticsearch + vector search 搜索引擎。
- **FROG.US** [2026-06-02] = JFrog,软件供应链管理(Artifactory/Xray)。
- **FSLY.US** [2026-06-02] = Fastly,边缘 CDN(Cloudflare 竞争者)。
- **CRM.US** [2026-06-02] = Salesforce,CRM SaaS 全球龙头。Agentforce 是其企业 Agent 平台。
- **PLTR.US** [2026-06-02] = Palantir Technologies,政府 + 企业 AI 数据分析平台(Foundry + AIP)。
- **NOW.US** [2026-06-02] = ServiceNow,企业 IT 服务管理(ITSM)龙头,Now Assist 是其 Agent 产品。
- **MNDY.US** [2026-06-02] = monday.com,以色列工作管理 SaaS。AI workflow agents 新方向。
- **APPN.US** [2026-06-02] = Appian,美国低代码 BPM 平台。Process Automation + AI agents。
- **PATH.US** [2026-06-02] = UiPath,RPA(机器人流程自动化)龙头,转型 Agentic Automation。
- **HUBS.US** [2026-06-02] = HubSpot,营销/销售 SaaS 中小企业市场。
- **NICE.US** [2026-06-02] = NICE Ltd,以色列客服自动化龙头。
- **ZS.US** [2026-06-02] = Zscaler,云安全网关(SSE)龙头。
- **BILL.US** [2026-06-02] = BILL Holdings,美国 SMB 财务自动化 SaaS。
- **AI.US** [2026-06-02] = C3.ai,企业 AI 应用平台。
- **GTLB.US** [2026-06-02] = GitLab,代码托管 + DevOps 一体化(GitHub 竞争者)。
- **SOUN.US** [2026-06-02] = SoundHound AI,语音识别 + 语音 AI agents。
- **APP.US** [2026-06-02] = AppLovin,移动广告 AI 平台。
- **DBX.US** [2026-06-02] = Dropbox,云存储 + Dropbox AI 文档功能。
- **S.US** [2026-06-02] = SentinelOne,AI 驱动的端点安全。
- **MSFT.US** [2026-06-02] = Microsoft,Azure 云 + Copilot Studio + OpenAI 战略合作。
- **GOOGL.US** [2026-06-02] = Alphabet,Google + Gemini LLM + Vertex AI Agent Builder。
- **META.US** [2026-06-02] = Meta Platforms,Llama 开源 LLM 持有方 + 广告 + 元宇宙。
- **AAPL.US** [2026-06-02] = Apple,M 系列芯片 + Apple Neural Engine + 设备生态。
- **ZI.US** [2026-06-02] = ZoomInfo Technologies,B2B 销售情报数据库。

### AI 安全层(2026-06-02 ETF audit 补 — IGV/CIBR 持仓发现)
- **PANW.US** [2026-06-02] = Palo Alto Networks,企业级网络安全 + AI 防火墙巨头。AI Access Security(管员工/Agent 调用 LLM 流量)+ AI Runtime Security(保护 AI app)+ Prisma AIRS(2025 收购 Protect AI)。CIBR 第 2 大仓 10.23%。
- **CRWD.US** [2026-06-02] = CrowdStrike,云原生端点安全龙头。Falcon Platform + Charlotte AI(对话式安全 Agent)。CIBR 第 1 大仓 10.66%。
- **FTNT.US** [2026-06-02] = Fortinet,网络安全融合(SD-WAN + Firewall + Cloud)。FortiAI 是其内嵌 LLM 威胁分析。CIBR 第 3 大仓 8.83%。
- **RBRK.US** [2026-06-02] = Rubrik,云数据保护 + DSPM(数据安全态势管理)。Ruby AI 是其 GenAI 安全运营助手。卡 AI agent 训练/RAG 的数据治理必经路径。2024 IPO。
- **TENB.US** [2026-06-02] = Tenable,漏洞管理 + ExposureAI(AI 风险优先级排序)。
- **QLYS.US** [2026-06-02] = Qualys,云原生漏洞 + 合规扫描。TruRisk AI 是其 AI 风险评估。
- **SAIL.US** [2026-06-02] = SailPoint,身份治理(IAM 细分)。AI 身份分析。2025 重新 IPO(Thoma Bravo 私有化后)。
- **OKTA.US** [2026-06-02] = Okta,企业身份认证 + SSO 龙头。Agent 调用 SaaS API 必经身份验证层。
- **CHKP.US** [2026-06-02] = Check Point Software,以色列网络安全老牌(Infinity 平台 + AI 威胁防御)。
- **AKAM.US** [2026-06-02] = Akamai,CDN + 边缘安全。Guardicore(2021 收购)做微分段。
- **FFIV.US** [2026-06-02] = F5 Networks,应用流量管理 + 应用安全(API + bot defense)。
- **GEN.US** [2026-06-02] = Gen Digital,消费安全(Norton + LifeLock + Avast 合并)。

### AI 应用层(2026-06-02 ETF audit 补 — WCLD/IGV 持仓发现)
- **FIVN.US** [2026-06-02] = Five9,云客服平台。Agentic AI(IVA + Agent Assist)是其 Genesys/NICE 对标 AI 客服 Agent 主线。
- **TWLO.US** [2026-06-02] = Twilio,通信 API 平台(SMS/Voice/WhatsApp)+ Segment CDP + AI 客服 Agent。
- **BRZE.US** [2026-06-02] = Braze,客户互动平台(消息/推送/邮件)+ AI 个性化营销 Agent。
- **ZETA.US** [2026-06-02] = Zeta Global,AI 营销云 + ZOE 平台。
- **PAYC.US** [2026-06-02] = Paycom,人力资源 SaaS(Beti 自助薪资 + AI HR Agent)。
- **FRSH.US** [2026-06-02] = Freshworks,客服/IT 服务台 SaaS。Freddy AI 是其内嵌 AI Agent。
- **IOT.US** [2026-06-02] = Samsara,Connected Operations 平台(车队/资产追踪)+ AI fleet/物联网 Agent。
- **PD.US** [2026-06-02] = PagerDuty,事件响应 SaaS。AIOps + AI Agent 自动响应。
- **DOCU.US** [2026-06-02] = DocuSign,电子签名龙头 + IAM(智能协议管理)+ AI 合同分析。
- **ZM.US** [2026-06-02] = Zoom Communications,视频会议 + Zoom Phone + AI Companion(会议总结 Agent)。
- **TEAM.US** [2026-06-02] = Atlassian,Jira/Confluence 工作管理。Rovo 是其 AI Agent(2024 发布)。
- **WDAY.US** [2026-06-02] = Workday,人力资本 + 财务 SaaS。Workday AI(HR/Fin Agent)。
- **FICO.US** [2026-06-02] = Fair Isaac,FICO 信用评分(消费金融行业标准)+ AI 决策 Agent。
- **ROP.US** [2026-06-02] = Roper Technologies,垂直行业软件 conglomerate(Aderant/Deltek/Strata 等 30+ 子公司)。AI 在子公司内嵌。

### 网络安全板块补充(2026-06-05 Dogfood #15,ETF audit CIBR+BUG+HACK)
- **NTSK.US** [2026-06-05] = Netskope,SSE(安全服务边缘)纯 play,Zscaler 直接对手。2025-09 IPO 后破发。
- **VRNS.US** [2026-06-05] = Varonis Systems,DSPM 数据安全态势管理(文件/SaaS 数据权限分析),AI 数据治理标的。
- **CVLT.US** [2026-06-05] = Commvault,企业数据备份恢复老牌,云转型中(Rubrik 的传统对手)。
- **RDWR.US** [2026-06-05] = Radware,以色列 DDoS 防护 + 应用安全。
- **RPD.US** [2026-06-05] = Rapid7,漏洞管理 + SIEM(InsightIDR)+ MDR 服务,长期落后于 TENB/QLYS,PE 收购传闻常客。
- **300454.SHE** [2026-06-05] = 深信服(Sangfor),A 股安全+云计算双主业,民企市场份额第一,SASE/超融合。
- **002212.SHE** [2026-06-05] = 天融信(Topsec),国内第一台自研防火墙厂商,政企安全老牌。
- **300369.SHE** [2026-06-05] = 绿盟科技(NSFOCUS),攻防研究/漏洞挖掘强项,安全服务+设备。
- **601360.SHG** [2026-06-05] = 三六零(360),消费安全入口 + 政企安全 + AI 大模型(纳米搜索)双题材。
- **688023.SHG** [2026-06-05] = 安恒信息(DBAPPSecurity),安全运营 SOC + MSS 托管服务 + 数据安全。
- **300768.SHE** [2026-06-05] = 迪普科技(DPtech),网络安全设备 + 应用交付(国产 F5 对标)。
- **002268.SHE** [2026-06-05] = 电科网安(Westone,原卫士通),中国电科旗下商用密码国家队,密码安全核心。
- **603232.SHG** [2026-06-05] = 格尔软件(Koal),PKI 公钥基础设施龙头,密码应用。
- **688201.SHG** [2026-06-05] = 信安世纪(Infosec Tech),密码技术 + 信创安全。
- **300352.SHE** [2026-06-05] = 北信源(VRV),终端安全管理 + 安全准入。
- **300659.SHE** [2026-06-05] = 中孚信息(Zhongfu),保密安全(党政军涉密信息系统)。
- **300188.SHE** [2026-06-05] = 美亚柏科(Meiya Pico),电子数据取证第一,国投智能旗下,公安政法市场。
- **688168.SHG** [2026-06-05] = 安博通(ABT Networks),安全策略可视化 + 网关。
- **CYBR(已退市)** [2026-06-05] = CyberArk,PAM 特权账户管理近垄断 — 2025 被 PANW ~$25B 收购退市,标 acquired。

### AI Infra / Observability 层(2026-06-02 ETF audit 补)
- **DT.US** [2026-06-02] = Dynatrace,APM + AIOps observability。Davis AI(因果推理 AI)。DDOG 主要对标。
- **NTNX.US** [2026-06-02] = Nutanix,超融合基础设施 + 私有云。GPT-in-a-Box(私有部署 LLM 解决方案)。
- **NTAP.US** [2026-06-02] = NetApp,企业存储 + AIPod(与 NVIDIA 合作的 AI 存储参考架构)。
- **DOCN.US** [2026-06-02] = DigitalOcean,中小企业云平台。GPU 云 + AI infra(2024 转型)。

## AI Agent 经济(A股 + 港股)

- **688256.SHG** [2026-06-02] = 寒武纪科技,A 股 AI 芯片厂(思元系列推理芯片)。
- **688041.SHG** [2026-06-02] = 海光信息,A 股 AI/CPU 芯片国产替代(深算 GPU 系列)。
- **300308.SHE** [2026-06-02] = 中际旭创,光模块全球龙头之一。AI 数据中心 800G/1.6T 光模块主供。
- **000977.SHE** [2026-06-02] = 浪潮信息,中国 AI 服务器主要供应商。海若大模型 + 元脑 Agent 平台。
- **603019.SHG** [2026-06-02] = 中科曙光,中国 AI 服务器 + 高性能计算厂。
- **603296.SHG** [2026-06-02] = 华勤技术,AI 服务器 ODM 代工。
- **688158.SHG** [2026-06-02] = 优刻得 UCloud,A 股第三方云计算 + AI 算力服务。
- **300229.SHE** [2026-06-02] = 拓尔思,A 股 NLP + 知识图谱 + 大模型应用(政务/媒体方向)。
- **688787.SHG** [2026-06-02] = 海天瑞声,A 股 AI 训练数据集纯 play(语音/视觉/NLP 标注)。
- **688561.SHG** [2026-06-02] = 奇安信,A 股网络安全龙头。AI agents API 安全护栏新方向。
- **002439.SHE** [2026-06-02] = 启明星辰,A 股网络安全主供(被中移动控股)。
- **688030.SHG** [2026-06-02] = 山石网科,A 股网络安全小盘(下一代防火墙)。
- **688111.SHG** [2026-06-02] = 金山办公,A 股 WPS Office 龙头。WPS AI 是类 Copilot 国产替代。
- **600588.SHG** [2026-06-02] = 用友网络,A 股企业 ERP 龙头(SAP 国产替代)。YonGPT 企业级大模型 + AI agents。
- **0268.HK** [2026-06-02] = 金蝶国际,港股企业 ERP + 云 SaaS。金蝶云苍穹 + AI Agent。
- **300033.SHE** [2026-06-02] = 同花顺,A 股金融信息服务龙头。i 问财 AI 是金融场景智能助手。
- **002410.SHE** [2026-06-02] = 广联达,A 股建筑工程 SaaS 龙头(BIM)。AI 嵌入项目管理流程。
- **603039.SHG** [2026-06-02] = 泛微网络,A 股 OA(协同办公)主供。e-cology + AI 流程自动化。
- **688369.SHG** [2026-06-02] = 致远互联,A 股 OA(协同办公)中型厂商。
- **002315.SHE** [2026-06-02] = 焦点科技,A 股跨境 B2B 电商 SaaS(Made-in-China.com)+ AI 营销 agents。
- **2013.HK** [2026-06-02] = 微盟集团,港股微信营销 SaaS + AI 智能营销(腾讯生态)。
- **0020.HK** [2026-06-02] = 商汤集团,港股 AI 视觉龙头 + 商量大模型(日日新)。
- **1357.HK** [2026-06-02] = 美图公司,港股美图秀秀 / 美颜相机 / AI 设计工具(订阅制商业化)。
- **9988.HK** [2026-06-02] = 阿里巴巴,港股电商 + 阿里云 + 通义千问 LLM + 百炼 Agent 平台。
- **0700.HK** [2026-06-02] = 腾讯,港股微信 + 游戏 + 腾讯云 + 混元大模型 + 元宝。
- **9888.HK** [2026-06-02] = 百度,港股搜索 + 百度云 + 文心一言 LLM + 千帆 Agent 平台。
- **3690.HK** [2026-06-02] = 美团,港股本地生活服务 + LongCat 自研 LLM + 内部业务 agents。
- **9618.HK** [2026-06-02] = 京东,港股自营电商 + 京东云 + 言犀大模型。

## 商业航天 / 防务

- **VNP.TO** [2026-06-02] = 5N Plus,西方少数能产锗 / 镓 / 铟 + AZUR 空间太阳能电池。
- **MTRN.US** [2026-06-02] = Materion Corporation,铍材料公司(空间反射镜/制导/高超音速)。
- **RKLB.US** [2026-06-02] = Rocket Lab,小型火箭发射 + 卫星总包公司。
- **RDW.US** [2026-06-02] = Redwire,空间太阳能阵(ROSA)+ 星敏感器。
- **JOBY.US** [2026-06-02] = Joby Aviation,eVTOL(电动垂直起降)飞行汽车,Toyota 投资。
- **ACHR.US** [2026-06-02] = Archer Aviation,eVTOL 飞行汽车,Stellantis 投资。
- **EH.US** [2026-06-05] = 亿航智能(EHang Holdings),中国 eVTOL,全球唯一载人无人驾驶航空器适航三证(型号合格证+生产许可+标准适航证)。**注意**:此前误用 EHGO.US(实为 Eshallgo 办公设备)— 2026-06-05 hook 追溯拦截修复。
- **EHGO.US** [2026-06-05] = Eshallgo,中国办公设备/打印服务微盘股。非 eVTOL — 此前被错标为亿航,已修复。

## A 股半导体(韬定律)

- **688072.SHG** [2026-06-02] = 拓荆科技,混合键合 + PECVD 设备(3D NAND 堆叠核心)。
- **688120.SHG** [2026-06-02] = 华海清科,CMP(化学机械抛光)设备国产领先。
- **688012.SHG** [2026-06-02] = 中微公司,刻蚀设备国产替代主供。
- **002371.SHE** [2026-06-02] = 北方华创,半导体设备平台型公司(综合)。
- **600584.SHG** [2026-06-02] = 长电科技,先进封装代工 A 股龙头。
- **002156.SHE** [2026-06-02] = 通富微电,先进封装(给 AMD/华为代工)。

## 光子学(2026 历史种子)

- **AXTI.US** [2026-06-02] = AXT Inc,InP 衬底主要供应商(全球 40% 份额)。光通信激光器链上游。
- **SIVE.ST** [2026-06-02] = Sivers Semiconductors,瑞典 SiPh 设计 + InP 收发器小盘公司。
- **LITE.US** [2026-06-02] = Lumentum Holdings,光通信器件大厂。
- **TSEM.US** [2026-06-02] = Tower Semiconductor,SiPh / 光子学代工(IBM 收购完成后)。
- **SOI.PA** [2026-06-02] = Soitec,SOI 衬底 + CPO 衬底主要供应商(法国)。
- **IQE.LSE** [2026-06-02] = IQE plc,化合物半导体外延片(英国)。

## 中游系统 / 数据中心电源

- **VRT.US** [2026-06-02] = Vertiv Holdings,数据中心电源系统集成(液冷 + UPS + PDU)。
- **ETN.US** [2026-06-02] = Eaton Corporation,电气基础设施(数据中心配电)。
- **2382.TW** [2026-06-02] = Quanta Computer,台湾笔电 ODM 龙头。
- **2356.TW** [2026-06-02] = Inventec,台湾笔电 ODM。
- **5392.TWO** [2026-06-02] = Auras Technology,台湾散热模组 Vapor Chamber 供应商。
- **3324.TW** [2026-06-02] = 双鸿科技,台湾笔电散热龙头。
- **3483.TWO** [2026-06-02] = 力致科技,台湾散热模组公司。
- **0522.HK** [2026-06-02] = ASMPT,香港上市的封装设备公司。
- **ASX.US** [2026-06-05] = 日月光 ASE(ASE Industrial Holding ADR),台湾封测 OSAT 综合大厂。**注意**:此前误用 ASEKY.US(实为爱信精机)— 2026-06-05 hook 追溯拦截修复。
- **ASEKY.US** [2026-06-05] = 爱信精机(Aisin Seiki),日本汽车零部件(丰田系,变速箱/车身件)。非半导体公司 — 此前被错标为 ASE 日月光,已修复。
- **LPL.US** [2026-06-02] = LG Display ADR,韩国 OLED 屏幕(笔电 + 电视屏)。
- **005930.KO** [2026-06-02] = Samsung Electronics,韩国半导体 + 显示综合巨头。
- **000660.KO** [2026-06-02] = SK Hynix,韩国 LPDDR + HBM 第 2 大供应商。
- **6981.T** [2026-06-02] = Murata 同上,日本 MLCC 全球龙头。
- **CTS.US** [2026-06-02] = CTS Corporation,陶瓷元件多元(压电/传感器/MLCC)。
- **KYOCY.US** [2026-06-02] = Kyocera ADR,日本京瓷 ADR,含 Kyocera AVX MLCC 子部门。
- **MRAAY.US** [2026-06-02] = Murata ADR,日本村田制作所 ADR(MLCC #1)。

---

## 编辑日志

- **2026-06-02 创建**:初始预填 100+ 个跨 11 个主题的标的(business 描述)。
- **2026-06-02 重构(用户挑战驱动)**:**清洗所有动态信息**(price/stage/跨主题数/市值/估值)— 只保留 business static 描述。Dynamic 内容(status)交给每份报告的 LLM 在 `data-status` 属性里现写,带日期标签。
- **维护**:每跑新主题 → LLM append 新标的 business 描述到本文件 → 再到报告里写 data-status 动态。
