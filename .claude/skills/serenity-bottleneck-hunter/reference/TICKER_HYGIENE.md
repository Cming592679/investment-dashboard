<!-- ticker-verify: skip — 本文档含"错的例子"示意,跳过 hook 扫描 -->

# Ticker Hygiene — L1 + L2 + L3 三层防御使用文档

> 2026-06-05 用户挑战驱动(绿的谐波 ticker 错标 case)

## 问题本质

LLM 不可信任 "ticker → 公司名" 凭记忆映射。
- hallucination 概率 ~5%,**无自察觉信号**
- 一次错标可能让整个主题的 thesis 反向(本次绿的谐波 case:误"等回 rng<30 入场" → 实际"已 ext 抛物线")

## 三层防御

### L1 · ground truth 数据库

文件:`reference/ticker_truth.csv`

Schema:
```
ticker,name_en,name_zh,exchange,sector,last_verified,source
688017.SHG,"Leader Harmonious Drive Systems Co Ltd",绿的谐波,SHG,Common Stock,2026-06-05,EODHD search
603297.SHG,"Ningbo Yongxin Optics Co Ltd",永新光学,SHG,Common Stock,2026-06-05,EODHD search
```

- 90 天 freshness check,过期重新 EODHD search
- 初始化:`python scripts/init_ticker_truth.py`(从历史 forward_picks 一次性 init)

### L2 · resolve_tickers.py 工作流改造

**所有 `_scan_*.py` 必须用 NAMES 先行模式,禁止 hardcode (ticker, name) 元组**。

#### 旧模式(禁用 · 易错标):
```python
SYMBOLS = [
    ("603297.SHG", "绿的谐波 谐波减速器单源"),  # ❌ 凭记忆写,容易错
    ("603667.SHG", "五洲新春 行星滚柱丝杠"),
    ...
]
```

#### 新模式(强制):
```python
from ticker_truth import resolve_tickers

NAMES = [
    "绿的谐波", "五洲新春", "北特科技",
    "奥普光电", "鸣志电器", "步科股份",
]
# resolve_tickers 走 ground truth 命中或 EODHD search 新增 → 返回 [(ticker, name_zh, name_en), ...]
SYMBOLS = resolve_tickers(NAMES, theme_hint="物理AI中国")

for ticker, zh, en in SYMBOLS:
    if ticker is None:
        print(f"⚠ {zh} NOT_FOUND, 手动查证")
        continue
    # 然后再做 price.py 9 字段扫描
    r = analyze(ticker)
    ...
```

#### 已知 ticker 验证(单只):
```python
from ticker_truth import verify_pair
ok, reason = verify_pair("688017.SHG", "绿的谐波")
if not ok:
    raise ValueError(f"ticker fail: {reason}")
```

### L3 · git pre-commit hook 自动拦截

- 装一次:`powershell scripts/install_pre_commit.ps1`(私库 + 公库各装一个)
- 之后:每次 `git commit` 前自动跑 `verify_tickers.py --staged`
- 扫描 staged 文件里所有 ticker 模式(数字.SHG/HK/US 等),对每个查 ticker_truth.csv 旁边的中文名是否匹配
- mismatch → 阻止 commit + 显示 diff
- bypass(紧急用):`git commit --no-verify`(不推荐)

## CLI 速查

| 命令 | 用途 |
|---|---|
| `python scripts/ticker_truth.py lookup 688017.SHG` | 查单只 ground truth |
| `python scripts/ticker_truth.py verify 688017.SHG "绿的谐波"` | 验证一对 (ticker, name) |
| `python scripts/ticker_truth.py resolve 绿的谐波 五洲新春` | 多个中文名 → 解析为 ticker |
| `python scripts/ticker_truth.py stats` | 看 DB 统计 |
| `python scripts/init_ticker_truth.py` | 全量 init/refresh DB |
| `python scripts/verify_tickers.py path/to/file.html` | 手动 scan 单文件 |
| `python scripts/verify_tickers.py --staged` | scan git staged 文件(hook 调用) |

## 失效场景(L3 hook 仍可能漏)

| 场景 | 原因 | 缓解 |
|---|---|---|
| EODHD search 本身错 | 外部 ground truth 不是 100% 可信 | 用户挑战是终极防线 |
| 新上市公司未在 EODHD 收录 | 训练截止后的新代码 | 手动加入 ticker_truth.csv |
| 中文公司名极短 + 通用词冲突 | regex match 噪音 | 调 STOPWORDS list |
| 港股繁简体差异 | "小鵬汽車" vs "小鹏汽车" | 在 name_zh 字段同时存 |
| 北交所 / OTC EODHD 不支持 | 鼎智科技 case | 标 untracked + 文档说明 |

## 三道闸门类比(SKILL.md 已写入)

| 闸 | 防什么 | 工具 |
|---|---|---|
| A 穷尽性 | 防漏 | A+ ETF audit + 人工列已知玩家全集 |
| A+ ETF audit | 防偏 | `scripts/theme_etf_coverage.py` |
| **A++ ticker 双向验证** | **防错位** | `scripts/ticker_truth.py` + `verify_tickers.py` + pre-commit hook |

## 教训金句

> 穷尽性纪律(A)防漏 + ETF audit(A+)防偏 + ticker 双向验证(A++)防错位 — 三道闸都得过

> LLM 不知道自己什么时候在 hallucinate — **不要让 LLM 写 ticker,要让 LLM 消费已验证 ticker**
