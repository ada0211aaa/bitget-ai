import json
from pathlib import Path

from bitget_ai_backtest.web import build_dashboard_payload


def test_build_dashboard_payload_reads_reports_and_marks_backtest_only(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["NVDAUSDT", "AMDUSDT"],
  "granularity": "15m",
  "limit": 200,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"NVDAUSDT": "NVDA", "AMDUSDT": "AMD"}
}
""".strip(),
        encoding="utf-8",
    )
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "backtest-report.md").write_text(
        """
# Bitget AI Local Backtest Report

| Symbol | Final Equity | Total Return | Max Drawdown | Last View | Trades |
| --- | ---: | ---: | ---: | --- | ---: |
| NVDAUSDT | 10020.00 | 0.20% | -0.10% | cautiously_bullish | 1 |
| AMDUSDT | 10080.00 | 0.80% | -0.20% | neutral_observe | 1 |
""".strip(),
        encoding="utf-8",
    )
    (report_dir / "trades.csv").write_text(
        "timestamp_ms,symbol,side,price,quantity,fee,reason\n1780916400000,NVDAUSDT,buy,209.66,1,0,cautiously_bullish\n",
        encoding="utf-8",
    )
    (report_dir / "trade-explanations.json").write_text(
        json.dumps(
            {
                "trade_explanations": [
                    {
                        "symbol": "NVDAUSDT",
                        "timestamp_ms": 1780916400000,
                        "side": "buy",
                        "price": 209.66,
                        "quantity": 1,
                        "fee": 0,
                        "final_view": "cautiously_bullish",
                        "technical_reasons": [],
                        "matched_events": ["event-1"],
                        "news_score": 1,
                        "explanation": "Matched event",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    events = tmp_path / "events.json"
    events.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "event_id": "event-noise",
                        "symbol": "NVDAUSDT",
                        "published_at": "2026-06-08T09:00:00Z",
                        "title": "Bitcoin Could Be 50% Undervalued. Should You Buy It Right Now?",
                        "source_name": "Yahoo Finance RSS",
                        "source_type": "public_news_fallback",
                        "url": "https://example.com/bitcoin",
                        "sentiment": "neutral",
                        "confidence": 0.5,
                        "reason": "No bullish or bearish keyword matched",
                    },
                    {
                        "event_id": "event-1",
                        "symbol": "NVDAUSDT",
                        "published_at": "2026-06-08T10:00:00Z",
                        "title": "Nvidia raises guidance",
                        "source_name": "Bitget news-briefing",
                        "source_type": "bitget_news_briefing",
                        "url": "https://example.com/news",
                        "sentiment": "bullish",
                        "confidence": 0.7,
                        "reason": "Matched bullish keyword: raises guidance",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    candles = report_dir / "candles.json"
    candles.write_text(
        json.dumps(
            {
                "NVDAUSDT": [{"timestamp_ms": 1780916400000, "close": 209.66}],
                "AMDUSDT": [{"timestamp_ms": 1780916400000, "close": 511.06}],
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "coverage.json").write_text(
        json.dumps(
            {
                "symbols": {
                    "NVDAUSDT": {
                        "symbol": "NVDAUSDT",
                        "interval": "15m",
                        "source": "bitget_public",
                        "rows": 1,
                        "start_date": "2026-06-08",
                        "end_date": "2026-06-08",
                        "kline_coverage": "2026-06-08 -> 2026-06-08",
                        "news_coverage": "2026-06-08 -> 2026-06-08",
                        "effective_backtest_coverage": "2026-06-08 -> 2026-06-08",
                    },
                    "AMDUSDT": {
                        "symbol": "AMDUSDT",
                        "interval": "1d",
                        "source": "bitget_public",
                        "rows": 2,
                        "start_date": "2026-06-08",
                        "end_date": "2026-06-09",
                        "kline_coverage": "2026-06-08 -> 2026-06-09",
                        "news_coverage": "",
                        "effective_backtest_coverage": "2026-06-08 -> 2026-06-09",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "decision-records.json").write_text(
        json.dumps(
            {
                "decision_records": [
                    {
                        "decision_id": "NVDAUSDT-15m-20260608-buy-001",
                        "timestamp_ms": 1780916400000,
                        "symbol": "NVDAUSDT",
                        "action": "buy",
                        "price": 209.66,
                        "quantity": 1,
                        "fee": 0,
                        "news_strength": "强利好",
                        "news_direction": "看多",
                        "technical_confirmation": "已确认",
                        "cooldown_state": "可交易",
                        "decision_reason": "强利好新闻成立，并且技术面确认，所以回测触发买入。",
                        "final_view": "看多",
                        "technical_reasons": [],
                        "event_id": "event-1",
                        "news_title": "Nvidia raises guidance",
                        "news_source": "Bitget news-briefing",
                        "news_source_type": "bitget_news_briefing",
                        "news_published_at": "2026-06-08T10:00:00Z",
                        "news_url": "https://example.com/news",
                        "news_sentiment": "bullish",
                        "news_source_action": "查看原文",
                        "news_topic": "earnings_guidance",
                        "news_time_horizon": "medium_term",
                        "stock_relevance": "direct",
                    },
                    {
                        "decision_id": "AMDUSDT-15m-20260608-buy-001",
                        "timestamp_ms": 1780916400000,
                        "symbol": "AMDUSDT",
                        "action": "buy",
                        "price": 511.06,
                        "quantity": 1,
                        "fee": 0,
                        "news_strength": "强利好",
                        "news_direction": "看多",
                        "technical_confirmation": "已确认",
                        "cooldown_state": "可交易",
                        "decision_reason": "强利好新闻成立，并且技术面确认，所以回测触发买入。",
                        "final_view": "看多",
                        "technical_reasons": [],
                        "event_id": "amd-event-1",
                        "news_title": "AMD gets monster price target",
                        "news_source": "Yahoo Finance RSS",
                        "news_source_type": "public_news_fallback",
                        "news_published_at": "2026-06-08T10:00:00Z",
                        "news_url": "https://example.com/amd",
                        "news_sentiment": "bullish",
                        "news_source_action": "查看原文",
                    },
                    {
                        "decision_id": "NVDAUSDT-15m-20260608-sell-001",
                        "timestamp_ms": 1780917300000,
                        "symbol": "NVDAUSDT",
                        "action": "sell",
                        "price": 220.0,
                        "quantity": 1,
                        "fee": 0,
                        "news_strength": "强利空",
                        "news_direction": "看空",
                        "technical_confirmation": "已确认",
                        "cooldown_state": "可交易",
                        "decision_reason": "强利空新闻成立，并且技术面确认，所以回测触发卖出。",
                        "final_view": "看空",
                        "technical_reasons": ["take_profit"],
                        "event_id": "event-1",
                        "news_title": "Nvidia trims outlook",
                        "news_source": "Bitget news-briefing",
                        "news_source_type": "bitget_news_briefing",
                        "news_published_at": "2026-06-08T10:15:00Z",
                        "news_url": "https://example.com/news-sell",
                        "news_sentiment": "bearish",
                        "news_source_action": "查看原文",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "markers.json").write_text(
        json.dumps(
            {
                "markers": [
                    {
                        "decision_id": "NVDAUSDT-15m-20260608-buy-001",
                        "symbol": "NVDAUSDT",
                        "date": "2026-06-08",
                        "timestamp_ms": 1780916400000,
                        "action": "buy",
                        "label": "买入",
                        "price": 209.66,
                        "position": "belowBar",
                        "shape": "arrowUp",
                        "color": "#22c55e",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "technical-candidates.json").write_text(
        json.dumps(
            {
                "technical_candidates": [
                    {
                        "symbol": "NVDAUSDT",
                        "date": "2026-06-08",
                        "timestamp_ms": 1780916400000,
                        "price": 209.66,
                        "candidate_type": "buy_watch",
                        "technical_reasons": ["price_above_ma50"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "news-coverage.json").write_text(
        json.dumps(
            {
                "symbols": {
                    "NVDAUSDT": {
                        "symbol": "NVDAUSDT",
                        "event_count": 2,
                        "start_date": "2026-06-01",
                        "end_date": "2026-06-08",
                        "coverage": "2026-06-01 -> 2026-06-08",
                        "fetched_at": "2026-06-17T09:00:00Z",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "candidate-markers.json").write_text(
        json.dumps(
            {
                "candidate_markers": [
                    {
                        "symbol": "NVDAUSDT",
                        "date": "2026-06-08",
                        "timestamp_ms": 1780916400000,
                        "action": "candidate",
                        "label": "观察",
                        "price": 209.66,
                        "position": "inBar",
                        "shape": "circle",
                        "color": "#38bdf8",
                        "candidate_type": "buy_watch",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = build_dashboard_payload(config, report_dir, playbook_report=tmp_path / "missing.md", events_path=events)

    assert payload["status"]["mode"] == "backtest-only"
    assert payload["status"]["safe_notice"] == "本页面只读取回测报告，不下单、不查账户、不展示密钥。"
    assert payload["config"]["symbols"] == ["NVDAUSDT", "AMDUSDT"]
    assert payload["config"]["price_source"] == "yahoo_chart_daily"
    assert payload["summary"][0]["symbol"] == "NVDAUSDT"
    assert payload["trades"][0]["side"] == "buy"
    assert payload["trade_explanations"][0]["matched_events"] == ["event-1"]
    assert [event["event_id"] for event in payload["events"]] == ["event-1"]
    assert payload["events"][0]["source_type"] == "bitget_news_briefing"
    assert payload["price_series"]["NVDAUSDT"][0]["close"] == 209.66
    assert payload["chart_markers"]["NVDAUSDT"][0]["decision_id"] == "NVDAUSDT-15m-20260608-buy-001"
    assert payload["candidate_markers"]["NVDAUSDT"][0]["action"] == "candidate"
    assert payload["coverage"]["symbols"]["AMDUSDT"]["interval"] == "1d"
    assert payload["technical_candidates"][0]["candidate_type"] == "buy_watch"
    assert payload["news_coverage"]["symbols"]["NVDAUSDT"]["event_count"] == 2
    assert payload["playbook"]["available"] is False
    assert payload["submission_checklist"][0] == "GitHub 仓库链接"
    assert payload["focus_symbol"] == {"symbol": "NVDAUSDT", "name": "英伟达"}
    assert [row["symbol"] for row in payload["symbol_overview"]] == ["NVDAUSDT", "AMDUSDT"]
    amd_overview = next(row for row in payload["symbol_overview"] if row["symbol"] == "AMDUSDT")
    assert amd_overview["latest_price"] == "511.06"
    assert amd_overview["total_return"] == "0.80%"
    assert amd_overview["latest_action"] == "买入"
    assert amd_overview["latest_news_strength"] == "强利好"
    assert amd_overview["latest_technical_confirmation"] == "已确认"
    assert amd_overview["kline_coverage"] == "2026-06-08 -> 2026-06-09"
    assert amd_overview["news_coverage"] == ""
    assert amd_overview["effective_backtest_coverage"] == "2026-06-08 -> 2026-06-09"
    assert {row["symbol"] for row in payload["decision_rows"]} == {"NVDAUSDT", "AMDUSDT"}
    assert len(payload["decision_rows"]) == 3

    decision = next(row for row in payload["decision_rows"] if row["symbol"] == "NVDAUSDT")
    assert decision["symbol"] == "NVDAUSDT"
    assert decision["decision_id"] == "NVDAUSDT-15m-20260608-buy-001"
    assert decision["symbol_name"] == "英伟达"
    assert decision["action"] == "买入"
    assert decision["price"] == "209.66"
    assert decision["quantity"] == "1.0000"
    assert decision["event_title"] == "Nvidia raises guidance"
    assert decision["news_source"] == "Bitget news-briefing"
    assert decision["news_published_at"] == "2026-06-08 10:00"
    assert decision["news_sentiment"] == "利好"
    assert decision["news_strength"] == "强利好"
    assert decision["news_direction"] == "看多"
    assert decision["news_topic"] == "earnings_guidance"
    assert decision["news_time_horizon"] == "medium_term"
    assert decision["stock_relevance"] == "direct"
    assert decision["technical_confirmation"] == "已确认"
    assert decision["cooldown_state"] == "可交易"
    assert decision["news_url"] == "https://example.com/news"
    assert decision["source_action"] == "查看原文"
    assert decision["technical_reason"] == "暂无"
    assert decision["final_view"] == "看多"
    assert "强利好新闻成立" in decision["decision_reason"]
    assert decision["backtest_result"] == "下一笔卖出价 220.00，单笔价格变化 4.93%"

    amd_decision = next(row for row in payload["decision_rows"] if row["symbol"] == "AMDUSDT")
    assert amd_decision["backtest_result"] == "待下一笔卖出或回测结算确认"
