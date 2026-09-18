"""Future Admiral v7 - Market data with exchange fallback."""
import ccxt
import pandas as pd
import time
import sys

# Fallback chain — jo pehle kaam kare
EXCHANGES = [
    ("kraken",   "crypto"),  # Global, no geo-block
    ("coinbase", "crypto"),  # Global
    ("okx",      "crypto"),  # Global
    ("bybit",    "crypto"),  # Global
    ("binance",  "crypto"),  # Might be blocked in some regions
]

_cached_client = None
_cached_name = None

def _log(msg):
    print(f"[MARKET] {msg}", flush=True)
    sys.stdout.flush()

def _get_working_exchange():
    """Find first working exchange. Cache result."""
    global _cached_client, _cached_name
    if _cached_client is not None:
        return _cached_client, _cached_name

    for name, _ in EXCHANGES:
        try:
            client = getattr(ccxt, name)({"enableRateLimit": True, "timeout": 15000})
            # Test with BTC/USDT
            try:
                client.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=5)
                _log(f"Using exchange: {name}")
                _cached_client = client
                _cached_name = name
                return client, name
            except Exception:
                # Some exchanges use BTC/USD instead
                try:
                    client.fetch_ohlcv("BTC/USD", timeframe="1h", limit=5)
                    _log(f"Using exchange: {name} (USD pairs)")
                    _cached_client = client
                    _cached_name = name
                    return client, name
                except Exception as e:
                    _log(f"{name} failed: {str(e)[:80]}")
                    continue
        except Exception as e:
            _log(f"{name} init failed: {str(e)[:80]}")
            continue

    _log("WARNING: No exchange reachable. Using binance as last resort.")
    _cached_client = ccxt.binance({"enableRateLimit": True, "timeout": 15000})
    _cached_name = "binance"
    return _cached_client, _cached_name


def _symbol_variants(symbol):
    """Try different symbol formats."""
    base = symbol.split("/")[0].upper()
    quote = symbol.split("/")[1].upper() if "/" in symbol else "USDT"
    variants = [symbol]
    if quote == "USDT":
        variants.append(f"{base}/USD")
    if "/" not in symbol:
        variants.append(f"{symbol}/USDT")
    return list(dict.fromkeys(variants))


class MarketData:
    def __init__(self):
        self.ex, self.name = _get_working_exchange()

    def is_crypto(self, symbol):
        try:
            s = symbol.upper()
            if s.endswith("USDT") or s.endswith("USD"):
                return True
            if "/" in s:
                return True
            return False
        except Exception:
            return False

    def crypto_ohlcv(self, symbol, tf="15m", limit=500):
        last_err = None
        for sym_variant in _symbol_variants(symbol):
            try:
                raw = self.ex.fetch_ohlcv(sym_variant, timeframe=tf, limit=limit)
                if not raw:
                    continue
                df = pd.DataFrame(raw, columns=["ts","open","high","low","close","volume"])
                df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
                return df.set_index("ts")
            except Exception as e:
                last_err = e
                continue
        raise last_err or ValueError(f"No data for {symbol}")

    def multi_tf(self, symbol, kind="crypto"):
        out = {}
        for tf in ["1m","5m","15m","1h","4h","1d"]:
            try:
                df = self.crypto_ohlcv(symbol, tf, 500)
                if df is not None and len(df) > 50:
                    out[tf] = df
            except Exception:
                continue
        return out

    def orderbook(self, symbol):
        for sym_variant in _symbol_variants(symbol):
            try:
                ob = self.ex.fetch_order_book(sym_variant, limit=50)
                bid = sum(b[1] for b in ob["bids"])
                ask = sum(a[1] for a in ob["asks"])
                spread = ob["asks"][0][0] - ob["bids"][0][0]
                imbalance = (bid - ask) / (bid + ask) if (bid + ask) else 0
                return {"bid_vol": bid, "ask_vol": ask, "spread": spread, "imbalance": imbalance}
            except Exception:
                continue
        return {}

    def funding_oi(self, symbol):
        """Only available on Binance/Bybit/OKX futures. Optional."""
        for sym_variant in _symbol_variants(symbol):
            try:
                if hasattr(self.ex, "fetch_funding_rate"):
                    fr = self.ex.fetch_funding_rate(sym_variant)
                    return {"funding": fr.get("fundingRate")}
            except Exception:
                continue
        return {}
