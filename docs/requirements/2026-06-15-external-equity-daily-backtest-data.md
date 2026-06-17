# 外部美股日线落盘回测需求文档

## 背景

当前脚本已经能用 Bitget 公共 K 线跑股票类合约回测，并在网页里展示多票行情、K 线和交易决策明细。问题是 Bitget 当前股票类合约的日线历史较短，不利于验证“技术指标 + 新闻事件”在更长周期里是否有效。

本轮目标不是接实盘，也不是证明外部数据等于 Bitget 合约长期历史。本轮只把外部美股日线作为研究和回测数据源落盘，用来测试指标和新闻信号准不准。

## 目标

1. 增加一个外部美股日线数据源，用于长期回测和本地落盘。
2. 标的仍以 Bitget 支持的股票类合约展示，例如 `NVDAUSDT`，但外部数据用其底层股票 ticker，例如 `NVDA`。
3. 回测按 1 倍现货敞口模拟：只做多、不借钱、不加杠杆、不处理爆仓和资金费。
4. 页面和落盘文件必须明确价格数据来源，避免把外部现货日线误写成 Bitget 合约历史。

## 非目标

1. 不接真实下单。
2. 不读取账户、余额、仓位或密钥。
3. 不新增后台任务、定时任务或守护进程。
4. 不一次性接多个付费数据源。
5. 不实现融资融券、杠杆、资金费率、合约基差和真实滑点模型。

## 数据源口径

第一版使用 `yahoo_chart_daily`：

| 字段 | 口径 |
| --- | --- |
| 用途 | 外部美股日线落盘和长周期回测 |
| 鉴权 | 不需要密钥 |
| 标的映射 | `NVDAUSDT -> NVDA`、`AMDUSDT -> AMD`、`TSLAUSDT -> TSLA`、`AAPLUSDT -> AAPL`、`MSFTUSDT -> MSFT` |
| K 线周期 | `1d` |
| 落盘 source | `yahoo_chart_daily` |
| 回测含义 | 美股现货参考回测，不代表 Bitget 合约真实历史 |

如果后续更换为 Alpha Vantage、Polygon 或 Finnhub，只替换数据源适配层，不改变回测和网页主体结构。

## 功能范围

1. 配置文件增加 `price_source` 字段：
   - 默认值：`bitget_public`
   - 可选值：`bitget_public`、`yahoo_chart_daily`
2. 配置文件可增加 `ticker_map`：
   - 示例：`"NVDAUSDT": "NVDA"`
   - 未配置时默认去掉 `USDT`。
3. `backtest` 命令根据 `price_source` 选择 K 线客户端。
4. `fetch` 命令增加 `--source` 参数，方便单票落盘。
5. `candles.json`、`coverage.json`、`data/market/.../candles.json` 均写入实际 source。
6. Web 页面继续显示 K 线、明细和覆盖区间，并在覆盖卡片里显示数据源。
7. 公开新闻过滤需要识别常见公司别名，例如 `Apple/iPhone`、`Tesla`，避免外部新闻落盘后被误判为噪音。

## 验收标准

| 编号 | 验收项 | 验证方式 | 通过标准 |
| --- | --- | --- | --- |
| AC-1 | 配置能读取外部价格源 | 单元测试 | `price_source` 读成 `yahoo_chart_daily` |
| AC-2 | 外部日线响应能转为 Candle | 单元测试 | Yahoo Chart fixture 转出按时间升序的日线 |
| AC-3 | `fetch --source yahoo_chart_daily` 可落盘 | CLI 测试 | 输出 JSON 中 `source` 为 `yahoo_chart_daily` |
| AC-4 | `backtest` 按配置选择外部源 | CLI 测试 | 输出 coverage/candles source 为 `yahoo_chart_daily` |
| AC-5 | normalized data 保留 source | 文件检查 / 单元测试 | `data/market/<symbol>/1d/latest/candles.json` 内 source 正确 |
| AC-6 | 不触碰实盘 | 代码检查 | 无下单、无账户、无密钥读取 |
| AC-7 | 新增股票别名可匹配公开新闻 | 单元测试 | `AAPLUSDT` 能匹配 Apple/iPhone，`TSLAUSDT` 能匹配 Tesla |

## 安全边界

本功能只调用公开价格数据接口和本地文件写入。所有交易结果都是回测模拟，不代表投资建议，不执行真实交易。
