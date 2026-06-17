from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float


@dataclass(frozen=True)
class StrategySignal:
    symbol: str
    timestamp_ms: int
    score: int
    view: str
    action: str
    close: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Trade:
    timestamp_ms: int
    symbol: str
    side: str
    price: float
    quantity: float
    fee: float
    reason: str
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class DecisionRecord:
    timestamp_ms: int
    symbol: str
    action: str
    price: float
    news_strength: str
    news_direction: str
    technical_confirmation: str
    cooldown_state: str
    decision_reason: str
    final_view: str
    technical_reasons: tuple[str, ...] = ()
    event_id: str = ""
    news_title: str = ""
    news_source: str = ""
    news_source_type: str = ""
    news_published_at: str = ""
    news_url: str = ""
    news_sentiment: str = ""
    news_source_action: str = "无新闻来源"
    news_topic: str = "unknown"
    news_time_horizon: str = "short_term"
    stock_relevance: str = "direct"
    quantity: float = 0.0
    fee: float = 0.0


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    initial_cash: float
    final_equity: float
    total_return: float
    max_drawdown: float
    equity_curve: tuple[float, ...]
    trades: tuple[Trade, ...]
    last_signal: StrategySignal
    decision_records: tuple[DecisionRecord, ...] = ()
