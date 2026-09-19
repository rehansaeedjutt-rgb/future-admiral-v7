"""Future Admiral v7 - Market data (MEXC primary, multi-exchange fallback)"""
import ccxt
import pandas as pd
import sys

# MEXC primary — user trades here
EXCHANGES = [
    ("mexc",    "crypto"),   # User's exchange — primary
    ("bybit",   "crypto"),   # Fallback 1
    ("okx",     "crypto"),   # Fallback 2
    ("kraken",  "crypto"),   # Fallback 3 (privacy coins)
    ("coinbase", "crypto"),  # Fallback 4
    ("binance", "crypto"),   # Fallback 5
]

_cached_client = None
_cached_name = None

def _log(msg):
    print(f"[MARKET] {msg}", flush=True); sys.stdout.flush()

def _get_working_exchange():
    global _cached_client, _cached_name
    if _cached_client is not None:
        return _cached_client, _cached_name
    for name, _ in EXCHANGES:
        try:
            client = getattr(ccxt, name)({"enableRateLimit": True, "timeout": 20000})
            try:
                client.load_markets()
                # Test with BTC/USDT (most common)
                if "BTC/USDT" in client.markets:
                    _log(f"Using exchange: {name}")
                    _cached_client = client; _cached_name = name
                    return client, name
                elif "BTC/USDC" in client.markets:
                    _log(f"Using exchange: {name} (USDC)")
                    _cached_client = client; _cached_name = name
                    return client, name
                elif "BTC/USD" in client.markets:
                    _log(f"Using exchange: {name} (USD)")
                    _cached_client = client; _cached_name = name
                    return client, name
                else:
                    _log(f"{name}: no BTC pairs")
                    continue
            except Exception as e:
                _log(f"{name} test failed: {str(e)[:80]}")
                continue
        except Exception as e:
            _log(f"{name} init failed: {str(e)[:80]}")
            continue
    _log("WARNING: No exchange reachable. Using mexc as last resort.")
    _cached_client = ccxt.mexc({"enableRateLimit": True, "timeout": 20000})
    _cached_name = "mexc"
    return _cached_client, _cached_name


def _symbol_variants(symbol):
    """Generate all possible symbol formats for MEXC/multi-exchange.
    Priority: USDT (most liquid) > USDC > USD
    """
    if "/" not in symbol:
        base = symbol.upper()
        return [f"{base}/USDT", f"{base}/USDC", f"{base}/USD"]
    
    base, quote = symbol.upper().split("/", 1)
    
    # If user specified USDT, try USDT first then fallbacks
    if quote == "USDT":
        return [f"{base}/USDT", f"{base}/USDC", f"{base}/USD"]
    if quote == "USDC":
        return [f"{base}/USDC", f"{base}/USDT", f"{base}/USD"]
    if quote == "USD":
        return [f"{base}/USD", f"{base}/USDT", f"{base}/USDC"]
    
    # Unknown quote — try all
    return [f"{base}/USDT", f"{base}/USDC", f"{base}/USD"]


class MarketData:
    def __init__(self):
        self.ex, self.name = _get_working_exchange()
        self._markets_loaded = True

    def is_crypto(self, symbol):
        try:
            s = symbol.upper()
            if "/" in s:
                return True
            if s.endswith("USDT") or s.endswith("USD"):
                return True
            return False
        except Exception:
            return False

    def crypto_ohlcv(self, symbol, tf="15m", limit=500):
        last_err = None
        # 1. Try primary exchange
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

        # 2. Per-symbol fallback — try Kraken, OKX, Bybit
        _log(f"{symbol} not on {self.name}, trying fallbacks...")
        for fb_name in ["kraken", "okx", "bybit", "coinbase"]:
            try:
                fb = getattr(ccxt, fb_name)({"enableRateLimit": True, "timeout": 20000})
                for sym_variant in _symbol_variants(symbol):
                    try:
                        raw = fb.fetch_ohlcv(sym_variant, timeframe=tf, limit=limit)
                        if not raw:
                            continue
                        df = pd.DataFrame(raw, columns=["ts","open","high","low","close","volume"])
                        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
                        _log(f"  -> {symbol} found on {fb_name}")
                        return df.set_index("ts")
                    except Exception:
                        continue
            except Exception:
                continue

        raise last_err or ValueError(f"No data for {symbol} on any exchange")

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
        for sym_variant in _symbol_variants(symbol):
            try:
                if hasattr(self.ex, "fetch_funding_rate"):
                    fr = self.ex.fetch_funding_rate(sym_variant)
                    return {"funding": fr.get("fundingRate")}
            except Exception:
                continue
        return {}

    def get_all_tradable_symbols(self, quote="USDT"):
        """
        Returns list of all active symbols on MEXC.
        Prefers USDT pairs (most liquid), falls back to USDC/USD.
        """
        try:
            self.ex.load_markets()
        except Exception as e:
            _log(f"load_markets failed: {e}")
            return []

        markets = self.ex.markets or {}
        wanted_quotes = {quote, "USDT", "USDC", "USD"}

        out = set()
        for native_sym, m in markets.items():
            try:
                if not m.get("active", True):
                    continue
                if m.get("quote") not in wanted_quotes:
                    continue
                # Skip futures/options contracts
                if ":" in native_sym or "-" in native_sym:
                    continue
                # Skip stablecoins
                base = m.get("base", "")
                if base in ("USDT", "USDC", "DAI", "BUSD", "TUSD", "USDP", "FDUSD"):
                    continue
                out.add(native_sym)
            except Exception:
                continue

        result = sorted(out)
        _log(f"Found {len(result)} tradable symbols on {self.name}")
        return result
