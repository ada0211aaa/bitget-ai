const SIDE_LABELS = {
  buy: "买入",
  sell: "卖出"
};

const SENTIMENT_LABELS = {
  bullish: "利好",
  bearish: "利空",
  neutral: "中性"
};

const VIEW_LABELS = {
  bullish: "看多",
  cautiously_bullish: "谨慎看多",
  neutral_observe: "中性观察",
  cautiously_bearish: "谨慎看空",
  bearish: "看空"
};

const SOURCE_LABELS = {
  bitget_news_briefing: "Bitget news-briefing",
  bitget_macro_analyst: "Bitget macro-analyst",
  bitget_technical_analysis: "Bitget technical-analysis",
  bitget_sentiment_analyst: "Bitget sentiment-analyst",
  bitget_market_intel: "Bitget market-intel",
  public_news_fallback: "公开新闻降级源"
};

const TOPIC_LABELS = {
  earnings_guidance: "财报/指引",
  ai_demand: "AI需求",
  product: "产品/发布",
  regulation: "监管",
  macro: "宏观",
  unknown: "未分类"
};

const TIME_HORIZON_LABELS = {
  short_term: "短期",
  medium_term: "中期",
  long_term: "长期"
};

const RELEVANCE_LABELS = {
  direct: "直接相关",
  indirect: "间接相关",
  weak: "弱相关"
};

const REASON_LABELS = {
  trend_up: "价格趋势走强",
  trend_down: "价格趋势走弱",
  mean_reversion_buy: "均值回归买点",
  mean_reversion_sell: "均值回归卖点",
  stop_loss: "触发止损",
  take_profit: "触发止盈",
  cautiously_bullish: "谨慎看多信号",
  cautiously_bearish: "谨慎看空信号",
  neutral_observe: "中性观察"
};

let dashboardData = null;
let chartState = {
  chart: null,
  candleSeries: null,
  markerByTime: new Map()
};

async function loadDashboard() {
  const response = await fetch("./dashboard-data.json");
  const data = await response.json();
  dashboardData = data;

  document.getElementById("safe-notice").textContent = data.status.safe_notice;
  document.getElementById("symbol-count").textContent = data.config.symbols.length;
  document.getElementById("trade-count").textContent = data.trades.length;
  document.getElementById("explanation-count").textContent = data.decision_rows.length;

  renderConfig(data.config);
  renderMarketTable(data.symbol_overview || []);
  renderPlaybook(data.playbook);
  renderChecklist(data.submission_checklist);
  document.getElementById("back-to-market").addEventListener("click", () => {
    location.hash = "";
  });
  window.addEventListener("hashchange", routeDashboard);
  routeDashboard();
}

function renderFocusSymbol(focusSymbol) {
  const node = document.getElementById("focus-symbol");
  node.textContent = `${focusSymbol.symbol} / ${focusSymbol.name}`;
}

function renderConfig(config) {
  const container = document.getElementById("config");
  const values = [
    `原始股票池：${config.symbols.join(" / ")}`,
    `K线周期：${config.granularity}`,
    `K线数量：${config.limit}`,
    `初始资金：${formatMoney(config.initial_cash)}`,
    `单次仓位：${formatPercent(config.trade_fraction)}`,
    `手续费率：${formatPercent(config.fee_rate)}`,
    `宏观模式：${translateView(config.macro_mode)}`,
    `价格数据源：${translatePriceSource(config.price_source)}`,
    `决策模式：${translateDecisionMode(config.decision_mode)}`,
    `新闻降级参数：${translateSentiment(config.news_bias)}`
  ];
  container.innerHTML = `<div class="chips">${values.map((value) => `<span class="chip">${escapeHtml(value)}</span>`).join("")}</div>`;
}

function routeDashboard() {
  if (!dashboardData) return;
  const symbol = getSelectedSymbolFromHash();
  if (symbol) {
    renderDetailView(dashboardData, symbol);
    return;
  }
  renderMarketView(dashboardData);
}

function getSelectedSymbolFromHash() {
  const match = location.hash.match(/^#\/symbol\/([^/]+)$/);
  return match ? decodeURIComponent(match[1]).toUpperCase() : "";
}

function renderMarketView(data) {
  document.getElementById("market-view").hidden = false;
  document.getElementById("detail-view").hidden = true;
  document.getElementById("trade-count").textContent = data.trades.length;
  document.getElementById("explanation-count").textContent = data.decision_rows.length;
}

function renderDetailView(data, symbol) {
  const overview = (data.symbol_overview || []).find((row) => row.symbol === symbol);
  const tradeRows = filterBySymbol(data.trades, symbol);
  const decisionRows = filterBySymbol(data.decision_rows, symbol);
  const summaryRows = filterBySymbol(data.summary, symbol);

  document.getElementById("market-view").hidden = true;
  document.getElementById("detail-view").hidden = false;
  document.getElementById("trade-count").textContent = filterBySymbol(data.trades, symbol).length;
  document.getElementById("explanation-count").textContent = decisionRows.length;

  if (!overview) {
    document.getElementById("detail-title").textContent = `${symbol} 未找到回测数据`;
    renderFocusSymbol({ symbol, name: "未配置" });
    renderCoverage({});
    renderSummary([]);
    renderKlineChart(data.price_series, data.chart_markers, symbol);
    renderNewsCoverage(data.news_coverage, symbol);
    renderTechnicalCandidates([]);
    renderExplanations([]);
    renderDecisionTable([]);
    renderEvents([]);
    return;
  }

  renderFocusSymbol({ symbol: overview.symbol, name: overview.symbol_name });
  document.getElementById("detail-title").textContent = `${overview.symbol} / ${overview.symbol_name} 运行详情`;
  document.getElementById("price-chart-title").textContent = `${overview.symbol} 价格走势`;
  renderCoverage(overview);
  renderSummary(summaryRows);
  renderKlineChart(data.price_series, data.chart_markers, symbol);
  renderNewsCoverage(data.news_coverage, symbol);
  renderTechnicalCandidates(filterBySymbol(data.technical_candidates, symbol));
  renderExplanations(filterBySymbol(data.trade_explanations, symbol));
  renderDecisionTable(decisionRows);
  renderEvents(filterBySymbol(data.events, symbol));

  if (!tradeRows.length && !decisionRows.length) {
    document.getElementById("explanation-count").textContent = 0;
  }
}

function renderMarketTable(rows) {
  const body = document.querySelector("#market-table tbody");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="10" class="empty-cell">暂无行情列表。请先运行回测生成 dashboard-data.json。</td></tr>`;
    return;
  }
  body.innerHTML = rows.map((row) => `
    <tr class="clickable-row" data-symbol="${escapeHtml(row.symbol)}" tabindex="0">
      <td><span class="symbol">${escapeHtml(row.symbol)}<br>${escapeHtml(row.symbol_name)}</span></td>
      <td>${escapeHtml(row.latest_price)}</td>
      <td>${formatSignedCell(row.total_return)}</td>
      <td>${formatSignedCell(row.max_drawdown)}</td>
      <td><span class="view-pill">${escapeHtml(translateView(row.last_view))}</span></td>
      <td>${escapeHtml(row.trade_count)}</td>
      <td>${renderActionPill(row.latest_action)}</td>
      <td>${renderStrengthPill(row.latest_news_strength)}</td>
      <td>${renderConfirmationPill(row.latest_technical_confirmation)}</td>
      <td><button class="detail-link" type="button">查看</button></td>
    </tr>
  `).join("");
  rows.forEach((row) => {
    const rowNode = body.querySelector(`tr[data-symbol="${row.symbol}"]`);
    if (!rowNode) return;
    rowNode.addEventListener("click", () => openSymbolDetail(row));
    rowNode.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openSymbolDetail(row);
      }
    });
  });
}

function openSymbolDetail(row) {
  location.hash = `#/symbol/${row.symbol}`;
}

function renderDecisionTable(rows) {
  const body = document.querySelector("#decision-table tbody");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="21" class="empty-cell">暂无交易决策明细。请先运行回测并生成交易解释。</td></tr>`;
    return;
  }
  body.innerHTML = rows.map((row, index) => `
    <tr data-decision-id="${escapeHtml(row.decision_id || "")}">
      <td>${escapeHtml(index + 1)}</td>
      <td>${escapeHtml(row.trade_time)}</td>
      <td><span class="symbol">${escapeHtml(row.symbol)}<br>${escapeHtml(row.symbol_name)}</span></td>
      <td>${renderActionPill(row.action)}</td>
      <td>${renderStrengthPill(row.news_strength)}</td>
      <td>${escapeHtml(row.news_direction)}</td>
      <td>${escapeHtml(translateTopic(row.news_topic))}</td>
      <td>${escapeHtml(translateTimeHorizon(row.news_time_horizon))}</td>
      <td>${escapeHtml(translateRelevance(row.stock_relevance))}</td>
      <td>${renderConfirmationPill(row.technical_confirmation)}</td>
      <td>${renderCooldownPill(row.cooldown_state)}</td>
      <td>${escapeHtml(row.price)}</td>
      <td>${escapeHtml(row.quantity)}</td>
      <td class="event-title-cell">${escapeHtml(row.event_title || "未匹配到 24 小时内新闻事件，主要由技术信号触发")}</td>
      <td>${escapeHtml(row.news_source)}</td>
      <td>${escapeHtml(row.news_published_at)}</td>
      <td>${renderSourceAction(row)}</td>
      <td>${escapeHtml(row.technical_reason)}</td>
      <td><span class="view-pill">${escapeHtml(row.final_view)}</span></td>
      <td class="reason-cell">${escapeHtml(row.decision_reason)}</td>
      <td class="result-cell">${escapeHtml(row.backtest_result)}</td>
    </tr>
  `).join("");
}

function renderSummary(rows) {
  const body = document.querySelector("#summary-table tbody");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="6" class="empty-cell">暂无回测汇总，请先运行回测生成报告。</td></tr>`;
    return;
  }
  body.innerHTML = rows.map((row) => `
    <tr>
      <td><span class="symbol">${escapeHtml(row.symbol)}</span></td>
      <td>${escapeHtml(row.final_equity)}</td>
      <td>${formatSignedCell(row.total_return)}</td>
      <td>${formatSignedCell(row.max_drawdown)}</td>
      <td><span class="view-pill">${escapeHtml(translateView(row.last_view))}</span></td>
      <td>${escapeHtml(row.trades)}</td>
    </tr>
  `).join("");
}

function renderCoverage(overview) {
  const container = document.getElementById("coverage-grid");
  const values = [
    ["K线覆盖", overview.kline_coverage || "暂无"],
    ["新闻覆盖", overview.news_coverage || "暂无"],
    ["有效回测覆盖", overview.effective_backtest_coverage || "暂无"],
    ["数据来源 / 行数", `${overview.data_source || "暂无"}${overview.coverage_rows ? ` · ${overview.coverage_rows} 行` : ""}`]
  ];
  container.innerHTML = values.map(([label, value]) => `
    <div class="coverage-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `).join("");
}

function renderNewsCoverage(newsCoverage, symbol) {
  const container = document.getElementById("news-coverage-grid");
  if (!container) return;
  const symbols = newsCoverage && newsCoverage.symbols ? newsCoverage.symbols : {};
  const row = symbols[symbol] || {};
  const values = [
    ["新闻条数", row.event_count || 0],
    ["新闻覆盖", row.coverage || "暂无"],
    ["最早新闻", row.start_date || "暂无"],
    ["最新新闻", row.end_date || "暂无"]
  ];
  container.innerHTML = values.map(([label, value]) => `
    <div class="coverage-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `).join("");
}

function renderTechnicalCandidates(rows) {
  const container = document.getElementById("technical-candidates");
  if (!container) return;
  const candidates = (rows || []).filter((row) => row.candidate_type && row.candidate_type !== "none");
  if (!candidates.length) {
    container.innerHTML = `<p class="empty-state">暂无技术候选观察点。可能是技术面没有触发，或尚未运行新闻库回测。</p>`;
    return;
  }
  container.innerHTML = candidates.slice(-20).reverse().map((row) => `
    <article class="event-card">
      <div class="card-heading">
        <h3>${escapeHtml(row.date)} · ${escapeHtml(translateCandidateType(row.candidate_type))}</h3>
        <span class="source-pill">${escapeHtml(formatFixed(row.price))}</span>
      </div>
      <p class="meta">技术原因：${escapeHtml(translateReasons(row.technical_reasons || []))}</p>
    </article>
  `).join("");
}

function renderExplanations(rows) {
  const container = document.getElementById("explanations");
  if (!rows.length) {
    container.innerHTML = `<p class="empty-state">暂无交易解释。请先用事件文件运行 backtest。</p>`;
    return;
  }
  container.innerHTML = rows.slice(0, 24).map((row) => {
    const events = row.matched_event_details || [];
    const eventHtml = events.length
      ? `<ul class="event-links">${events.map((event) => `<li><strong>${escapeHtml(translateSentiment(event.sentiment))}</strong>${escapeHtml(event.title)} <span class="meta">(${escapeHtml(translateSource(event.source_type))})</span></li>`).join("")}</ul>`
      : `<p class="meta">触发前 24 小时内没有匹配到新闻事件，主要按价格和策略信号解释。</p>`;
    return `
      <article class="trade-card">
        <div class="card-heading">
          <h3>${escapeHtml(row.symbol)} · ${escapeHtml(translateSide(row.side))} @ ${escapeHtml(String(row.price))}</h3>
          <span class="view-pill">${escapeHtml(translateView(row.final_view))}</span>
        </div>
        <p>${escapeHtml(buildChineseExplanation(row, events))}</p>
        <p class="meta">新闻分：${escapeHtml(String(row.news_score))} · 技术原因：${escapeHtml(translateReasons(row.technical_reasons || []))}</p>
        ${eventHtml}
      </article>
    `;
  }).join("");
}

function renderEvents(events) {
  const container = document.getElementById("events");
  if (!events.length) {
    container.innerHTML = `<p class="empty-state">暂无事件文件。请先运行 fetch-events 拉取真实新闻和信号记录。</p>`;
    return;
  }
  container.innerHTML = events.slice(0, 30).map((event) => `
    <article class="event-card" data-sentiment="${escapeHtml(event.sentiment)}">
      <div class="card-heading">
        <h3>${escapeHtml(event.symbol)} · ${escapeHtml(translateSentiment(event.sentiment))}事件</h3>
        <span class="source-pill">${escapeHtml(translateSource(event.source_type))}</span>
      </div>
      <p>${escapeHtml(event.title)}</p>
      <p class="meta">${escapeHtml(formatDateTime(event.published_at))} · ${escapeHtml(event.source_name)}</p>
      <p class="meta">主题：${escapeHtml(translateTopic(event.topic))} · 周期：${escapeHtml(translateTimeHorizon(event.time_horizon))} · 相关性：${escapeHtml(translateRelevance(event.stock_relevance))}</p>
      <p class="meta">${escapeHtml(event.reason)}</p>
    </article>
  `).join("");
}

function renderKlineChart(priceSeries, chartMarkers, symbol) {
  const container = document.getElementById("kline-chart");
  const hover = document.getElementById("kline-hover");
  const rows = (priceSeries && priceSeries[symbol]) || [];
  const markers = (chartMarkers && chartMarkers[symbol]) || [];
  destroyKlineChart();
  container.innerHTML = "";
  hover.textContent = "";

  if (!rows.length) {
    container.innerHTML = `<p class="empty-state">暂无价格快照。请先运行 backtest 生成 candles.json。</p>`;
    return;
  }
  if (!window.LightweightCharts) {
    container.innerHTML = `<p class="empty-state">图表库未加载，请检查本地静态资源。</p>`;
    return;
  }

  const chart = LightweightCharts.createChart(container, {
    height: 420,
    layout: {
      background: { type: "solid", color: "transparent" },
      textColor: "#dbe7f3"
    },
    grid: {
      vertLines: { color: "rgba(159, 176, 196, 0.16)" },
      horzLines: { color: "rgba(159, 176, 196, 0.16)" }
    },
    rightPriceScale: {
      borderColor: "rgba(159, 176, 196, 0.22)"
    },
    timeScale: {
      borderColor: "rgba(159, 176, 196, 0.22)",
      timeVisible: true,
      secondsVisible: false
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal
    },
    handleScroll: true,
    handleScale: true
  });

  const candleSeries = addCandlestickSeries(chart);
  const candleData = rows
    .map((row) => ({
      time: row.date || dateFromTimestamp(row.timestamp_ms),
      open: Number(row.open),
      high: Number(row.high),
      low: Number(row.low),
      close: Number(row.close)
    }))
    .filter((row) => Number.isFinite(row.open) && Number.isFinite(row.high) && Number.isFinite(row.low) && Number.isFinite(row.close));
  candleSeries.setData(candleData);

  const markerData = markers.map((marker) => ({
    id: marker.decision_id || `${marker.symbol || symbol}-${marker.date || marker.timestamp_ms}-${marker.action || "marker"}`,
    time: marker.date || dateFromTimestamp(marker.timestamp_ms),
    position: marker.position,
    color: marker.color,
    shape: marker.shape,
    text: marker.label,
    decision_id: marker.decision_id || ""
  }));
  setSeriesMarkers(candleSeries, markerData);
  chartState = {
    chart,
    candleSeries,
    markerByTime: new Map(markerData.map((marker) => [String(marker.time), marker]))
  };

  chart.subscribeClick((param) => {
    const hoveredId = String(param.hoveredObjectId || "");
    if (hoveredId) {
      scrollToDecisionRow(hoveredId);
      return;
    }
    const marker = chartState.markerByTime.get(String(param.time || ""));
    if (marker && marker.decision_id) {
      scrollToDecisionRow(marker.decision_id);
    }
  });
  chart.subscribeCrosshairMove((param) => {
    const series = param.seriesData.get(candleSeries);
    if (!series) return;
    hover.textContent = `${symbol} ${series.time} 开 ${formatFixed(series.open)} 高 ${formatFixed(series.high)} 低 ${formatFixed(series.low)} 收 ${formatFixed(series.close)}`;
  });
  chart.timeScale().fitContent();
}

function addCandlestickSeries(chart) {
  const options = {
    upColor: "#22c55e",
    downColor: "#ef4444",
    borderUpColor: "#22c55e",
    borderDownColor: "#ef4444",
    wickUpColor: "#22c55e",
    wickDownColor: "#ef4444"
  };
  if (typeof chart.addCandlestickSeries === "function") {
    return chart.addCandlestickSeries(options);
  }
  return chart.addSeries(LightweightCharts.CandlestickSeries, options);
}

function setSeriesMarkers(series, markers) {
  if (typeof series.setMarkers === "function") {
    series.setMarkers(markers);
    return;
  }
  if (LightweightCharts.createSeriesMarkers) {
    LightweightCharts.createSeriesMarkers(series, markers);
  }
}

function destroyKlineChart() {
  if (chartState.chart) {
    chartState.chart.remove();
  }
  chartState = { chart: null, candleSeries: null, markerByTime: new Map() };
}

function dateFromTimestamp(timestampMs) {
  const date = new Date(Number(timestampMs));
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().slice(0, 10);
}

function formatFixed(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "--";
}

function scrollToDecisionRow(decisionId) {
  const row = document.querySelector(`[data-decision-id="${CSS.escape(decisionId)}"]`);
  if (!row) return;
  row.scrollIntoView({ behavior: "smooth", block: "center" });
  row.classList.add("highlighted-row");
  window.setTimeout(() => row.classList.remove("highlighted-row"), 2200);
}

function renderPlaybook(playbook) {
  document.getElementById("playbook").textContent = playbook.available ? playbook.text : "尚未找到 Playbook 报告。";
}

function renderChecklist(items) {
  document.getElementById("checklist").innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderActionPill(action) {
  const tone = action === "买入" ? "buy" : action === "卖出" ? "sell" : "observe";
  return `<span class="action-pill ${tone}">${escapeHtml(action)}</span>`;
}

function renderSentimentPill(sentiment) {
  const tone = sentiment === "利好" ? "positive" : sentiment === "利空" ? "negative" : "neutral";
  return `<span class="sentiment-pill ${tone}">${escapeHtml(sentiment)}</span>`;
}

function renderStrengthPill(strength) {
  const tone = strength === "强利好" || strength === "利好"
    ? "positive"
    : strength === "强利空" || strength === "利空"
      ? "negative"
      : "neutral";
  return `<span class="strength-pill ${tone}">${escapeHtml(strength || "未分级")}</span>`;
}

function renderConfirmationPill(value) {
  const tone = value === "已确认" ? "positive" : "neutral";
  return `<span class="confirmation-pill ${tone}">${escapeHtml(value || "未记录")}</span>`;
}

function renderCooldownPill(value) {
  const tone = value === "冷却中" ? "warning" : "neutral";
  return `<span class="cooldown-pill ${tone}">${escapeHtml(value || "未记录")}</span>`;
}

function renderSourceAction(row) {
  if (row.news_url) {
    return `<a class="source-link" href="${escapeHtml(row.news_url)}" target="_blank" rel="noopener noreferrer">查看原文</a>`;
  }
  if (row.source_action === "查看信号详情") {
    return `
      <details class="source-details">
        <summary>查看信号详情</summary>
        <p>${escapeHtml(row.event_title || "暂无标题")}</p>
        <p>${escapeHtml(row.news_source || "未知来源")}</p>
      </details>
    `;
  }
  return `<span class="meta">无新闻来源</span>`;
}

function filterBySymbol(rows, symbol) {
  return (rows || []).filter((row) => row.symbol === symbol);
}

function buildChineseExplanation(row, events) {
  const side = translateSide(row.side);
  const view = translateView(row.final_view);
  if (events.length) {
    return `${side}触发时，过去 24 小时内匹配到 ${events.length} 条事件，综合观点为“${view}”，用于解释这笔回测交易。`;
  }
  return `${side}触发时没有匹配到新闻事件，当前解释主要来自价格走势、技术原因和回测策略信号，综合观点为“${view}”。`;
}

function translateSide(value) {
  return SIDE_LABELS[value] || value || "未知";
}

function translateSentiment(value) {
  return SENTIMENT_LABELS[value] || value || "未知";
}

function translateView(value) {
  return VIEW_LABELS[value] || SENTIMENT_LABELS[value] || value || "未知";
}

function translateSource(value) {
  return SOURCE_LABELS[value] || value || "未知来源";
}

function translateTopic(value) {
  return TOPIC_LABELS[value] || value || "未分类";
}

function translateTimeHorizon(value) {
  return TIME_HORIZON_LABELS[value] || value || "短期";
}

function translateRelevance(value) {
  return RELEVANCE_LABELS[value] || value || "直接相关";
}

function translatePriceSource(value) {
  const labels = {
    bitget_public: "Bitget 公共合约K线",
    yahoo_chart_daily: "Yahoo 美股日线"
  };
  return labels[value] || value || "未知";
}

function translateDecisionMode(value) {
  const labels = {
    conservative: "保守模式",
    aggressive_news: "激进新闻模式"
  };
  return labels[value] || value || "未知";
}

function translateCandidateType(value) {
  const labels = {
    buy_watch: "买入观察",
    sell_watch: "卖出观察",
    none: "非候选"
  };
  return labels[value] || value || "未知";
}

function translateReasons(reasons) {
  if (!reasons.length) return "暂无";
  return reasons.map((reason) => REASON_LABELS[reason] || reason).join("、");
}

function formatMoney(value) {
  return Number(value).toLocaleString("zh-CN", {
    maximumFractionDigits: 2
  });
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return value;
  return `${(number * 100).toFixed(2)}%`;
}

function formatSignedCell(value) {
  const numeric = Number(String(value).replace("%", ""));
  const tone = Number.isFinite(numeric) && numeric >= 0 ? "positive" : "negative";
  return `<span class="${tone}">${escapeHtml(String(value))}</span>`;
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    hour12: false,
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  })[char]);
}

loadDashboard().catch((error) => {
  document.body.innerHTML = `<main><section class="band"><h1>页面加载失败</h1><p>${escapeHtml(String(error))}</p></section></main>`;
});
