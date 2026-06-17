# Bitget AI Hackathon - 美股 AI 新闻交易回测台

本项目参加 **Bitget AI Base Camp Hackathon S1 - 美股 AI Trading** 赛道。目标不是做实盘自动下单，而是做一个可解释的美股/代币化美股 AI 回测工具：把真实新闻、技术趋势和风险退出规则放到同一张 K 线图和决策表里，回答“为什么买、为什么卖、依据是哪条新闻”。

## 第一段：核心假设与真实痛点

核心假设是：美股科技股和代币化美股的短中期波动，不能只看 MA、RSI 这类技术指标，也不能只看一条孤立新闻。更实用的信号应该是 **新闻事件强度 + 股票相关性 + 日线趋势确认 + 风险退出规则** 的组合。策略只在真实新闻触发时考虑买入，没有新闻时即使技术面有观察信号也不下单；卖出则来自看空新闻、跌破 MA50、或持仓后从高点明显回撤。

它解决的真实痛点是：普通回测经常只给收益曲线，用户看不懂每次交易的原因；新闻策略又容易混入未来新闻，或者只停留在“情绪分数”。本工具把每个股票的新闻先落盘，再按时间回测，并在页面里展示买入/卖出点、匹配新闻、技术原因和后续结果。用户可以点股票进入详情页，直接看到 K 线上的真实买卖点和对应决策表。

## 第二段：完成度、问题与下一步

开发中最大的问题是新闻覆盖。最早只用 Yahoo RSS，新闻实际只覆盖最近一两天，导致买点都出现在最后一根 K 线附近，没有后续 K 线可卖出。后来我们接入了 `daily_stock_analysis-main` 的新闻归档、SEC EDGAR 官方公告，并新增 Google News 按月搜索，把 5 个美股标的的新闻覆盖补到约 2 年。另一个问题是页面上“观察点”太多，影响看买卖点，已改成图表只显示真实买入/卖出 marker。

当前已完成：多票行情入口、单票详情页、TradingView 风格 K 线、新闻落盘、2 年新闻搜索、新闻覆盖统计、技术候选记录、买卖决策表、买卖点跳转、回测只读安全边界。尚未实现：实盘下单、账户读取、真实仓位同步、专业付费新闻源、LLM 深度新闻判分。下一步计划是把 SEC/网页新闻再过一层 AI 结构化判断，减少“标题关键词误判”，并增加更严格的卖出解释与胜率统计。

使用能力包括：Bitget Agent Hub / Skill Hub 的新闻、宏观、技术、情绪、market-intel 思路与导出结构；Bitget Playbook API 的回测包与报告流程；Yahoo 美股日线数据；Yahoo Finance RSS；SEC EDGAR；Google News RSS date-window search；以及本地 Python CLI + vanilla JS dashboard。当前项目仍然是 **backtest-only**，不读取账户、不放置真实订单、不保存任何交易密钥。

## 当前核心结果

最新 2 年全网新闻回测输出：

```text
报告目录：reports/us-stock-daily-2y-web-search
新闻库：data/news-us-stock-2y-web-search
标的：NVDAUSDT / AMDUSDT / TSLAUSDT / AAPLUSDT / MSFTUSDT
K线覆盖：2025-01-13 -> 2026-06-16
真实买入点：30
真实卖出点：26
观察记录：1724
```

新闻覆盖：

```text
AAPLUSDT 2024-06-17 -> 2026-06-16，292 条
AMDUSDT  2024-06-19 -> 2026-06-17，276 条
MSFTUSDT 2024-06-18 -> 2026-06-17，270 条
NVDAUSDT 2024-06-18 -> 2026-06-17，276 条
TSLAUSDT 2024-06-17 -> 2026-06-17，276 条
```

## 快速运行

进入项目：

```bash
cd "/Users/ada/Documents/bitget ai"
```

重新拉 2 年新闻并落盘：

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli fetch-news-library \
  --config configs/us_stock_daily_external_2y.json \
  --days 730 \
  --output-dir data/news-us-stock-2y-web-search \
  --external-news-archive /Users/ada/Documents/daily_stock_analysis-main/data/news_archive \
  --include-sec-edgar \
  --include-web-search
```

运行 2 年回测：

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/us_stock_daily_external_2y.json \
  --news-library data/news-us-stock-2y-web-search \
  --output-dir reports/us-stock-daily-2y-web-search
```

打开网页：

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web \
  --config configs/us_stock_daily_external_2y.json \
  --output-dir reports/us-stock-daily-2y-web-search \
  --news-library data/news-us-stock-2y-web-search \
  --port 8017
```

浏览器访问：

```text
http://127.0.0.1:8017
```

如果端口被占用，把 `--port 8017` 换成 `--port 8021`。

## 主要文件

```text
configs/us_stock_daily_external_2y.json          2 年多票回测配置
src/bitget_ai_backtest/cli.py                   CLI 入口
src/bitget_ai_backtest/events.py                新闻事件结构与基础新闻源
src/bitget_ai_backtest/external_news_collectors.py 外部新闻员：归档 / SEC / Google News
src/bitget_ai_backtest/news_library.py          新闻落盘与读取
src/bitget_ai_backtest/conservative_policy.py   新闻 + 技术 + 风控决策
src/bitget_ai_backtest/static/                  中文深色网页
reports/us-stock-daily-2y-web-search/           最新 2 年回测报告
data/news-us-stock-2y-web-search/               最新 2 年新闻库
```

## 安全边界

- 本项目只做回测和演示，不做实盘交易。
- 不读取 Bitget 账户、仓位、余额。
- 不放置真实订单。
- 不提交 API key、secret、passphrase、私钥或账户数据。
- Playbook API 只用于受控回测流程，运行结果会脱敏保存。

## 测试

```bash
python3 -m pytest -q
```

当前验证结果：

```text
91 passed
```
