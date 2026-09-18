# Future Admiral v7 — Institutional Multi-Agent Desk (100% Free)

Real multi-agent debate, multi-timeframe analysis, free local AI, and institutional risk framing.

## Features

- Multi-agent debate system using local Ollama models
- Multi-timeframe technical checks for 1m, 5m, 15m, 1h, 4h, 1d
- Macro, sentiment, and news context integration
- Risk engine with position sizing and invalidation rules
- Telegram alerting support
- Audit log and dossier export

## Quick install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
ollama pull llama3
```

Optional:

```bash
ollama pull deepseek-r1
```

Then copy `.env.example` to `.env` and configure Telegram if needed.

## Run

```bash
streamlit run app.py
```

Or use the root-level launcher:

```bat
start_desk.bat
```

## Notes

This project is intentionally free and local-first. It does not require paid APIs. It uses Ollama plus open market data sources and feeds.
