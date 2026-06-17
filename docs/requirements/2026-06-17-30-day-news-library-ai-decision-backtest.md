# 30 天新闻库 + 技术候选点 + AI 决策回测需求文档

## 背景

当前日线回测已经支持价格数据落盘、新闻事件文件和页面决策展示，但实际使用时出现过“回测跑了，模拟交易记录为 0”的情况。排查后发现核心问题不是页面展示，而是新闻数据与 K 线日期没有形成稳定的历史证据库：

1. 价格数据可以回溯较长时间，但新闻文件只覆盖很短日期。
2. 新闻发布时间可能晚于当前最新 K 线，不能用于过去 K 线决策，否则会形成未来函数。
3. 现有事件文件和股票池不完全一致，部分标的没有新闻覆盖。
4. 页面缺少“为什么没有交易”的覆盖诊断，用户难以判断是策略没触发还是数据不足。

因此下一版先做 30 天新闻库方案：按股票落盘新闻，用技术指标筛候选日期，再让 AI 只分析候选日期之前可见的新闻，最后生成买入、卖出或观望决策。

## 目标

1. 为每只股票建立独立的 30 天新闻库。
2. 回测时先用技术指标生成候选观察日，而不是直接让 AI 分析所有日期。
3. AI 只分析候选观察日前已经发布、且落在可用窗口内的新闻。
4. 策略仍由确定性规则生成买入、卖出、观望，AI 不直接下单。
5. 页面必须清楚展示：
   - 哪些日期有价格数据。
   - 哪些日期有新闻覆盖。
   - 哪些日期是技术候选点。
   - AI 对候选点附近新闻的判断。
   - 为什么最终买入、卖出或观望。
6. 没有新闻覆盖的历史 K 线只展示价格走势，不参与新闻策略胜率统计。

## 非目标

1. 不做真实下单。
2. 不读取账户、余额、持仓或密钥。
3. 不做高频或分钟级事件交易。
4. 不一次性补全多年历史新闻。
5. 不让 AI 直接决定买入或卖出。
6. 不把没有新闻覆盖的历史日期算成“新闻策略失败”。

## 核心口径

第一版固定为 30 天新闻库。

选择 30 天的原因：

1. 数据量小，容易验证。
2. 页面展示更清楚。
3. 可以先把流程跑顺，再扩到 90 天或一年。
4. 能避免一上来拉取过多新闻导致结构混乱。

## 数据流

```text
价格数据落盘
-> 每只股票新闻库落盘
-> 技术指标生成候选观察日
-> 从新闻库读取候选日前可见新闻
-> AI 生成结构化新闻判断
-> 策略规则生成决策
-> 落盘决策、模拟交易、图表 marker、页面诊断
```

## 新闻库落盘要求

### 存储粒度

新闻按股票单独存储。

建议目录：

```text
data/news/<SYMBOL>/raw/
data/news/<SYMBOL>/ai-events/
data/news/<SYMBOL>/coverage.json
```

示例：

```text
data/news/AMDUSDT/raw/2026-06-17.json
data/news/AMDUSDT/ai-events/2026-06-17.json
data/news/AMDUSDT/coverage.json
```

### raw 新闻字段

每条原始新闻至少包含：

| 字段 | 说明 |
| --- | --- |
| `news_id` | 新闻唯一 ID |
| `symbol` | 标的，例如 `AMDUSDT` |
| `ticker` | 美股 ticker，例如 `AMD` |
| `published_at` | 新闻发布时间 |
| `fetched_at` | 本地抓取时间 |
| `source_name` | 来源名称 |
| `source_type` | 来源类型 |
| `title` | 标题 |
| `summary` | 摘要，没有则为空 |
| `url` | 原文链接 |

### AI 结构化字段

AI 对新闻只做结构化判断，字段至少包含：

| 字段 | 示例 | 说明 |
| --- | --- | --- |
| `sentiment` | `bullish` / `bearish` / `neutral` | 新闻方向 |
| `strength` | `strong` / `medium` / `weak` | 新闻强度 |
| `confidence` | `0.0` 到 `1.0` | 判断置信度 |
| `topic` | `earnings_guidance` | 新闻主题 |
| `time_horizon` | `short_term` / `medium_term` / `long_term` | 影响周期 |
| `stock_relevance` | `direct` / `indirect` / `weak` | 与股票相关性 |
| `ai_reason` | 文本 | AI 判断理由 |

## 技术候选点要求

技术指标不直接买入，只负责筛出“值得看新闻”的候选观察日。

第一版候选点规则：

1. 买入候选：
   - close > MA50。
   - MA20 > MA50，或 MA50 斜率向上。
   - RSI < 75。
2. 卖出候选：
   - 持仓后 close < MA50。
   - 或持仓后从最高价回撤达到 12%。
   - 或候选日前存在强利空新闻。

候选点需要落盘，便于页面展示。

建议文件：

```text
data/backtests/<SYMBOL>/1d/latest/technical-candidates.json
```

## 新闻匹配要求

回测某个候选日时，只允许读取该候选日决策时间点之前已经发布的新闻。

禁止：

```text
用候选日之后发布的新闻解释候选日买入。
```

第一版新闻窗口：

1. 日线候选点默认读取过去 72 小时新闻。
2. 如果遇到周末或美股休市，允许继续使用 72 小时窗口。
3. 如果 72 小时内无新闻，则该候选点标记为“无新闻覆盖”，不参与新闻策略胜率统计。

## 决策规则

### 买入

满足全部条件才生成模拟买入：

1. 当前是买入候选点。
2. 候选点前可见新闻中存在强利好。
3. `stock_relevance = direct`。
4. `confidence >= 0.7`。
5. 当前没有持仓。

### 卖出

满足任一条件可生成模拟卖出：

1. 当前是卖出候选点且已持仓。
2. 候选点前可见新闻中存在强利空。
3. 持仓后 close < MA50。
4. 持仓后从最高价回撤达到 12%。

### 观望

以下情况必须写入观望记录：

1. 技术面达标，但无新闻覆盖。
2. 有新闻，但 AI 判断不够强。
3. 有强新闻，但股票相关性不是 `direct`。
4. 有强利好，但 RSI 过热。
5. 已持仓，但没有卖出条件。

## 页面要求

页面需要新增或强化以下信息：

1. 新闻库覆盖区间：
   - 每只票新闻最早日期。
   - 每只票新闻最新日期。
   - 新闻条数。
2. 有效新闻回测区间：
   - 从新闻覆盖开始的日期。
   - 不把无新闻覆盖日期算入新闻策略胜率。
3. 候选点列表：
   - 日期。
   - 技术原因。
   - 是否找到新闻。
   - AI 新闻判断。
   - 最终动作。
4. 无交易原因：
   - 没新闻。
   - 新闻在 K 线之后，不能使用。
   - 技术候选没触发。
   - AI 判断不够强。
   - 风控阻止。
5. 图表 marker：
   - 买入点。
   - 卖出点。
   - 技术候选观察点，必须和真实买入/卖出 marker 使用不同颜色和文字，避免混淆。

## CLI 要求

第一版建议新增或调整为三步命令：

### 1. 拉取 30 天新闻库

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli fetch-news-library \
  --config configs/us_stock_daily_external.json \
  --days 30 \
  --output-dir data/news
```

### 2. 运行新闻库回测

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/us_stock_daily_external.json \
  --news-library data/news \
  --output-dir reports/us-stock-daily-news-library
```

### 3. 打开网页

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web \
  --config configs/us_stock_daily_external.json \
  --output-dir reports/us-stock-daily-news-library \
  --news-library data/news \
  --port 8014
```

实际参数名可在实现方案中按现有 CLI 风格微调，但必须保持“先拉新闻库，再回测，再看页面”的流程。

## 落盘产物要求

新增或更新以下文件：

```text
data/news/<SYMBOL>/raw/*.json
data/news/<SYMBOL>/ai-events/*.json
data/news/<SYMBOL>/coverage.json
reports/us-stock-daily-news-library/decision-records.json
reports/us-stock-daily-news-library/technical-candidates.json
reports/us-stock-daily-news-library/news-coverage.json
reports/us-stock-daily-news-library/markers.json
reports/us-stock-daily-news-library/candidate-markers.json
reports/us-stock-daily-news-library/backtest-report.md
```

## 验收标准

| 编号 | 验收项 | 验证方式 | 通过标准 |
| --- | --- | --- | --- |
| AC-1 | 能按股票生成 30 天新闻库 | 运行 `fetch-news-library` | 每只配置标的生成 `data/news/<SYMBOL>/coverage.json` |
| AC-2 | 新闻库包含 raw 新闻 | 文件检查 | raw 文件包含标题、发布时间、来源、URL、抓取时间 |
| AC-3 | AI 结构化字段可落盘 | 文件检查或测试 | `ai-events` 中包含 sentiment/strength/topic/time_horizon/stock_relevance |
| AC-4 | 技术候选点可落盘 | 回测输出检查 | 生成 `technical-candidates.json` |
| AC-5 | 禁止未来新闻 | 单元测试 | 候选日之后发布的新闻不会参与该日决策 |
| AC-6 | 无新闻覆盖不计入新闻策略胜率 | 报告检查 | 报告区分价格覆盖和新闻策略有效覆盖 |
| AC-7 | 买入决策可解释 | 回测样例或测试 | 买入记录包含技术原因、新闻标题、AI 判断和最终原因 |
| AC-8 | 无交易原因可解释 | 页面检查 | 页面显示无交易是因无新闻、无候选点、AI 不够强或风控阻止 |
| AC-9 | 页面展示新闻库覆盖 | 页面检查 | 每只票能看到新闻覆盖日期和条数 |
| AC-10 | 不触发实盘行为 | 代码和运行检查 | 不读取账户、不下单、不要求交易密钥 |
| AC-11 | 技术候选点图表可见且不混淆 | 页面检查 | 候选观察点 marker 与真实买入/卖出 marker 颜色和文字不同 |

## 安全边界

本功能只做本地数据落盘、AI 结构化新闻分析、回测和页面展示。

禁止：

1. 真实下单。
2. 查询真实账户。
3. 写入密钥、token、私钥。
4. 后台运行长任务。
5. 把 AI 输出作为直接交易指令。

## 已确认口径

当前已确认：

1. 第一版使用 30 天新闻库。
2. 采用混合方案：先按股票落盘新闻库，再由技术指标筛候选点，AI 只分析候选点附近新闻。
3. 无新闻覆盖的历史日期只展示价格，不参与新闻策略胜率统计。
4. 第一版新闻来源继续优先使用现有 Yahoo RSS / Bitget skill 导出，暂不接新的付费新闻源。
5. 技术候选观察点需要在图表上展示，并和真实买卖 marker 明确区分。
