from __future__ import annotations

from dataclasses import replace

from .events import NewsEvent, event_timestamp_ms
from .indicators import moving_average, rsi
from .models import Candle, DecisionRecord
from .strategy import generate_signal


COOLDOWN_MS = 12 * 60 * 60 * 1000
EVENT_WINDOW_MS = 24 * 60 * 60 * 1000
DAILY_EVENT_WINDOW_MS = 72 * 60 * 60 * 1000
DAILY_CANDLE_MIN_GAP_MS = 20 * 60 * 60 * 1000
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
    position_high_price: float | None = None,
    cooldown_ms: int = COOLDOWN_MS,
    decision_mode: str = "conservative",
) -> DecisionRecord:
    if len(candles) < 3:
        raise ValueError("at least three candles are required")

    latest = candles[-1]
    signal = generate_signal(symbol, candles, macro_mode="neutral", news_bias="neutral")
    matched_events = _events_inside_window(symbol, latest.timestamp_ms, events, candles)
    event = matched_events[0] if matched_events else None
    news_strength = _news_strength(event)
    news_direction = _news_direction(event)
    technical_confirmation, technical_reasons = _daily_technical_confirmation(candles, signal, news_direction)
    final_view = _final_view(news_strength, news_direction, technical_confirmation)
    wanted_action = _wanted_action(news_strength, news_direction, technical_confirmation, has_position, event, decision_mode)
    risk_exit_action, risk_exit_reason = _risk_exit_action(candles, has_position, position_high_price, technical_reasons)
    if risk_exit_action == "sell":
        wanted_action = "sell"
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
        risk_exit_reason=risk_exit_reason,
        decision_mode=decision_mode,
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
        technical_reasons=tuple(technical_reasons),
        event_id=event.event_id if event else "",
        news_title=event.title if event else "",
        news_source=event.source_name if event else "",
        news_source_type=event.source_type if event else "",
        news_published_at=event.published_at if event else "",
        news_url=event.url if event else "",
        news_sentiment=event.sentiment if event else "",
        news_source_action=_source_action(event),
        news_topic=event.topic if event else "unknown",
        news_time_horizon=event.time_horizon if event else "short_term",
        stock_relevance=event.stock_relevance if event else "direct",
    )


def attach_fill(decision: DecisionRecord, *, quantity: float, fee: float) -> DecisionRecord:
    return replace(decision, quantity=quantity, fee=fee)


def _events_inside_window(symbol: str, timestamp_ms: int, events: list[NewsEvent], candles: list[Candle] | None = None) -> list[NewsEvent]:
    normalized = symbol.upper()
    window_ms = _event_window_ms(candles)
    forward_window_ms = _daily_forward_window_ms(candles)
    matched = [
        event
        for event in events
        if event.symbol.upper() == normalized and timestamp_ms - window_ms <= event_timestamp_ms(event) <= timestamp_ms + forward_window_ms
    ]
    matched.sort(key=lambda event: (_event_rank(event), event_timestamp_ms(event)), reverse=True)
    return matched


def _event_window_ms(candles: list[Candle] | None) -> int:
    if candles and len(candles) >= 2:
        latest_gap = candles[-1].timestamp_ms - candles[-2].timestamp_ms
        if latest_gap >= DAILY_CANDLE_MIN_GAP_MS:
            return DAILY_EVENT_WINDOW_MS
    return EVENT_WINDOW_MS


def _daily_forward_window_ms(candles: list[Candle] | None) -> int:
    if candles and len(candles) >= 2:
        latest_gap = candles[-1].timestamp_ms - candles[-2].timestamp_ms
        if latest_gap >= DAILY_CANDLE_MIN_GAP_MS:
            return 24 * 60 * 60 * 1000
    return 0


def _event_rank(event: NewsEvent) -> int:
    strength = _news_strength(event)
    return {"强利好": 5, "强利空": 5, "利好": 3, "利空": 3, "中性": 1}.get(strength, 0)


def _news_strength(event: NewsEvent | None) -> str:
    if event is None:
        return "无新闻"
    if event.strength == "strong" and event.sentiment == "bullish":
        return "强利好"
    if event.strength == "strong" and event.sentiment == "bearish":
        return "强利空"
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


def _daily_technical_confirmation(
    candles: list[Candle],
    signal,
    news_direction: str,
) -> tuple[str, list[str]]:
    if len(candles) < 50:
        return _technical_confirmation(signal.action, news_direction), list(signal.reasons)

    closes = [candle.close for candle in candles]
    ma20 = moving_average(closes, 20)[-1]
    ma50_values = moving_average(closes, 50)
    ma50 = ma50_values[-1]
    ma50_previous = next((value for value in reversed(ma50_values[:-1]) if value is not None), None)
    recent_rsi = rsi(closes, 14)
    latest_close = closes[-1]
    reasons: list[str] = []

    if ma20 is not None and ma50 is not None and ma20 > ma50:
        reasons.append("ma20_above_ma50")
    else:
        reasons.append("ma20_below_ma50")
    if ma50 is not None and latest_close > ma50:
        reasons.append("price_above_ma50")
    else:
        reasons.append("price_below_ma50")
    if ma50 is not None and ma50_previous is not None and ma50 > ma50_previous:
        reasons.append("ma50_slope_up")
    else:
        reasons.append("ma50_slope_flat_or_down")
    if recent_rsi >= 75:
        reasons.append("rsi_overheated")
    else:
        reasons.append("rsi_not_overheated")

    bullish_confirmed = (
        news_direction == "看多"
        and ma20 is not None
        and ma50 is not None
        and latest_close > ma50
        and (ma20 > ma50 or (ma50_previous is not None and ma50 > ma50_previous))
        and recent_rsi < 75
    )
    bearish_confirmed = (
        news_direction == "看空"
        and ma50 is not None
        and latest_close < ma50
    )
    if bullish_confirmed or bearish_confirmed:
        return "已确认", reasons
    return "未确认", reasons


def _wanted_action(
    news_strength: str,
    news_direction: str,
    technical_confirmation: str,
    has_position: bool,
    event: NewsEvent | None,
    decision_mode: str = "conservative",
) -> str:
    if decision_mode == "aggressive_news":
        return _aggressive_news_wanted_action(news_strength, news_direction, technical_confirmation, has_position, event)
    if (
        news_strength == "强利好"
        and news_direction == "看多"
        and technical_confirmation == "已确认"
        and not has_position
        and (event is None or event.stock_relevance == "direct")
        and (event is None or event.confidence >= 0.7)
    ):
        return "buy"
    if news_strength == "强利空" and news_direction == "看空" and technical_confirmation == "已确认" and has_position:
        return "sell"
    return "observe"


def _aggressive_news_wanted_action(
    news_strength: str,
    news_direction: str,
    technical_confirmation: str,
    has_position: bool,
    event: NewsEvent | None,
) -> str:
    if event is None:
        return "observe"
    if has_position and news_direction == "看空" and news_strength in {"强利空", "利空"}:
        return "sell"
    if has_position:
        return "observe"
    if event.stock_relevance != "direct":
        return "observe"
    if news_direction == "看多" and news_strength == "强利好":
        return "buy"
    if news_direction == "看多" and news_strength == "利好" and technical_confirmation == "已确认":
        return "buy"
    return "observe"


def _risk_exit_action(
    candles: list[Candle],
    has_position: bool,
    position_high_price: float | None,
    technical_reasons: list[str],
) -> tuple[str, str]:
    if not has_position or len(candles) < 50:
        return "observe", ""
    latest_close = candles[-1].close
    if "price_below_ma50" in technical_reasons:
        return "sell", "price_below_ma50"
    if position_high_price and position_high_price > 0 and latest_close <= position_high_price * 0.88:
        technical_reasons.append("trailing_drawdown_12pct")
        return "sell", "trailing_drawdown_12pct"
    return "observe", ""


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
    risk_exit_reason: str = "",
    decision_mode: str = "conservative",
) -> str:
    if cooldown_state == "冷却中" and wanted_action in {"buy", "sell"}:
        return "信号满足交易方向，但仍处于 12 小时冷却期，保守型策略选择观望。"
    if action == "buy":
        if decision_mode == "aggressive_news":
            return "激进新闻模式：新闻方向看多且技术面可接受，所以回测触发买入。"
        return "强利好新闻成立，并且技术面确认，所以回测触发买入。"
    if action == "sell" and risk_exit_reason == "price_below_ma50":
        return "持仓后价格跌破 MA50，按卖出规则 A 触发卖出。"
    if action == "sell" and risk_exit_reason == "trailing_drawdown_12pct":
        return "持仓后从最高价回撤达到 12%，按卖出规则 A 触发卖出。"
    if action == "sell":
        if decision_mode == "aggressive_news":
            return "激进新闻模式：持仓后出现看空新闻或风险退出条件，所以回测触发卖出。"
        return "强利空新闻成立，并且技术面转弱，所以回测触发卖出。"
    if technical_confirmation == "未确认" and news_strength == "强利好":
        return "强利好新闻成立，但技术面未确认或 RSI 过热，保守型策略避免追高。"
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
