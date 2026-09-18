# Future Admiral v7 — Institutional Multi-Agent Trading Desk

100% free, local, multi-agent quantitative research suite. Har candle, news, aur macro indicator analyze karta hai, aur strict JSON trading signal deta hai.

## Features

- 7 Analyst Agents — Technical, Fundamental, News, Macro, Sentiment, OnChain, Risk
- Bull vs Bear Debate — 2 rounds with rebuttals
- Admiral (CIO) — strict JSON signal (entry, SL, TP, size, leverage, R:R)
- Multi-Timeframe — 1m, 5m, 15m, 1h, 4h, 1d
- Real Data — ccxt (Binance), yfinance, RSS, Fear and Greed
- Risk Engine — position sizing, R:R, leverage cap
- Discord Alerts — embed card with full reasoning
- Audit Trail — har signal JSONL mein save

## Quickstart

1. git clone https://github.com/rehansaeedjutt-rgb/future-admiral-v7.git
2. cd future-admiral-v7
3. python -m venv .venv
4. .venv\Scripts\activate
5. pip install -e .
6. ollama pull llama3.2:3b
7. copy .env.example .env
8. streamlit run app.py --server.port 8504

Browser: http://localhost:8504

## Architecture

- data/ — ccxt, yfinance, RSS, macro, sentiment
- features/ — indicators, market structure
- agents/ — 7 analysts + bull/bear + admiral
- debate/ — debate orchestrator
- risk/ — position sizing
- alerts/ — Discord webhook
- audit/ — JSONL audit trail
- exporter/ — HTML dossier

## Disclaimer

Yeh research tool hai, financial advice nahi. Live trading se pehle paper trade karo. Position size small rakho.

## License

MIT
