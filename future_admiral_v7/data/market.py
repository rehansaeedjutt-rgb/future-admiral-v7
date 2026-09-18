from __future__ import annotations

import pandas as pd
import yfinance as yf

try:
    import ccxt
except Exception:  # pragma: no cover
    ccxt = None


class MarketData:
    def __init__(self):
        self.crypto = ccxt.binance({"enableRateLimit": True}) if ccxt else None

    def is_crypto(self, symbol: str) -> bool:
        s = symbol.upper().replace(" ", "")
        return s.endswith("USDT") or (s.endswith("USD") and "/" not in s and "-" not in s)

    def crypto_ohlcv(self, symbol: str, tf: str = "15m", limit: int = 500) -> pd.DataFrame:
        if self.crypto is None:
            return pd.DataFrame()
        raw = self.crypto.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
        df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        df = df.set_index("ts")
        return df

    def stock_ohlcv(self, ticker: str, interval: str = "15m", period: str = "5d") -> pd.DataFrame:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval)
        if df.empty:
            return df
        df.columns = [c.lower() for c in df.columns]
        return df[["open", "high", "low", "close", "volume"]]

    def multi_tf(self, symbol: str, kind: str = "crypto") -> dict:
        out: dict[str, pd.DataFrame] = {}
        if kind == "crypto":
            for tf in ["1m", "5m", "15m", "1h", "4h", "1d"]:
                try:
                    out[tf] = self.crypto_ohlcv(symbol, tf, 500)
                except Exception:
                    continue
        else:
            for tf, period in [("1m", "1d"), ("5m", "5d"), ("15m", "5d"), ("1h", "1mo"), ("1d", "6mo")]:
                try:
                    out[tf] = self.stock_ohlcv(symbol, tf, period)
                except Exception:
                    continue
        return out

    def orderbook(self, symbol: str) -> dict:
        if self.crypto is None:
            return {}
        try:
            ob = self.crypto.fetch_order_book(symbol, limit=50)
            bids = sum(b[1] for b in ob.get("bids", []))
            asks = sum(a[1] for a in ob.get("asks", []))
            spread = ob["asks"][0][0] - ob["bids"][0][0]
            imbalance = (bids - asks) / (bids + asks) if (bids + asks) else 0.0
            return {"bid_vol": bids, "ask_vol": asks, "spread": spread, "imbalance": imbalance}
        except Exception:
            return {}

    def funding_oi(self, symbol: str) -> dict:
        if self.crypto is None:
            return {}
        try:
            fr = self.crypto.fetch_funding_rate(symbol)
            oi = self.crypto.fetch_open_interest(symbol)
            return {"funding": fr.get("fundingRate"), "oi": oi.get("openInterestAmount")}
        except Exception:
            return {}
