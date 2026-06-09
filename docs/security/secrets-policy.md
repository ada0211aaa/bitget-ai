# Secrets Policy

Never commit:

- Playbook API keys.
- Bitget API keys.
- API secrets.
- Passphrases.
- Private keys.
- Full account snapshots.
- Real live-trading configuration.

Use placeholders such as `<PLAYBOOK_API_KEY>`.
Use `.env.example` for placeholder structure only; never put real secrets there.
