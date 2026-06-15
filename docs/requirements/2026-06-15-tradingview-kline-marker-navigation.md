# TradingView 风格 K线与买卖点定位需求文档

## 1. 基本信息

- 需求名称：TradingView 风格 K线与买卖点定位
- 所属项目：Bitget AI Hackathon，美股 AI 交易赛道
- 项目路径：`/Users/ada/Documents/bitget ai`
- 创建日期：2026-06-15
- 文档状态：待用户确认后进入代码实现
- 参考项目：`/Users/ada/Documents/daily_stock_analysis-main/`

## 2. 背景

当前页面已经有两层结构：第一层是多票行情列表，第二层是单票运行详情。详情页目前使用原生 canvas 绘制简单价格折线，能看 AMDUSDT 走势，但不像专业行情图，也不能在图上标注买入 / 卖出动作。

参考项目的行情详情页使用 `lightweight-charts`，也就是 TradingView 官方轻量图表库。它不是嵌入 TradingView 网站，而是在本地页面里渲染 K 线、成交量、缩放、十字光标和悬停信息。这个方向适合当前项目，因为回测买卖点来自本地落盘数据，可以绑定到下方明细表。

## 3. 目标

1. 保留当前轻量网页和两层页面结构，不整套迁移 React / Vite。
2. 把单票详情页的简单 canvas 折线替换为 TradingView Lightweight Charts 风格的 K 线图。
3. 在 K 线图上标注真实回测买入 / 卖出动作。
4. 用户点击图上的买入 / 卖出标记后，页面自动滚动到下方“交易决策明细表”的对应行。
5. 被定位到的明细行短暂高亮，方便用户看到这笔动作为什么发生。
6. 新增清晰的落盘结构，支持未来多票、多周期、按日期保存行情和回测产物。
7. 页面默认读取 `latest` 回测结果；历史日期快照先落盘保存，第一版不做日期切换 UI。

## 4. 非目标

1. 本轮不整套迁移到 React / Vite。
2. 本轮不引入后台常驻服务、定时任务或自动监控。
3. 本轮不做真实交易、下单、账户读取、余额读取、持仓读取。
4. 本轮不把所有新闻事件都标到图上。
5. 本轮不把观望记录标到图上；观望只在明细表里展示。
6. 本轮不实现多个回测日期之间的页面切换器。
7. 本轮不把参考项目的 FastAPI、Electron、机器人通知、账号体系搬进当前项目。

## 5. 专家口径

采用 Marcos López de Prado 的量化回测视角：

1. 图上的每个交易标记必须能追溯到落盘的交易 / 决策记录。
2. 标记不能只是视觉装饰，必须能回答“这笔交易为什么发生”。
3. 页面展示和落盘数据要一一对应，避免前端临时拼出无法复盘的买卖点。

## 6. 页面口径

### 6.1 第一层：多票行情列表

保持当前一行一个标的的行情列表：

- 标的
- 最新价
- 回测收益
- 最大回撤
- 最新观点
- 交易次数
- 最新动作
- 新闻强度
- 技术确认
- 详情入口

用户点击标的后进入单票详情页。

### 6.2 第二层：单票详情页

单票详情页展示：

1. 返回行情列表按钮。
2. 标的名称与周期。
3. K 线覆盖、新闻覆盖、有效回测覆盖。
4. TradingView Lightweight Charts 风格 K 线图。
5. 买入 / 卖出标记。
6. 回测总览。
7. 交易决策明细表。
8. 新闻与事件信号。
9. 只读回测安全提示。

### 6.3 图表行为

图表第一版必须支持：

| 功能 | 口径 |
| --- | --- |
| K 线 | 使用 open/high/low/close 渲染蜡烛图 |
| 成交量 | 优先显示 volume 柱；若实现成本过高，可在第一版先不显示，但需求和计划里必须明确 |
| 缩放 / 拖动 | 使用 `lightweight-charts` 默认能力 |
| 悬停信息 | 显示当前 K 线日期、开、高、低、收、成交量 |
| 买入标记 | 绿色向上箭头，文字 `买入` |
| 卖出标记 | 红色向下箭头，文字 `卖出` |
| 观望记录 | 不在图上标记，只在明细表展示 |

### 6.4 标记点击定位

图上的买入 / 卖出标记必须绑定到明细表行：

1. 每个真实交易动作生成一个 `decision_id`。
2. 图表 marker 带同一个 `decision_id`。
3. 明细表对应行带同一个 `decision_id`。
4. 用户点击图表 marker 后，页面滚动到对应表格行。
5. 对应行短暂高亮。
6. 如果找不到对应行，页面不报错，只保留当前视图。

示例 marker：

```json
{
  "time": "2026-06-12",
  "position": "belowBar",
  "color": "#22c55e",
  "shape": "arrowUp",
  "text": "买入",
  "decision_id": "AMDUSDT-1d-20260612-buy-001"
}
```

示例决策行：

```json
{
  "decision_id": "AMDUSDT-1d-20260612-buy-001",
  "symbol": "AMDUSDT",
  "action": "买入",
  "decision_reason": "强利好新闻成立，并且技术面确认，所以回测触发买入。"
}
```

## 7. 落盘结构

第一版新增标准化目录，同时保留现有 `reports/amd-daily/` 兼容输出。

推荐结构：

```text
data/
  market/
    AMDUSDT/
      1d/
        latest/
          candles.json
        by-date/
          2026-06-15/
            candles.json

  backtests/
    AMDUSDT/
      1d/
        latest/
          trades.json
          markers.json
          decisions.json
          coverage.json
          report.md
        by-date/
          2026-06-15/
            trades.json
            markers.json
            decisions.json
            coverage.json
            report.md
```

大白话：

- `data/market` 放行情原始数据。
- `data/backtests` 放某次回测结果。
- `latest` 给网页默认读取。
- `by-date/YYYY-MM-DD` 留历史快照。

## 8. 数据字段

### 8.1 `candles.json`

```json
[
  {
    "date": "2026-06-12",
    "timestamp_ms": 1781280000000,
    "open": 506.07,
    "high": 521.82,
    "low": 505.4,
    "close": 515.83,
    "volume": 3729.52,
    "quote_volume": 1917754.37,
    "source": "bitget_public"
  }
]
```

### 8.2 `markers.json`

```json
[
  {
    "decision_id": "AMDUSDT-1d-20260612-buy-001",
    "symbol": "AMDUSDT",
    "date": "2026-06-12",
    "timestamp_ms": 1781280000000,
    "action": "buy",
    "label": "买入",
    "price": 515.83,
    "position": "belowBar",
    "shape": "arrowUp",
    "color": "#22c55e"
  }
]
```

### 8.3 `decisions.json`

保留当前 `decision-records.json` 的解释字段，并新增稳定 `decision_id`。真实买入 / 卖出动作的 `decision_id` 必须能与 `markers.json` 对上。

## 9. 参考项目复用边界

允许借鉴 / 复制：

1. `apps/dsa-web/src/components/market-data/StockKlineChart.tsx` 的图表信息结构。
2. `lightweight-charts` standalone 静态资源，保留许可证说明。
3. 行情列表页和单票详情页的信息分层。
4. K 线悬停时展示开高低收、涨跌、成交量的方式。

不允许搬运：

1. 整套 React / Vite / Electron 工程。
2. 参考项目的数据库、通知、机器人、账号、定时任务。
3. 任何密钥、token、账户或私有配置。

## 10. 安全边界

1. 只读回测，不下单。
2. 不读取账户、余额、持仓、订单。
3. 不读取或输出密钥、token、私钥。
4. 本地 Web 服务仍由用户在前台命令启动，可用 `Ctrl+C` 停止。
5. 图表和表格只读取本地落盘文件和回测报告。

## 11. 验收标准

| 编号 | 验收项 | 验收方式 | 通过标准 |
| --- | --- | --- | --- |
| AC-1 | K 线图替换 canvas 折线 | 浏览器检查 / 静态测试 | 详情页存在 `lightweight-charts` 图表容器，不再依赖 `price-chart` canvas |
| AC-2 | 图表使用 OHLC | 单元测试 / 文件检查 | 图表数据包含 `open/high/low/close/date` |
| AC-3 | 买入 / 卖出标记落盘 | 文件检查 | `markers.json` 只包含真实 `buy/sell` 动作 |
| AC-4 | marker 与明细行绑定 | 单元测试 | marker 和明细行共享同一个 `decision_id` |
| AC-5 | 点击 marker 定位表格行 | 浏览器检查 | 点击买入 / 卖出标记后滚动到对应明细行并高亮 |
| AC-6 | 观望不画图上 | 单元测试 / 浏览器检查 | `observe` 不进入 `markers.json` |
| AC-7 | latest 落盘 | 文件检查 | `data/market/<symbol>/<interval>/latest/candles.json` 和 `data/backtests/<symbol>/<interval>/latest/*.json` 存在 |
| AC-8 | by-date 快照落盘 | 文件检查 | `by-date/YYYY-MM-DD` 下存在行情和回测快照 |
| AC-9 | 页面默认读取 latest | 浏览器检查 | 不选择日期时展示 latest 回测结果 |
| AC-10 | 安全提示保留 | 浏览器检查 | 页面仍显示只读回测、不下单、不查账户 |
| AC-11 | 测试通过 | 命令检查 | `python3 -m pytest -q` 通过 |

## 12. 需求追踪表

| 需求 | 实现位置 | 验证方式 | 状态 |
| --- | --- | --- | --- |
| TradingView 风格 K 线 | 待实施 | 浏览器检查 / 静态测试 | 待实现 |
| 买入 / 卖出 marker | 待实施 | `markers.json` 文件检查 | 待实现 |
| marker 点击定位明细行 | 待实施 | 浏览器检查 | 待实现 |
| `decision_id` 绑定 | 待实施 | 单元测试 | 待实现 |
| latest / by-date 落盘 | 待实施 | 文件检查 | 待实现 |
| 保留两层页面 | 待实施 | 浏览器检查 | 待实现 |
| 不迁移 React/Vite | 设计约束 | 代码审查 | 已确认 |
| 不做实盘 | 设计约束 | 代码审查 / 页面检查 | 已确认 |

## 13. 待确认问题

当前无阻塞问题。第一版默认读取 latest，不做历史日期切换器。

## 14. 文档自检

- [x] 目标、非目标、输入、输出、约束、风险和验收标准已写明。
- [x] 页面交互中的 marker 点击定位行为已写明。
- [x] latest / by-date 落盘结构已写明。
- [x] 敏感信息检查：未记录密钥、token、私钥、账户、余额、持仓。
- [x] 未要求实现真实下单或账户读取。
