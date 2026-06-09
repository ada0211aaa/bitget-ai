# API Key Handling

Playbook API keys are required only when actually running Bitget Playbook.
Bitget trading API credentials are required only for authenticated account or trading API calls.

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
- Current backtest code does not need trading credentials.
