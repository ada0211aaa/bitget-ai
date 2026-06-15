# 多票行情列表 + 单票运行详情页需求文档

## 1. 基本信息

- 需求名称：多票行情列表 + 单票运行详情页
- 所属项目：Bitget AI Hackathon，美股 AI 交易赛道
- 项目路径：`/Users/ada/Documents/bitget ai`
- 文档状态：已按用户确认口径整理，待实施
- 创建日期：2026-06-14
- 参考页面：`/Users/ada/Documents/daily_stock_analysis-main/apps/dsa-web/src/pages/MarketDataPage.tsx` 和 `MarketDataDetailPage.tsx`

## 2. 背景

当前 Web 页面已经能展示一只股票的回测解释，但默认聚焦 `NVDAUSDT`，不方便用户查看多只股票的整体运行结果。

用户希望参考 `daily_stock_analysis-main` 的行情页面，把当前网页端口升级成更像行情工作台的结构：

1. 首页是一张多票行情表，一行一个股票。
2. 用户点击某只股票后，进入该股票自己的运行详情。
3. 详情页展示该票的价格轨迹、买入 / 卖出 / 观望记录、新闻原因和查看原文。

本轮不是重做一个 React/Vue 大系统，也不是搬运参考项目的 API、登录、账户、调度或真实行情系统；只借鉴它的页面结构和交互方式。

## 3. 目标

1. 同一个本地 Web 端口默认展示多票行情列表。
2. 列表中每只票都有清楚的回测结果摘要。
3. 点击任意一只票进入该票详情页。
4. 单票详情页复用现有价格图、决策明细表、新闻事件和原文入口。
5. 继续保持 backtest-only：不下单、不查账户、不展示密钥。
6. 尽量做最小改动，不引入前端框架、不新增数据库、不新增后端服务。

## 4. 非目标

1. 本轮不做真实交易、实盘下单、账户读取、余额读取、持仓读取。
2. 本轮不新增登录系统、多用户系统、权限系统。
3. 本轮不引入 React、Vue、Vite、FastAPI 或参考项目的大型前端架构。
4. 本轮不做手机顶部横向卡片，不做横向滑动股票卡片入口。
5. 本轮不新增复杂搜索、筛选、排序、分页；第一版先保证多票能看、能点、能回退。
6. 本轮不伪造收益、新闻或交易动作。

## 5. 页面结构

### 5.1 首页：回测行情列表

打开 `http://127.0.0.1:8000` 后默认展示行情列表页。

列表采用一行一个股票的表格，参考行情页的清晰列表结构。

建议字段：

| 字段 | 说明 |
| --- | --- |
| 标的 | 例如 `AMDUSDT / AMD` |
| 最新价 | 来自 `candles.json` 中该票最后一根 K 线 close |
| 回测收益 | 来自 `backtest-report.md` |
| 最大回撤 | 来自 `backtest-report.md` |
| 最新观点 | 来自 `backtest-report.md` |
| 交易次数 | 来自 `backtest-report.md` 或 `trades.csv` |
| 最新动作 | 该票最近一条 decision record 的动作：买入 / 卖出 / 观望 |
| 新闻强度 | 最近一条 decision record 的新闻强度 |
| 技术确认 | 最近一条 decision record 的技术确认 |
| 查看详情 | 点击进入该票详情页 |

### 5.2 单票详情页

点击某只股票后，进入 hash 路由形式的详情页：

- `/#/symbol/NVDAUSDT`
- `/#/symbol/AMDUSDT`
- `/#/symbol/MSFTUSDT`

详情页内容：

1. 返回行情列表按钮。
2. 当前标的、最新价、回测收益、最大回撤、交易次数、最新观点。
3. 价格走势 canvas。
4. 当前股票自己的交易决策明细表。
5. 当前股票自己的新闻与事件信号。
6. 有 URL 的新闻继续显示“查看原文”，新标签打开。
7. 无 URL 的结构化信号显示“查看信号详情”。
8. 无新闻来源显示“无新闻来源”。

## 6. 数据要求

### 6.1 后端 payload

`dashboard-data.json` 需要从“只给 NVDA 过滤结果”升级为“给所有股票的数据”。

必须包含：

1. `symbols` / `config.symbols`
2. `summary`
3. `trades`
4. `decision_rows`
5. `events`
6. `price_series`
7. `symbol_overview`

其中 `symbol_overview` 是面向首页列表的派生数据，至少包含：

| 字段 | 说明 |
| --- | --- |
| `symbol` | 标的代码 |
| `symbol_name` | 展示名，没有映射时可用去掉 `USDT` 的代码 |
| `latest_price` | 最新价 |
| `total_return` | 回测收益 |
| `max_drawdown` | 最大回撤 |
| `last_view` | 最新观点 |
| `trade_count` | 交易次数 |
| `latest_action` | 最新动作 |
| `latest_news_strength` | 最新新闻强度 |
| `latest_technical_confirmation` | 最新技术确认 |

### 6.2 事件过滤

事件仍需按 symbol 做相关性过滤：

1. 公开新闻降级源必须过滤掉明显不相关标题。
2. Bitget 官方技能结构化信号按 symbol 信任。
3. 首页展示摘要，详情页展示当前票相关事件。

## 7. 交互要求

1. 默认首页是行情列表，不再默认进入 NVDA 单票详情。
2. 点击表格行或“查看详情”进入对应详情页。
3. 详情页点击“返回行情列表”回到首页。
4. URL hash 可直接访问某票详情。
5. 如果 URL 中的 symbol 不存在，页面显示找不到该标的，并提供返回按钮。
6. 切换票时，价格图、决策表、新闻区必须同步切换。

## 8. 视觉要求

1. 参考 `daily_stock_analysis-main` 的行情页结构：清晰表格、信息密度高、像工作台。
2. 保持当前项目深色主题。
3. 列表页不要做顶部横向滑动卡片。
4. 页面文字全部中文。
5. 表格要适合扫读，收益和动作需要用颜色区分。
6. 详情页保留“只读回测 · 不下单”的安全提示。

## 9. 安全约束

1. 页面只读取本地回测文件和事件文件。
2. 不读取 `.env`。
3. 不读取账户、余额、持仓、订单。
4. 不提供真实下单按钮。
5. 不启动后台任务或守护进程。
6. 启动 Web 服务仍然必须是前台可见命令，用户可以 `Ctrl+C` 停止。

## 10. 验收标准

| 编号 | 验收项 | 验收方式 | 通过标准 |
| --- | --- | --- | --- |
| AC-1 | 首页是多票行情列表 | 浏览器检查 / 静态测试 | 打开根路径显示多只股票表格，不再只显示 NVDA |
| AC-2 | 一行一个股票 | 浏览器检查 | 表格中至少显示配置里的 5 个 symbol |
| AC-3 | 可进入详情 | 浏览器检查 | 点击 `AMDUSDT` 后 URL 变为 `/#/symbol/AMDUSDT` 并显示 AMD 详情 |
| AC-4 | 可返回列表 | 浏览器检查 | 详情页返回按钮回到列表 |
| AC-5 | 数据按票切换 | 单元测试 / 浏览器检查 | AMD 详情只显示 AMD 的决策、事件、价格序列 |
| AC-6 | 原文按钮保留 | 浏览器检查 | 有 URL 的新闻显示“查看原文”并新标签打开 |
| AC-7 | 安全提示保留 | 浏览器检查 | 页面仍显示只读回测、不下单、不查账户 |
| AC-8 | 测试通过 | 命令检查 | `python3 -m pytest -q` 通过 |

## 11. 运行口令

实现完成后，运行方式仍保持：

```bash
cd "/Users/ada/Documents/bitget ai"

PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/default_universe.json \
  --events data/events/us_stock_events.json \
  --output-dir reports/latest

PYTHONPATH=src python3 -m bitget_ai_backtest.cli web \
  --config configs/default_universe.json \
  --output-dir reports/latest \
  --events data/events/us_stock_events.json \
  --port 8000
```

## 12. 需求追踪表

| 需求 | 实现位置 | 验证方式 | 状态 |
| --- | --- | --- | --- |
| 多票行情列表 | `src/bitget_ai_backtest/static/index.html` / `app.js` | 静态测试 + 浏览器检查 | 待实现 |
| 单票详情页 | `src/bitget_ai_backtest/static/app.js` | 静态测试 + 浏览器检查 | 待实现 |
| 全量 payload | `src/bitget_ai_backtest/web.py` | `tests/test_web.py` | 待实现 |
| 按票过滤决策和事件 | `web.py` / `app.js` | 单元测试 + 浏览器检查 | 待实现 |
| 保留原文按钮 | `app.js` | 静态测试 + 浏览器检查 | 待实现 |
| 保留安全边界 | `index.html` / `web.py` | 浏览器检查 | 待实现 |

## 13. 文档自检

- [x] 没有 TODO / TBD / 占位符
- [x] 目标、非目标和安全边界明确
- [x] 页面结构、数据结构和交互口径明确
- [x] 验收标准可测试
- [x] 未记录密钥、账户、余额、持仓或完整实盘策略参数
