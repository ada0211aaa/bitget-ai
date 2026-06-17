# Aggressive News Decision Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a research-only aggressive news decision mode that creates real buy/sell backtest markers from recent true news plus acceptable daily technical context.

**Architecture:** Keep the existing conservative policy as the default. Add a `decision_mode` config option that lets the current daily external backtest use `aggressive_news`, where buy/sell decisions still require a matched news event and never fall back to pure technical-only entries.

**Tech Stack:** Python standard library, existing CLI/backtester/policy modules, pytest.

---

## File Structure

- Modify `src/bitget_ai_backtest/config.py`: parse `decision_mode` with default `conservative`.
- Modify `src/bitget_ai_backtest/backtester.py`: pass the selected decision mode into the policy.
- Modify `src/bitget_ai_backtest/conservative_policy.py`: implement aggressive news thresholds behind a parameter.
- Modify `configs/us_stock_daily_external.json`: enable `aggressive_news` for this research/demo config.
- Modify tests in `tests/test_config.py`, `tests/test_conservative_policy.py`, `tests/test_backtester.py`, and `tests/test_cli.py`.

## Requirements

- Conservative mode remains unchanged by default.
- Aggressive news mode can buy on `强利好` with acceptable technical context, or on `利好` when technical confirmation is already positive.
- Aggressive news mode can sell an existing position on `强利空` or `利空`, even if MA confirmation is not perfect.
- Aggressive news mode must not buy when there is no matched news event.
- Generated buy/sell trades must keep normal marker generation and decision rows unchanged.
