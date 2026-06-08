from __future__ import annotations


def moving_average(values: list[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        chunk = values[index + 1 - window : index + 1]
        result.append(sum(chunk) / window)
    return result


def pct_change(values: list[float], periods: int) -> float:
    if periods <= 0:
        raise ValueError("periods must be positive")
    if len(values) <= periods:
        return 0.0
    start = values[-1 - periods]
    if start == 0:
        return 0.0
    return round(values[-1] / start - 1.0, 12)


def rsi(values: list[float], window: int) -> float:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) <= window:
        return 50.0
    gains = 0.0
    losses = 0.0
    recent = values[-(window + 1) :]
    for previous, current in zip(recent, recent[1:]):
        change = current - previous
        if change >= 0:
            gains += change
        else:
            losses += abs(change)
    if gains == 0 and losses == 0:
        return 50.0
    if losses == 0:
        return 100.0
    relative_strength = gains / losses
    return 100 - (100 / (1 + relative_strength))


def max_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst
