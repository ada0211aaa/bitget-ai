# Bitget Playbook AI 科技股策略需求文档

## 0. Skills 使用要求

写这份文档前已按要求使用：

1. `superpowers:brainstorming`
   - 已澄清赛道、工具优先级、策略方向、实现边界和安全边界。
2. `writing-requirements-docs`
   - 当前阶段只写需求文档和项目初始化文件，不写业务代码、不配置密钥、不运行交易。
3. `superpowers:verification-before-completion`
   - 交付前检查文档结构、占位符、敏感信息、验收标准和 Git 状态。

## 1. 基本信息

- 需求名称：Bitget Playbook AI 科技股新闻情绪策略
- 所属项目：`/Users/ada/Documents/bitget ai`
- 文档状态：草案，待用户确认
- 需求来源：用户口述 + Bitget AI Base Camp Hackathon S1 官方规则
- 创建日期：2026-06-07
- 最近更新：2026-06-07

## 2. 背景

用户计划参加 Bitget AI Base Camp Hackathon S1 的美股 AI 交易赛道。用户的原始想法是：通过新闻和行情分析，决定美股相关资产什么时候买入、卖出或观望。

比赛要求 Demo 真实可运行，并能说清楚解决了谁的什么问题；美股 AI 交易赛道尤其关注是否围绕美股代币化交易场景解决真实问题，是否有可验证的回测或模拟交易记录，以及是否使用 Bitget 提供的美股相关数据或工具。

为了降低实现复杂度和安全风险，本轮优先使用 Bitget 现成能力，而不是从零搭建新闻爬虫、交易执行器或复杂 Web 产品。

## 3. 目标

1. 形成一个可参赛的最小方案：用 Bitget Playbook 创建、回测并发布一个 AI 科技股交易策略。
2. 策略主题聚焦 AI 科技股，例如 NVDA、MSFT、GOOGL、AMD、META 或 Playbook 支持的对应美股代币化资产。
3. 策略性格为稳健型：新闻、宏观和趋势信号同向时才交易；信号冲突时优先观望。
4. 所有核心工具优先使用 Bitget 现成能力，尤其是 Bitget Playbook 和 Bitget Agent Hub 官方 skills。
5. 产出可用于提交和开发日记的材料：策略说明、回测指标、使用记录、公开展示文案草稿。

## 4. 非目标

1. 本轮不开发自定义交易执行引擎。
2. 本轮不接入真实资金下单。
3. 本轮不写入真实 Playbook API Key、Bitget API Key、secret、passphrase、私钥或真实账户敏感信息。
4. 本轮不自建新闻爬虫、行情数据库或复杂 Web UI。
5. 本轮不追求高频新闻抢跑；新闻源存在延迟时，策略仍按中低频稳健策略处理。
6. 本轮不承诺收益，不输出“保证赚钱”或直接投资建议。

## 5. 使用场景

| 场景 | 使用者 | 触发条件 | 预期结果 |
| --- | --- | --- | --- |
| 参赛策略创建 | 用户 | 用户拿到 Playbook API Key 后，希望生成一个参赛策略 | 通过 Playbook 创建 AI 科技股策略并生成可回测版本 |
| 策略回测 | 用户 | Playbook 策略创建完成后 | 得到 PnL、最大回撤、夏普比率等回测指标 |
| 策略说明 | 用户 / 评委 | 提交项目或录制演示视频时 | 能用 200 字以内讲清楚策略解决的问题、闭环和 Bitget 工具使用 |
| 开发日记 | 用户 / 社区 | 开发期间需要公开展示进展 | 在 X/Twitter 发布带 `#BitgetHackathon` 和 `@Bitget_AI` 的项目进展帖 |
| 安全检查 | 用户 / Codex | 需要提交 GitHub 仓库前 | 仓库不包含真实密钥、账户敏感信息或可直接实盘运行的完整策略 |

## 6. 功能范围

### 6.1 必须实现

1. 写清楚策略主题：AI 科技股新闻情绪 + 宏观风险 + 趋势确认。
2. 写清楚工具优先级：
   - Bitget Playbook 用于自然语言策略创建、上传、回测、发布和指标输出。
   - Bitget Agent Hub 官方 skills 用于辅助信号生成。
3. 写清楚第一版策略逻辑：
   - 新闻和产业叙事偏利好；
   - 宏观环境不明显 risk-off；
   - 技术趋势确认；
   - 三者同向时买入或加仓；
   - 任一关键信号冲突时观望或降低仓位。
4. 写清楚可提交证据：
   - Playbook 策略或 Demo 链接；
   - 回测指标；
   - 模拟交易或回测记录；
   - 项目说明；
   - 开发日记帖子链接。
5. 初始化 Git 仓库，便于后续上传 GitHub。

### 6.2 可以后置

1. 可视化网页 Demo。
2. 自动生成开发日记长文。
3. 多策略对比，例如稳健型、事件驱动型、激进型。
4. 更完整的 Agent Hub MCP 集成。
5. 视频演示脚本和录屏素材整理。

### 6.3 明确禁止

1. 禁止把真实密钥、API Key、私钥或账户敏感信息提交到 Git。
2. 禁止未经用户明确确认运行真实下单、自动调仓或后台交易任务。
3. 禁止为了比赛演示伪造回测结果、模拟交易记录或 API 调用记录。
4. 禁止把 Playbook 或 Agent Hub 未明确支持的能力写成已经实现。
5. 禁止把策略包装成投资建议或收益保证。

## 7. 脚本与系统架构草案

本项目第一版采用文档型架构和 Bitget Playbook 优先方案。下图用于说明未来如果逐步脚本化时应如何拆层；它不是当前已实现代码，也不代表当前要启动数据库、Web/API、通知或定时任务。

```mermaid
flowchart TD
    subgraph Entry["入口"]
        E1["README.md<br/>项目入口说明"]
        E2["docs/playbook/playbook-prompt.md<br/>Playbook 策略 Prompt"]
        E3["后续可选 CLI 入口<br/>仅在实施计划确认后新增"]
    end

    subgraph Config["配置"]
        C1["docs/strategy/*.md<br/>策略口径与可调规则"]
        C2["docs/bitget-skills/*.md<br/>Skill 使用说明"]
        C3["环境变量占位说明<br/>不写真实 Key"]
    end

    subgraph DataSources["数据源"]
        D1["Bitget Playbook<br/>历史数据 / 回测 / 发布"]
        D2["Bitget news-briefing<br/>新闻与叙事"]
        D3["Bitget macro-analyst<br/>Fed / DXY / VIX / Nasdaq"]
        D4["Bitget technical-analysis<br/>趋势 / RSI / MACD / 均线"]
        D5["Bitget sentiment-analyst<br/>情绪与拥挤度辅助"]
        D6["Bitget market-intel<br/>机构 / ETF / 主题叙事辅助"]
    end

    subgraph Database["数据库"]
        DB1["第一版不建数据库"]
        DB2["docs/playbook/backtest-record.md<br/>人工记录回测结果"]
        DB3["未来可选 SQLite / CSV<br/>存信号快照与回测记录"]
    end

    subgraph Core["核心流程"]
        P1["每日信号收集<br/>日线级"]
        P2["新闻指标提取<br/>财报/指引 + AI 芯片/算力需求"]
        P3["宏观风险判断<br/>risk-on / mixed / risk-off"]
        P4["技术趋势确认<br/>上涨 / 震荡 / 走弱"]
        P5["风控硬过滤<br/>先防亏、少犯大错"]
        P6["信号打分<br/>重大事件加权"]
        P7["五档观点输出<br/>看多 / 谨慎看多 / 中性观望 / 谨慎看空 / 看空"]
    end

    subgraph WebAPI["Web/API"]
        W1["第一版不做 Web/API"]
        W2["GitHub README + 文档展示"]
        W3["未来可选 Dashboard<br/>展示信号、回测和日志"]
    end

    subgraph Notify["通知"]
        N1["第一版不做自动通知"]
        N2["docs/devlog/x-post-drafts.md<br/>开发日记草稿"]
        N3["未来可选 Telegram / Email<br/>需用户明确批准"]
    end

    subgraph Scheduler["定时任务"]
        S1["第一版不启动定时任务"]
        S2["手动运行 Playbook / Skill 查询"]
        S3["未来可选每日任务<br/>需用户明确批准"]
    end

    subgraph Future["未来改造点"]
        F1["从文档型升级到脚本型"]
        F2["增加模块化 Python CLI"]
        F3["增加本地信号数据库"]
        F4["增加 Web Dashboard"]
        F5["增加模拟盘日报"]
    end

    E1 --> E2
    E2 --> D1
    C1 --> P5
    C2 --> D2
    C2 --> D3
    C2 --> D4
    C2 --> D5
    C2 --> D6
    D2 --> P2
    D3 --> P3
    D4 --> P4
    D5 --> P6
    D6 --> P6
    P1 --> P2
    P2 --> P5
    P3 --> P5
    P4 --> P5
    P5 --> P6
    P6 --> P7
    P7 --> D1
    D1 --> DB2
    DB2 --> W2
    W2 --> N2
    DB2 --> Future
    W3 --> Future
    N3 --> Future
    S3 --> Future
```

### 7.1 架构拆分说明

| 层级 | 第一版职责 | 当前状态 | 后续改造边界 |
| --- | --- | --- | --- |
| 入口 | 用 README 和 Playbook Prompt 作为人工入口 | 文档化 | 如需 CLI，先写实施计划 |
| 配置 | 用策略文档和 skill 文档记录可调口径 | 文档化 | 不写真实密钥，不写实盘配置 |
| 数据源 | 优先使用 Bitget Playbook 与 Agent Hub 官方 skills | 外部工具优先 | 不自建新闻爬虫 |
| 数据库 | 第一版不建库，只记录回测结果 | 文档化 | 可后置 SQLite / CSV |
| 核心流程 | 日线级信号收集、风控过滤、打分、五档观点 | 文档化 | 先模拟/回测，不接实盘 |
| Web/API | 第一版用 GitHub 文档展示 | 不实现服务 | Dashboard 后置 |
| 通知 | 第一版只准备开发日记草稿 | 不自动发送 | Telegram/Email 需明确批准 |
| 定时任务 | 第一版手动触发 | 不启动后台任务 | 每日自动任务需明确批准 |
| 未来改造点 | 记录脚本化和产品化方向 | 仅规划 | 每一步都需独立需求确认 |

## 8. Bitget 工具使用要求

### 8.1 Bitget Playbook

优先用于：

1. 根据自然语言策略哲思生成策略。
2. 上传策略。
3. 基于历史数据回测。
4. 发布策略。
5. 输出 PnL、最大回撤、夏普比率等指标。

使用前置条件：

1. 用户用报名 Bitget UID 创建子账户。
2. 用户在官方 Telegram 联系管理员获取 Playbook API Key。
3. Playbook API Key 只在本机临时输入或安全环境变量中使用，不写入项目文件。

### 8.2 Bitget Agent Hub Skills

优先使用以下官方 skills，不自建同类数据源：

| Skill | 本项目用途 | 第一版优先级 |
| --- | --- | --- |
| `news-briefing` | 聚合 AI 科技股、半导体、云计算、财报、监管相关新闻，并总结利好/利空 | 高 |
| `macro-analyst` | 判断美联储、利率、DXY、VIX、纳指环境是否支持 risk-on | 高 |
| `technical-analysis` | 用趋势、均线、RSI、MACD 等指标确认价格方向 | 高 |
| `sentiment-analyst` | 辅助判断市场拥挤度和风险偏好 | 中 |
| `market-intel` | 辅助查看机构、ETF 或资金叙事 | 中 |

第一版不强制把所有 skills 都接成自动流程，但需求文档和策略说明必须表达清楚：若需要新闻、宏观、技术、情绪和市场情报，优先使用 Bitget 官方 skills。

## 9. 输入与输出

### 输入

| 输入项 | 来源 | 格式 | 是否必填 | 说明 |
| --- | --- | --- | --- | --- |
| 策略哲思 | 用户 | 自然语言 | 是 | 描述稳健型 AI 科技股策略 |
| 标的范围 | 用户 / Playbook 支持范围 | 股票代码或代币化资产名称 | 是 | 初始偏向 NVDA、MSFT、GOOGL、AMD、META |
| Playbook API Key | Bitget 管理员 | 密钥字符串 | 执行阶段必填 | 只临时使用，不写入仓库 |
| 新闻信号 | Bitget Agent Hub `news-briefing` | 摘要 / 关键词结果 | 可选但优先 | 用于判断 AI 科技股新闻利好/利空 |
| 宏观信号 | Bitget Agent Hub `macro-analyst` | 分析结论 | 可选但优先 | 用于判断 risk-on / risk-off |
| 技术信号 | Bitget Agent Hub `technical-analysis` | 指标结果 | 可选但优先 | 用于趋势确认 |

### 输出

| 输出项 | 去向 | 格式 | 成功标准 |
| --- | --- | --- | --- |
| 需求文档 | `docs/requirements/` | Markdown | 覆盖目标、非目标、工具、验收和安全边界 |
| Playbook 策略 | Bitget Playbook | 平台记录 / 链接 | 能创建、回测并获得指标 |
| 回测指标 | 终端 / 文档 / 截图 | 表格或截图 | 包含至少 PnL、最大回撤、夏普比率或 Playbook 返回的等价指标 |
| 项目说明 | 提交表单 / README | 200 字以内 | 说明解决的问题、策略闭环和 Bitget 工具使用 |
| 开发日记 | X/Twitter | 公开帖子链接 | 带 `#BitgetHackathon` 和 `@Bitget_AI`，提交时可粘贴链接 |
| GitHub 仓库 | GitHub | 仓库链接 | 不含真实密钥，可公开访问 |

## 10. 约束条件

### 10.1 目录与文件约束

- 允许修改：
  - `AGENTS.md`
  - `README.md`
  - `.gitignore`
  - `docs/requirements/`
  - `docs/ai-sessions/`
- 禁止修改：
  - 不存在明确需求的业务代码和运行配置
  - 任何真实密钥文件
  - 任何会触发真实交易或后台长跑任务的脚本
- 新增需求文档必须放在：`docs/requirements/`

### 10.2 技术约束

- 技术栈：第一版优先使用 Bitget Playbook 和 Bitget Agent Hub，暂不限定自写代码语言。
- 运行环境：用户本机 + Bitget Playbook 平台。
- 性能要求：无低延迟要求；不做高频交易。
- 展示要求：提交材料必须真实、可核查、可公开展示。

### 10.3 安全与敏感信息约束

- 是否涉及密钥、token、资金、交易、账户：是。
- 所有密钥、API Key、secret、passphrase、私钥、真实账户敏感信息禁止进入文档和 Git 仓库。
- 任何真实交易、实盘部署、后台任务、自动下单都必须在用户明确确认后才允许进行。
- 回测和模拟记录必须标注为回测或模拟，不伪装成真实收益。

## 11. 稳健型策略口径

第一版策略采用稳健型，而不是激进型或复杂事件驱动型。

推荐自然语言策略描述：

> 该策略聚焦 AI 科技股和美股代币化资产，优先关注 NVDA、MSFT、GOOGL、AMD、META 等 AI 主线标的。策略结合 AI/科技新闻情绪、宏观 risk-on/risk-off 环境和技术趋势确认。只有当新闻叙事偏利好、宏观环境未明显转弱且价格趋势确认时才买入或加仓；当新闻利空、宏观转 risk-off 或趋势跌破关键均线时降低仓位或卖出；当信号冲突时优先观望，避免频繁交易和情绪化追涨。

## 12. 开发日记要求

开发日记不是正式日报，也不是必须写长文。它是公开展示参赛进展的帖子，建议发在 X/Twitter。

最低可行做法：

1. 发一条项目立项帖。
2. 发一条开发进展帖。
3. 发一条最终 showcase 帖。

每条帖子建议包含：

- `#BitgetHackathon`
- `@Bitget_AI`
- 项目方向
- 使用 Bitget Playbook / Agent Hub skills 的说明
- 截图、回测指标或链接，按进度选择添加

提交项目时，将这些公开帖子链接填入提交表单。

## 13. 验收标准

| 编号 | 验收项 | 验收方式 | 通过标准 |
| --- | --- | --- | --- |
| AC-1 | 项目已具备 Git 仓库基础 | 命令检查 | `git status --short` 能显示仓库状态 |
| AC-2 | 项目规则文件存在 | 文件检查 | `AGENTS.md` 存在，并写明 Bitget 优先和安全边界 |
| AC-3 | 需求文档存在 | 文件检查 | 当前文档存在于 `docs/requirements/` |
| AC-4 | 工具优先级清楚 | 人工检查 | 文档明确 Playbook 优先、Agent Hub skills 优先、不自建数据源 |
| AC-5 | 安全边界清楚 | 人工检查 | 文档明确禁止真实密钥入库、禁止未经确认实盘下单 |
| AC-6 | 策略口径清楚 | 人工检查 | 文档明确 AI 科技股、稳健型、新闻 + 宏观 + 技术确认 |
| AC-7 | 开发日记口径清楚 | 人工检查 | 文档说明发帖内容、标签、@ 对象和提交方式 |
| AC-8 | 文档无模板残留 | 命令检查 | 扫描需求文档、项目规则和 README，不出现未替换的模板字段或待填内容 |
| AC-9 | 敏感信息未写入 | 命令检查 | 扫描仓库，不发现真实密钥赋值、私钥文件或账户敏感数据 |
| AC-10 | 架构图覆盖指定层级 | 人工检查 | Mermaid 图包含入口、配置、数据源、数据库、核心流程、Web/API、通知、定时任务、未来改造点 |

## 14. 风险与回退

| 风险 | 影响 | 预防方式 | 回退方式 |
| --- | --- | --- | --- |
| Playbook API Key 暂未拿到 | 无法实际创建和回测策略 | 先完成需求文档、策略 prompt、GitHub 仓库和开发日记 | 等拿到 Key 后再执行 Playbook |
| Playbook 支持的美股标的范围不完全匹配 | 初始标的需要调整 | 需求中把标的写成“优先 NVDA 等，最终以 Playbook 支持范围为准” | 改用 Playbook 支持的相近 AI 科技资产 |
| 新闻源不是实时 | 不适合高频抢跑 | 策略定位为稳健中低频，不做毫秒级新闻交易 | 降级为日内或日线级新闻情绪策略 |
| 回测指标不好看 | 影响提交说服力 | 使用稳健策略并保留风险解释 | 调整策略哲思或改为更清晰的演示型回测 |
| 误提交敏感信息 | 账户与资金风险 | `.gitignore`、提交前搜索敏感关键词 | 立即删除本地文件、重写 Git 历史、轮换密钥 |

## 15. 待确认问题

> 无阻塞型待确认问题，可以进入实施计划。

非阻塞问题可在实施计划阶段继续确认：

1. 最终 Playbook 支持的美股代币化资产清单。
2. 是否需要录制 3 分钟以内演示视频。
3. GitHub 仓库是否公开，仓库名称用英文还是中文。

## 16. 实施计划入口

需求文档确认后，再使用 `superpowers:writing-plans` 生成实施计划。

实施计划至少要说明：

1. 准备修改哪些文件。
2. 每个文件为什么要改。
3. 如何安全使用 Playbook API Key。
4. 如何生成 Playbook 策略、回测和发布。
5. 如何整理开发日记、README 和提交材料。
6. 最小必要验证和残余风险。

## 17. 文档自检清单

- [x] 没有未处理的待填项或模板占位符。
- [x] 目标和非目标没有互相冲突。
- [x] 功能范围可以被实施计划直接引用。
- [x] 输入、输出和验收标准能对应起来。
- [x] 允许修改路径和禁止修改路径明确。
- [x] 涉及敏感信息时已写明安全约束。
- [x] 待确认问题不会和“可以进入实施计划”互相矛盾。
