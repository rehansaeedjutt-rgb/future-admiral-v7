"""On-chain flow proxy."""
import requests, time
_cache = {}; _cache_ts = {}; TTL = 300

def _get(k):
    if k in _cache and time.time() - _cache_ts.get(k, 0) < TTL: return _cache[k]
    return None
def _set(k, v):
    _cache[k] = v; _cache_ts[k] = time.time()

def _cgid(symbol):
    s = symbol.split("/")[0].lower()
    return {"btc":"bitcoin","eth":"ethereum","sol":"solana","xrp":"ripple",
            "ada":"cardano","doge":"dogecoin","bnb":"binancecoin","avax":"avalanche-2",
            "dot":"polkadot","matic":"matic-network","link":"chainlink",
            "aave":"aave","uni":"uniswap","mkr":"maker"}.get(s, s)

def fetch_exchange_flows(symbol):
    s = symbol.split("/")[0].upper()
    cached = _get(f"flow_{s}")
    if cached: return cached
    out = {"exchange_netflow_signal":"neutral","notes":[],"available":False}
    try:
        r = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{_cgid(symbol)}/market_chart",
            params={"vs_currency":"usd","days":7,"interval":"daily"}, timeout=15)
        if r.status_code == 200:
            d = r.json()
            prices = d.get("prices", []); vols = d.get("total_volumes", [])
            if len(prices) >= 3 and len(vols) >= 3:
                pc = (prices[-1][1]/prices[-2][1]) - 1
                vc = (vols[-1][1]/vols[-2][1]) - 1
                if vc > 0.3 and pc < -0.02:
                    out["exchange_netflow_signal"] = "bullish"
                    out["notes"].append("High volume + price drop = accumulation")
                elif vc > 0.3 and pc > 0.02:
                    out["exchange_netflow_signal"] = "bearish"
                    out["notes"].append("High volume + price pump = distribution")
                out["available"] = True
                out["price_change_24h"] = round(pc*100, 2)
                out["volume_change_24h"] = round(vc*100, 2)
    except Exception: pass
    _set(f"flow_{s}", out); return out
