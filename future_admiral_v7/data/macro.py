from __future__ import annotations

import yfinance as yf


def fetch_macro() -> dict:
    out: dict[str, float] = {}
    pairs = [("^VIX", "vix"), ("^TNX", "us10y"), ("DX-Y.NYB", "dxy"), ("^GSPC", "spx"), ("GC=F", "gold")]
    for symbol, label in pairs:
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if not hist.empty:
                out[label] = round(float(hist["Close"].iloc[-1]), 2)
        except Exception:
            continue
    return out
