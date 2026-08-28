# Project Rules: Bitget AI Hackathon

## Project Scope

This project is for the Bitget AI Base Camp Hackathon S1, US Stock AI Trading track.

The first deliverable is a requirements document for a minimal Bitget Playbook based strategy. Business code, runtime configuration, API keys, and live trading behavior must not be added before the requirements document and implementation plan are approved.

## Required Rule Chain

Before starting work, follow the global rule chain:

1. `/Users/ada/.codex/AGENTS.md`
2. `/Users/ada/Documents/root rules/00-core/00-START-HERE.md`
3. This project `AGENTS.md`
4. Relevant root rules for trading, complex scripts, credentials, and implementation planning

## Safety Boundary

- Do not write real API keys, Playbook keys, secrets, private keys, account IDs, or full account snapshots into this repository.
- Do not implement or run live trading, auto order placement, or background trading tasks without explicit user approval.
- The first version must use simulated trading, backtesting, or Playbook-generated records only.
- Strategy details should stay high-level enough for a hackathon demo and requirements document; do not record a fully tuned live trading strategy with private parameters.

## Product Direction

- Prefer Bitget-provided capabilities before custom systems.
- Use Bitget Playbook first for natural-language strategy creation, backtesting, publishing, and metric output.
- Use Bitget Agent Hub official skills first for market signals:
  - `news-briefing`
  - `macro-analyst`
  - `technical-analysis`
  - `sentiment-analyst`
  - `market-intel`
- Do not build a custom crawler, custom execution engine, or custom live trading pipeline for the first version.

## Documentation

- Requirements docs go under `docs/requirements/`.
- AI session recaps go under `docs/ai-sessions/`.
- Public-facing summary content can go in `README.md`.
- Architecture docs go under `docs/architecture/`.
- Bitget skill usage docs go under `docs/bitget-skills/`.
- Strategy docs go under `docs/strategy/`.
- Playbook prompts and backtest records go under `docs/playbook/`.
- Development diary drafts go under `docs/devlog/`.
- Security docs go under `docs/security/`.
- Project-level changes go in `CHANGELOG.md`.
- Durable project memory goes in `MEMORY.md`.
