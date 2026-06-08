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
