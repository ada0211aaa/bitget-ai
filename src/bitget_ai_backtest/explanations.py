from __future__ import annotations

import json
from pathlib import Path

from .events import NewsEvent, event_timestamp_ms
from .models import BacktestResult, Trade


NEWS_WEIGHTS = {"bullish": 1, "neutral": 0, "bearish": -1}


def explain_trades(
    results: list[BacktestResult],
    events: list[NewsEvent],
    *,
    window_hours: int = 24,
) -> list[dict]:
    explanations: list[dict] = []
    window_ms = window_hours * 60 * 60 * 1000
    for result in results:
        for trade in result.trades:
            matched = _match_events(trade, events, window_ms=window_ms)
            news_score = sum(NEWS_WEIGHTS.get(event.sentiment, 0) for event in matched)
            signal_reasons = list(trade.reasons or result.last_signal.reasons)
            explanations.append(
                {
                    "symbol": trade.symbol,
                    "timestamp_ms": trade.timestamp_ms,
                    "side": trade.side,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "fee": trade.fee,
                    "final_view": trade.reason,
                    "technical_reasons": signal_reasons,
                    "matched_events": [event.event_id for event in matched],
                    "matched_event_details": [
                        {
                            "event_id": event.event_id,
                            "published_at": event.published_at,
                            "title": event.title,
                            "source_name": event.source_name,
                            "source_type": event.source_type,
                            "url": event.url,
                            "sentiment": event.sentiment,
                            "confidence": event.confidence,
                            "reason": event.reason,
                        }
                        for event in matched
                    ],
                    "news_score": news_score,
                    "explanation": _build_explanation(trade, matched, news_score),
                }
            )
    return explanations


def write_trade_explanations(path: Path, explanations: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"trade_explanations": explanations}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_trade_explanations(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("trade_explanations", [])
    if not isinstance(rows, list):
        raise ValueError("trade explanations file must contain a trade_explanations list")
    return rows


def _match_events(trade: Trade, events: list[NewsEvent], *, window_ms: int) -> list[NewsEvent]:
    matched = []
    for event in events:
        if event.symbol.upper() != trade.symbol.upper():
            continue
        published_ms = event_timestamp_ms(event)
        if trade.timestamp_ms - window_ms <= published_ms <= trade.timestamp_ms:
            matched.append(event)
    matched.sort(key=event_timestamp_ms, reverse=True)
    return matched[:5]


def _build_explanation(trade: Trade, matched: list[NewsEvent], news_score: int) -> str:
    if matched:
        event_text = "; ".join(f"{event.title} ({event.sentiment})" for event in matched[:3])
        return (
            f"{trade.side} was triggered with view {trade.reason}. "
            f"Within the prior 24 hours, matched news score was {news_score}: {event_text}."
        )
    return (
        f"{trade.side} was triggered with view {trade.reason}. "
        "No matching news event was found in the prior 24 hours; this trade is explained by price and configured strategy signals."
    )
