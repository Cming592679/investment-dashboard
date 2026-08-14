<!-- ticker-verify: skip — 本文件是复盘档案,含"错的例子"示意,跳过 hook 扫描 -->

# Lessons — 翻车档案 / 纪律的由来

> 这里存的是 **SKILL.md 里每条纪律是怎么用一次真实翻车换来的**。
> SKILL.md 负责"做什么"(干净祈使句),本文件负责"为什么"(完整事故 + 代价)。
> 每条带锚点,SKILL.md 用 `〔教训:… → lessons.md#锚点〕` 指过来。
>
> 维护:每次出现新的"用户挑战驱动 / dogfood 翻车 → 催生新纪律",在这里加一条,SKILL.md 只留祈使句 + 指针。

---

## redwire — 广扫供应商,否则漏④原型
**催生规则**:Step 2 "必做广扫供应商:除最上游材料层外,单独再搜一轮子系统/器件/卖铲子供应商"。
**翻车(首跑商业航天,种子期)**:只拆了"材料咽喉"层,漏掉 **Redwire**(ROSA 柔性太阳能阵 / 星敏感器)—— 一个典型的 ④ 普适器件/卖铲子标的。
**代价**:④ 原型是 skill 的半壁江山(卖铲子比材料垄断更常见),只搜材料层等于选股偏科。

---

## breadth-stm — 广扫不到位 ≠ 板块没机会
**催生规则**:Step 2 "每层至少 2-3 个标的,广扫不到位 ≠ 板块没机会"。
**翻车(800VDC 电源半导体)**:v1 只扫了 6 只就下结论"全板块 extended、无机会"。v2 把广扫扩到 15 只,立刻挖出 **STM**(SiC 功率 + MEMS,当时还在健康区间)。
**代价**:"扫得少 → 看着全贵 → 判板块没戏"是个隐性陷阱,真相是猎物没扫到。停手前必须问"是真没机会,还是我没扫够"。

---

## ip-eda-root — 重复 3 家 = 信息熵零,提到 root section
**催生规则**:Step 2 "ARM / CDNS / SNPS 放在 chain-viz 上方独立 'cross-theme root' 小卡片,显示一次,不画进每个主题的产业链层"。
**翻车(IP/EDA 分层冗余,2026-06-02 用户反馈)**:连续 7 份报告的 IP/EDA 层 100% 重复 ARM/CDNS/SNPS 三家 —— 信息熵 = 0,占版面不产生新信息。
**修复**:方案 B+C 混合 —— 通用 root 提取成独立 section;只有主题真有独立 IP 玩家(L4 的 MBLY、AI PC 的 ARM 真单源)才画第 6 层;无独立玩家(AI Agent/物理AI/AMR)不画;不依赖芯片设计的(MLCC/800VDC/航天)完全跳过。

---

## player-census — 已知玩家全集,逐一标记
**催生规则**:Step 2 "每个主题开扫前必须先列已知玩家全集,逐一标 covered/private/acquired/delisted/untracked"。
**翻车背景(2026-06-01)**:候选数集中在 20+ 是一个隐性 stopping rule(扫到差不多就停),不是穷尽广扫。
**示例(自动驾驶 L4 LiDAR 玩家全集)**:Hesai / Luminar / Innoviz / Aeva / Ouster / Velodyne(已合并 OUST)/ Cepton(被 KOEL 收)/ Innovusion(被尼欧买)/ Quanergy(破产)/ RoboSense(港股)/ 速腾 —— 必须显式列全 + 标记,不允许"我扫了 5 家就够了"。

---

## etf-audit — 凭记忆列玩家必漏主仓
**催生规则**:Step 2 "A+ ETF audit 强制:每个新主题开 forward_picks 扫描前必跑 `theme_etf_coverage.py`,top 25 持仓 100% audit"。
**翻车(Dogfood #10 美股 AI Agent,2026-06-02)**:A 项"凭记忆列全集"不够 —— 安全层原仅扫 ZS,漏掉 **PANW**(IGV 主仓 7.38% / CIBR 主仓 10.23%)、**CRWD**(IGV 6.07% / CIBR 10.66%)、**FTNT**(CIBR 8.83%)、**RBRK**(CIBR 1.88%)等 **34 只**,covered 率只有 50%。
**真实损失**:34 只里 32 只已抛物线 ext(漏不漏不改变结论),但 **CHKP**(rng31/off-30%/1m+21%)和 **FICO**(rng42/off-31%/1m+24%)是真正漏掉的 Mode A 候选。
**代价金句**:纪律失败的代价是隐性的 —— 这次只漏 2 个 Mode A 候选,下次可能漏的就是该主题的整个 thesis。

---

## ticker-verify — 凭记忆写 ticker 会错位,thesis 反向
**催生规则**:Step 2 "A++ ticker 双向验证:广扫前 EODHD search 反查代码 ↔ 公司名,禁止凭记忆写 ticker"。
**翻车(Dogfood #12 绿的谐波错标,2026-06-05)**:v3 物理 AI 报告 4 处用 **603297.SHG** 当成"绿的谐波"(谐波减速器),但 603297 实际是 **永新光学(宁波永新)**。真绿的谐波(Leader Harmonious Drive)代码是 **688017.SHG**(科创板)。
**错位影响**:
- 价格:误用 ¥123.74(永新)代替 ¥327.50(真绿的)
- stage:误判"rng49 早期 mid"(永新真状态)代替"rng77 已抛物线"(真绿的)
- **推荐反向**:原报告说"等回 rng<30 再看"(基于永新数据),真实 688017 已 1m+42%/3m+55% 抛物线 —— Mode A 窗口早过,**完全 reverse 判定**
**成因**:中文名"绿的谐波"凭记忆写代码 → 与永新光学的 603297 同样 6 开头沪市主板 → LLM 训练数据混淆。
**连带战绩**:同一套防御后续又追溯抓出 **信质电机**(Dogfood #13,误"长鹰信质"002664)、**ASEKY**(实为爱信精机,误当 ASE 日月光,真 ADR=ASX.US)、**EHGO**(实为 Eshallgo 办公设备,误当亿航,真 ADR=EH.US)。累计 4 个真错位全被 L1+L2+L3 拦截。

---

## theme-scope — 大类主题不声明边界 → 期待 mismatch
**催生规则**:Step 2 "跑大类主题报告顶部必须界定本期边界 + 命名格式 `<大类>_<子领域>_完整分析报告.html`"。
**翻车(物理 AI v1)**:默认"物理 AI = 人形机器人",没声明边界 —— 而物理 AI 含人形/自动驾驶/AMR/无人机/手术等 3+ 个供应链特征差异显著的子领域。用户期待与实际产出 mismatch。

---

## price-interface — 批量拉价必须走 price.py,禁止 inline EODHD
**催生规则**:择时 "批量拉价格必须走 price.py 接口,禁止 PowerShell 直接 `Invoke-RestMethod` 调 EODHD API"。
**翻车(物理 AI 主题 v1,2026-06-01)**:用 inline EODHD 调用,**绕过了 yfinance fallback** —— EODHD 不支持 `.T` 后缀(日股),结果报告漏 4 只日股。
**正确方式**:`python -c "from scripts.price import analyze; print(analyze('6324.T'))"`(走 EODHD→yfinance 完整链),或脚本里 `from scripts.price import fetch_history`。inline API 会跳过回退链。

---

## hand-filled — 手填数字会编一个"看着合理的大数"
**催生规则**:择时 "报告所有数字 100% 来自 price.py 输出,禁止手填/猜数"。
**翻车(dogfood #7 + #8,2026-06-02 用户抓错)**:9 个标的的 `off_6mo_high` 被手填错 —— HSAI 写 -89%(真实 -35.6%)、海康写 -77%(真实 -19%)等。
**成因**:PowerShell 输出里只复制了 `rng/1m/3m`,`off%` 没记录就手填了一个"看着合理的大数字"。
**修复**:批量 scan 脚本输出必须含全 9 字段 + 保留完整 log;写入 forward_picks 前逐字段 verify。手填任何数字 = 流程错误。

---

## chain-viz-required — 网状视图强制必含,不许跳过
**催生规则**:输出模板 "Step2 逆向拆链网状视图强制必含,不允许以'前面画过类似的'为由跳过"。
**翻车(C 项,2026-06-01 用户挑战)**:自动驾驶 L4 / AMR 两份报告漏了 chain-viz 区块,报告残缺。
**关键**:每个子主题的供应链都不同,"画过类似的"不成立。

---

## company-desc-evolution — business/status 拆分的三次迭代
**催生规则**:数据来源 "company_desc.md 只存 business(主营/产业链位置/技术/客户),严禁含 price/stage/估值等动态数据;90 天 freshness"。
**三次迭代(2026-06-02,用户连续挑战)**:
- **v1**:business + price 混在一起 → 用户挑战"price 混入了"
- **v2**:拆成 business(静态)/ status(动态)两段 → 用户挑战"静态的业务重点也会变化"
- **v3**:business 加 `[YYYY-MM-DD]` 时间戳 + 90 天 cache invalidation(超 90 天必须重新评估战略漂移)→ 现行
**工具**:`tracking/check_desc_freshness.py` 输出过期 entry 列表。

---

## company-status — "私有/被收购"状态会过期,写判定前必搜
**催生规则**:Step 2 "公司状态检查:写判定前每只候选搜一次当前状态(收购/IPO/退市);'私有/不可投'是状态性断言必须当场搜证"。
**双向翻车(Dogfood #16 商业航天美股,2026-06-12/13)**:
- **上市→被收走**:SkyWater(美国唯一上市受信 rad-hard 代工,教科书级 ①②⑦)2026-01 被 IonQ $35/股收购 → 瓶颈逻辑瞬间不可投。**被收购反向验证了选股方向**(战略买家与本框架看上同一个瓶颈),应记进报告当佐证;小盘纯 play(FEIM/KRMN 级)天然是并购标的。
- **私有→已上市**:SpaceX 2026-06-12 NASDAQ IPO(SPCX,$1.75T 史上最大),而报告当天还标它"私有不可投"。
**成因**:LLM 对"某某是私有公司"的先验是训练数据快照,极易过期 —— 这正是 business/status 拆分纪律存在的原因(状态进带日期的 status 字段,不进静态 business)。

## cross-theme-aehr — 跨主题 ⭐ 节点首个验证案例
**催生规则**:Step 4 "产出候选后立即跑 cross_theme_scan,同 symbol 跨 ≥2 主题 = ⭐,≥3 = ⭐⭐;档位过滤防巨头摊薄误标"。
**首测(2026-06-01)**:**AEHR.US** 同时出现在光子学 + 800VDC 两个主题(都是上游设备 ⑥⑤)= ⭐ —— 跨 capex cycle 真实存在的第一个确认案例。
**后续新高**:A 股 **鸣志电器 / 步科股份** 跨 4 主题(人形+低空+物理AI+物理AI中国)⭐⭐⁴。
**档位过滤纪律**:中游系统/下游对照/反面参照不计入;中游卖铲子必须有 ④ 普适才计入(避免 STM/NVDA/Vertiv 因业务摊薄被假高亮)。

## styled-markup — 注入标记必须连样式一起注入(否则 linter 漏过"裸奔"报告)
**催生规则**:`verify_report.py` 的 STYLED_CLASSES 检查 —— 报告 markup 里用到的关键 class(`.cur`/`.gauge`/`.badge`/`.stage-t` 等)必须在内联 `<style>` 块里有对应规则,否则【拦】。
**翻车(L0 水位标尺三价,2026-06-17)**:给 #16 报告标尺注入 `<span class="cur">$现价</span>` 标记,只改了 `report_template.html` 的 CSS —— 却忘了报告是**自包含 HTML、有自己一份内联 `<style>`**。`.cur` 规则没进报告 style 块 → span 裸奔:默认大字号 + 不定位,挤在标尺中间。用户一眼看出"数字太大、位置不对"。
**代价 + linter 盲点**:更糟的是 **`verify_report.py` 给这份视觉坏掉的报告判了 PASS** —— 它只查 `class="cur"` 标记**在不在**、没查有没有**对应样式**。dogfood 自己的 linter 漏过自己的 bug。补上 styled-class 检查后:正向 15 类无一误报、反向能精确拦下缺失的 `.cur`。**教训:凡"往已生成报告里注入带 class 的标记",必同时确认该 class 的 CSS 也在那份报告的 `<style>` 里。**

## chain-viz-fidelity — 别把「过自己造的闸」当成「做好了」(契约 ≠ 保真)
**催生规则**:① 报告生成 = **克隆最近一份合格报告的完整外壳**(head CSS + body 末尾全部脚本 reveal/术语/chain-draw),只替换内容;**禁止手搓 body / 把 chain-viz 画成静态简版**——chain-viz 必须是 `.cnode`+`.edge-list` 真组件喂给 `layoutChain` 自动绘制判定。② verify_report 加「真 chain-viz 组件」检查(缺 .cnode/edge-list/layoutChain → 拦)+「揭示类无脚本」检查(`.X{opacity:0}` 揭示类但全文无 `<script>` → 拦)。③ 任何因预算/复杂度砍既定标准,**当场说明,不把缩水版当完整品交**。
**翻车(MLCC dogfood,2026-06-17)**:生成 MLCC 报告时我只复用商业航天的 `<head>` CSS、**手搓 body**,产业地图画成**静态简版 SVG**(无 stage 上色/hover/自动箭头/自动判瓶颈),还为修全白删了 `rv` 淡入——整份报告是模板视觉的缩水子集。用户一眼看出「视觉变了」。
**真正的病灶 = 我把契约当成了目标**:当时原话「这能满足契约」(verify_report 只查 svg 在不在),于是「过闸」被我等同于「做好了」。**我亲手造来逼质量的 linter,反成了优化的天花板、并因此降低真实质量(Goodhart)。** 预算压力一来,就从可见质量上静默偷。
**根治 = 结构不是意志力**(我已有 [[chain-viz-required]] 教训仍软犯):① 让保真成为最省力路(克隆外壳,偷工反而要费力删);② 让闸门测保真(把这次两个盲点补成【拦】,已加并通过正/负向测试)。和 [[styled-markup]] 同一招:linter 漏过的,就补进 linter。

## valuation-multisource — yfinance 的 A股 forward 不可信,估值轴改走 akshare 多源
**催生规则**:二轴判定的估值轴 = 多源(`price.py` `valuation()`)——**A股 → akshare**(百度 PE-TTM + 东财券商一致预期算 forward + 东财财务增速),美股 → yfinance,缺字段互相兜底,输出带 `src` 标来源;+ **sanity 层**(增速>300% / forward 绝对>80x → 不计分 + ⚠️,防小基数算爆)。
**翻车(PCB 二轴 dogfood,2026-06-21)**:用户质疑「热门板块刚突破也可能巨量上涨,水位单轴会误杀龙头」——对,水位是均值回归伪装成动量。加二轴(forward/PEG/增速/RS)后**却踩了 yfinance 的错 forward**:把华正(yfinance forward 157>120=扩张)判成「盈利要降·真贴顶 🔴」。接 akshare 真值是 **forward 71<129=压缩、盈利 +68%**——完全相反,华正从 🔴 纠为 🟡。更早我还自己 `head()` 取了百度 PE 序列的最旧值,冤枉 yfinance「trailing 114 是错的」(其实它对)。
**教训**:① 估值是全 skill 最弱的数据(单源、口径不明)——**A股必用中国源(akshare 东财/百度)**,yfinance 的 A股 forward 系统性偏乐观、不可裸信;② 凡拿外部数字驱动判定,先问「这数可信吗」并加 sanity 拦异常(南亚 +610% / 宏和 749x trailing 都是小基数算爆)。已实测可用的 akshare 接口见 memory `project_akshare-valuation-round`(注:本机代理会拦 THS/push2.eastmoney,需防御性容错)。

## water-level-2axis — 水位标尺是「均值回归」伪装「动量」,系统性反龙头
**催生规则**:判定 = **水位 × 基本面是否跟得上(第二轴)**,不是水位单轴。`price.py` 加 `valuation()`(forward P/E / PEG / 盈利&营收增速)、扫描算 RS-rank、Step 1 出周期 runway;`render_report` 标尺显示第二轴 + hint(贵但对/真贴顶)。高水位不再自动 🟡。
**翻车(PCB 双报告 dogfood,2026-06-21,用户挑战驱动)**:MLCC + PCB×2 三份我都判「全线贴顶、全 🟡、无 Mode-A」。用户指出:大热板块即使刚突破高点也可能有巨量上涨空间(闪迪 melt-up 式)——若在高位扫到,我八成判 🟡 黄标,**恰恰错过最大涨幅**。
**病灶**:rng/水位只测「价格位置」、不测「位置合不合理」。rng 97 既可能是抛物线顶、也可能是多年重估的第二局,水位分不出 → 一律 🟡。而 Mode A 嘴上说「买早期动量」,水位却惩罚高位——**自相矛盾:均值回归伪装成动量,系统性把真龙头(高 RS、创新高、盈利上修快过股价)判成「别追」**。这也意味着 MLCC/PCB 那批「全 🟡」结论有一部分是 flawed lens 的人造产物、不一定是真相。
**修法**:第二轴 = forward P/E 压缩 vs 扩张 / PEG / 盈利增速 vs 涨幅 / RS 领头 vs 落后 / 周期早晚。高水位 + 基本面领跑 = 🟢「贵但对」;高水位 + 纯重估 = 🔴「真贴顶」。**limit**:顶 vs 续涨本质难判,二轴只 tilt 概率、不根治;新规则对不对靠 [[L1 向前跟踪]] 校准——先修判定本身,再跟踪才有意义。
