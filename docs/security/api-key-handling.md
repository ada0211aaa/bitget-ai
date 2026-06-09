# API Key Handling

The current project only needs one Playbook API key when actually running the official Playbook flow.
The local backtest CLI does not need any key.

This project does not require Bitget account balance, position, order-history, or live-trading credentials.

Rules:

- Do not write real keys into Markdown files.
- Do not commit `.env` files.
- Keep `.env.example` as placeholders only.
- Prefer temporary local input or safe environment variables.
- Remove secrets from screenshots before public submission.
- If a key is accidentally committed, rotate the key and clean Git history.

## Local Template

- Use `.env.example` as the template.
- Copy to `.env` only on your machine.
- Fill real values only in `.env`, never in Git-tracked files.
- Current backtest code does not need credentials.
- Do not add account, balance, position, or live-order credentials unless a separate live-trading requirement is approved.
