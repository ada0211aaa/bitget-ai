# Failure Premortem

This project can fail in predictable ways:

| Failure | Mitigation |
| --- | --- |
| Playbook key is unavailable | Prepare docs, prompt, and devlog first; run Playbook after access is available. |
| Backtest result is weak | Keep strategy versioned and compare prompt variants. |
| News signal is too vague | Split news into relevance, sentiment, event strength, coverage breadth, and freshness. |
| Demo looks like a concept only | Record Playbook outputs, screenshots, and submission-ready summaries. |
| Repo looks confusing | Keep folder README files and point the main README to the core docs. |
| Secrets leak | Use `.gitignore`, placeholder-only docs, and pre-commit sensitive string scans. |
| Scope grows too large | Keep first version documentation-only and Playbook-first. |
