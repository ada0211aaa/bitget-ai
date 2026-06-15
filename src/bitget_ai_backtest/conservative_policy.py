from __future__ import annotations

from dataclasses import replace

from .events import NewsEvent, event_timestamp_ms
from .models import Candle, DecisionRecord
from .strategy import generate_signal


COOLDOWN_MS = 12 * 60 * 60 * 1000
EVENT_WINDOW_MS = 24 * 60 * 60 * 1000
STRONG_BULLISH_KEYWORDS = (
    "raises guidance",
    "raised guidance",
    "beats estimates",
    "beat estimates",
    "ai demand",
    "record revenue",
    "strong demand",
    "major order",
    "upgrade",
    "price target",
)
STRONG_BEARISH_KEYWORDS = (
    "cuts guidance",
    "cut guidance",
    "misses estimates",
    "missed estimates",
    "export restriction",
    "downgrade",
    "weak demand",
    "antitrust",
    "probe",
)


def evaluate_conservative_decision(
    symbol: str,
    candles: list[Candle],
    events: list[NewsEvent],
    *,
    has_position: bool,
    last_action_timestamp_ms: int | None = None,
    last_action_side: str | None = None,
    cooldown_ms: int = COOLDOWN_MS,
) -> DecisionRecord:
    if len(candles) < 3:
        raise ValueError("at least three candles are required")

    latest = candles[-1]
    signal = generate_signal(symbol, candles, macro_mode="neutral", news_bias="neutral")
    matched_events = _events_inside_window(symbol, latest.timestamp_ms, events)
    event = matched_events[0] if matched_events else None
    news_strength = _news_strength(event)
    news_direction = _news_direction(event)
    technical_confirmation = _technical_confirmation(signal.action, news_direction)
    final_view = _final_view(news_strength, news_direction, technical_confirmation)
    wanted_action = _wanted_action(news_strength, news_direction, technical_confirmation, has_position)
    cooldown_state = _cooldown_state(latest.timestamp_ms, wanted_action, last_action_timestamp_ms, last_action_side, cooldown_ms)
    action = wanted_action if cooldown_state == "可交易" else "observe"
    if action == "buy" and has_position:
        action = "observe"
    if action == "sell" and not has_position:
        action = "observe"

    decision_reason = _decision_reason(
        action=action,
        wanted_action=wanted_action,
        news_strength=news_strength,
        news_direction=news_direction,
        technical_confirmation=technical_confirmation,
        cooldown_state=cooldown_state,
    )
    return DecisionRecord(
        timestamp_ms=latest.timestamp_ms,
        symbol=symbol,
        action=action,
        price=latest.close,
        news_strength=news_strength,
        news_direction=news_direction,
        technical_confirmation=technical_confirmation,
        cooldown_state=cooldown_state,
        decision_reason=decision_reason,
        final_view=final_view,
        technical_reasons=tuple(signal.reasons),
        event_id=event.event_id if event else "",
        news_title=event.title if event else "",
        news_source=event.source_name if event else "",
        news_source_type=event.source_type if event else "",
        news_published_at=event.published_at if event else "",
        news_url=event.url if event else "",
        news_sentiment=event.sentiment if event else "",
        news_source_action=_source_action(event),
    )


def attach_fill(decision: DecisionRecord, *, quantity: float, fee: float) -> DecisionRecord:
    return replace(decision, quantity=quantity, fee=fee)


def _events_inside_window(symbol: str, timestamp_ms: int, events: list[NewsEvent]) -> list[NewsEvent]:
    normalized = symbol.upper()
    matched = [
        event
        for event in events
        if event.symbol.upper() == normalized and timestamp_ms - EVENT_WINDOW_MS <= event_timestamp_ms(event) <= timestamp_ms
    ]
    matched.sort(key=lambda event: (_event_rank(event), event_timestamp_ms(event)), reverse=True)
    return matched


def _event_rank(event: NewsEvent) -> int:
    strength = _news_strength(event)
    return {"强利好": 5, "强利空": 5, "利好": 3, "利空": 3, "中性": 1}.get(strength, 0)


def _news_strength(event: NewsEvent | None) -> str:
    if event is None:
        return "无新闻"
    text = f"{event.title} {event.reason}".lower()
    if event.sentiment == "bullish":
        if event.confidence >= 0.7 and any(keyword in text for keyword in STRONG_BULLISH_KEYWORDS):
            return "强利好"
        return "利好"
    if event.sentiment == "bearish":
        if event.confidence >= 0.7 and any(keyword in text for keyword in STRONG_BEARISH_KEYWORDS):
            return "强利空"
        return "利空"
    return "中性"


def _news_direction(event: NewsEvent | None) -> str:
    if event is None:
        return "无方向"
    if event.sentiment == "bullish":
        return "看多"
    if event.sentiment == "bearish":
        return "看空"
    return "无方向"


def _technical_confirmation(signal_action: str, news_direction: str) -> str:
    if news_direction == "看多" and signal_action == "buy":
        return "已确认"
    if news_direction == "看空" and signal_action == "sell":
        return "已确认"
    return "未确认"


def _wanted_action(news_strength: str, news_direction: str, technical_confirmation: str, has_position: bool) -> str:
    if news_strength == "强利好" and news_direction == "看多" and technical_confirmation == "已确认" and not has_position:
        return "buy"
    if news_strength == "强利空" and news_direction == "看空" and technical_confirmation == "已确认" and has_position:
        return "sell"
    return "observe"


def _cooldown_state(
    timestamp_ms: int,
    wanted_action: str,
    last_action_timestamp_ms: int | None,
    last_action_side: str | None,
    cooldown_ms: int,
) -> str:
    if wanted_action not in {"buy", "sell"}:
        return "可交易"
    if last_action_timestamp_ms is None or last_action_side != wanted_action:
        return "可交易"
    if timestamp_ms - last_action_timestamp_ms < cooldown_ms:
        return "冷却中"
    return "可交易"


def _final_view(news_strength: str, news_direction: str, technical_confirmation: str) -> str:
    if news_direction == "看多" and news_strength == "强利好" and technical_confirmation == "已确认":
        return "看多"
    if news_direction == "看空" and news_strength == "强利空" and technical_confirmation == "已确认":
        return "看空"
    return "中性观察"


def _decision_reason(
    *,
    action: str,
    wanted_action: str,
    news_strength: str,
    news_direction: str,
    technical_confirmation: str,
    cooldown_state: str,
) -> str:
    if cooldown_state == "冷却中" and wanted_action in {"buy", "sell"}:
        return "信号满足交易方向，但仍处于 12 小时冷却期，保守型策略选择观望。"
    if action == "buy":
        return "强利好新闻成立，并且技术面确认，所以回测触发买入。"
    if action == "sell":
        return "强利空新闻成立，并且技术面转弱，所以回测触发卖出。"
    if news_strength == "无新闻":
        return "技术面可能有信号，但没有足够新闻门票，保守型策略不买卖。"
    if news_strength in {"利好", "利空"}:
        return "新闻不错但不够强，尚未达到保守型交易门槛，先观察。"
    if news_strength in {"强利好", "强利空"} and technical_confirmation == "未确认":
        return f"{news_strength}新闻成立，但技术面未确认，保守型策略不追。"
    if news_direction == "无方向":
        return "新闻方向不清楚，保守型策略不交易。"
    return "新闻和技术面没有同时满足保守型交易条件，先观察。"


def _source_action(event: NewsEvent | None) -> str:
    if event is None:
        return "无新闻来源"
    return "查看原文" if event.url else "查看信号详情"
