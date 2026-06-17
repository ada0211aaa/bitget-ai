from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "src/bitget_ai_backtest/static"


def test_static_dashboard_shell_is_chinese() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert 'lang="zh-CN"' in html
    assert "<title>Bitget 多票回测行情台</title>" in html
    assert "Bitget 多票回测行情台" in html
    assert "项目状态" in html
    assert "回测行情列表" in html
    assert "回测总览" in html
    assert "交易决策明细表" in html
    assert "决策行数" in html
    assert 'id="market-view"' in html
    assert 'id="detail-view"' in html
    assert 'id="market-table"' in html
    assert 'id="detail-title"' in html
    assert 'id="coverage-grid"' in html
    assert "./vendor/lightweight-charts.standalone.production.js" in html
    assert 'id="kline-chart"' in html
    assert 'id="price-chart"' not in html
    assert "返回行情列表" in html
    assert 'id="decision-table"' in html
    assert "新闻强度" in html
    assert "新闻方向" in html
    assert "新闻主题" in html
    assert "影响周期" in html
    assert "股票相关性" in html
    assert "技术确认" in html
    assert "冷却状态" in html
    assert "查看原文" in html
    assert "为什么买 / 为什么卖" in html
    assert "新闻库覆盖" in html
    assert "技术候选观察点" in html
    assert "新闻与事件信号" in html


def test_static_dashboard_uses_dark_research_terminal_theme() -> None:
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

    assert "--bg-page" in css
    assert "#080a0f" in css
    assert "#f5f7f9" not in css
    assert "background: white" not in css


def test_static_dashboard_localizes_dynamic_labels() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "原始股票池：" in script
    assert "价格数据源：" in script
    assert "买入" in script
    assert "看多" in script
    assert "公开新闻降级源" in script
    assert "暂无交易解释" in script
    assert "renderDecisionTable" in script
    assert "renderSourceAction" in script
    assert "renderMarketTable" in script
    assert "renderDetailView" in script
    assert "renderCoverage" in script
    assert "renderNewsCoverage" in script
    assert "renderTechnicalCandidates" in script
    assert "renderKlineChart" in script
    assert "scrollToDecisionRow" in script
    assert "K线覆盖" in script
    assert "新闻覆盖" in script
    assert "有效回测覆盖" in script
    assert "getSelectedSymbolFromHash" in script
    assert 'window.addEventListener("hashchange"' in script
    assert "location.hash = `#/symbol/${row.symbol}`" in script
    assert "filterBySymbol(data.trades, symbol).length" in script
    assert 'target="_blank"' in script
    assert 'rel="noopener noreferrer"' in script
    assert "查看原文" in script
    assert "查看信号详情" in script
    assert "无新闻来源" in script
    assert "news_strength" in script
    assert "news_topic" in script
    assert "news_time_horizon" in script
    assert "stock_relevance" in script
    assert "data.chart_markers" in script
    assert "mergeChartMarkers" not in script
    assert "candidate_type" in script
    assert "technical_confirmation" in script
    assert "cooldown_state" in script
    assert "交易决策明细" in script
    assert "未匹配到 24 小时内新闻事件" in script
    assert "const summaryRows = filterBySymbol(data.summary, symbol)" in script
    assert "No trade explanations" not in script


def test_static_dashboard_styles_decision_table() -> None:
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

    assert ".decision-table" in css
    assert ".market-table" in css
    assert ".reason-cell" in css
    assert ".action-pill" in css
    assert ".source-link" in css
    assert ".back-button" in css
    assert ".clickable-row" in css
    assert ".coverage-grid" in css
    assert ".coverage-card" in css
    assert ".kline-chart" in css
    assert ".highlighted-row" in css
    assert ".strength-pill" in css
    assert ".confirmation-pill" in css
    assert ".cooldown-pill" in css
