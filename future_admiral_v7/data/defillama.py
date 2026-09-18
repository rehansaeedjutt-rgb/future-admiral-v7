"""DeFiLlama free API."""
import requests, time
_cache = {}; _cache_ts = {}; TTL = 600

def _get(k):
    if k in _cache and time.time() - _cache_ts.get(k, 0) < TTL: return _cache[k]
    return None
def _set(k, v):
    _cache[k] = v; _cache_ts[k] = time.time()

def _slug(symbol):
    s = symbol.split("/")[0].lower()
    return {"eth":"ethereum","sol":"solana","avax":"avalanche","matic":"polygon",
            "arb":"arbitrum","op":"optimism","uni":"uniswap","aave":"aave",
            "mkr":"maker","crv":"curve-dex","ldo":"lido","gmx":"gmx",
            "sui":"sui","apt":"aptos","near":"near","inj":"injective"}.get(s, s)

def fetch_tvl(symbol):
    slug = _slug(symbol)
    cached = _get(f"tvl_{slug}")
    if cached: return cached
    try:
        r = requests.get(f"https://api.llama.fi/protocol/{slug}", timeout=15)
        if r.status_code != 200: return {"available": False}
        d = r.json(); h = d.get("tvl", [])
        cur = h[-1].get("totalLiquidityUSD") if h else None
        t7 = h[-8].get("totalLiquidityUSD") if len(h) >= 8 else None
        t30 = h[-31].get("totalLiquidityUSD") if len(h) >= 31 else None
        out = {"available": True, "name": d.get("name"), "category": d.get("category"),
               "tvl_now": cur, "tvl_7d_ago": t7, "tvl_30d_ago": t30,
               "tvl_change_7d_pct": round((cur/t7 - 1)*100, 2) if (cur and t7) else None,
               "tvl_change_30d_pct": round((cur/t30 - 1)*100, 2) if (cur and t30) else None}
        _set(f"tvl_{slug}", out); return out
    except Exception:
        return {"available": False}

def fetch_fees(symbol):
    slug = _slug(symbol)
    cached = _get(f"fees_{slug}")
    if cached: return cached
    try:
        r = requests.get(f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyFees", timeout=15)
        if r.status_code != 200: return {"available": False}
        d = r.json()
        out = {"available": True, "total_24h": d.get("total24h"),
               "total_7d": d.get("total7d"), "total_30d": d.get("total30d"),
               "change_1d": d.get("change_1d"), "change_7d": d.get("change_7d")}
        _set(f"fees_{slug}", out); return out
    except Exception:
        return {"available": False}
