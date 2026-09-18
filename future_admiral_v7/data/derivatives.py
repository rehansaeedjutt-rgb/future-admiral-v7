"""Binance Futures free API."""
import requests, time
_cache = {}; _cache_ts = {}; TTL = 120

def _get(k):
    if k in _cache and time.time() - _cache_ts.get(k, 0) < TTL: return _cache[k]
    return None
def _set(k, v):
    _cache[k] = v; _cache_ts[k] = time.time()

def _derive(d):
    fr = d.get("funding_rate"); oic = d.get("open_interest_change_24h_pct")
    ls = d.get("long_short_ratio"); top = d.get("top_trader_long_pct")
    if fr is None: return "neutral"
    if oic and oic > 5 and fr < 0: return "bullish"
    if oic and oic > 5 and fr > 0.0005: return "bearish"
    if oic and oic < -5 and fr < 0: return "bearish"
    if top and top > 60 and ls and ls < 1.0: return "bullish"
    return "neutral"

def fetch_all_derivatives(symbol):
    s = symbol.replace("/","").upper()
    cached = _get(f"d_{s}")
    if cached: return cached
    out = {"funding_rate":None,"funding_rate_8h_avg":None,"open_interest":None,
           "open_interest_change_24h_pct":None,"long_short_ratio":None,
           "top_trader_long_pct":None,"taker_buy_sell_ratio":None}
    base = "https://fapi.binance.com"
    try:
        r = requests.get(f"{base}/fapi/v1/fundingRate", params={"symbol":s,"limit":24}, timeout=10)
        if r.status_code == 200 and r.json():
            rates = [float(x["fundingRate"]) for x in r.json()]
            out["funding_rate"] = rates[-1]
            out["funding_rate_8h_avg"] = sum(rates[-3:])/min(3,len(rates))
    except Exception: pass
    try:
        r = requests.get(f"{base}/fapi/v1/openInterest", params={"symbol":s}, timeout=10)
        if r.status_code == 200: out["open_interest"] = float(r.json().get("openInterest",0))
    except Exception: pass
    try:
        r = requests.get(f"{base}/futures/data/openInterestHist",
                         params={"symbol":s,"period":"1h","limit":25}, timeout=10)
        if r.status_code == 200 and len(r.json()) >= 2:
            data = r.json()
            oi_now = float(data[-1]["sumOpenInterestValue"]); oi_24h = float(data[0]["sumOpenInterestValue"])
            if oi_24h > 0: out["open_interest_change_24h_pct"] = round((oi_now/oi_24h - 1)*100, 2)
    except Exception: pass
    try:
        r = requests.get(f"{base}/futures/data/globalLongShortAccountRatio",
                         params={"symbol":s,"period":"1h","limit":1}, timeout=10)
        if r.status_code == 200 and r.json():
            out["long_short_ratio"] = float(r.json()[0].get("longShortRatio",0))
    except Exception: pass
    try:
        r = requests.get(f"{base}/futures/data/topLongShortPositionRatio",
                         params={"symbol":s,"period":"1h","limit":1}, timeout=10)
        if r.status_code == 200 and r.json():
            out["top_trader_long_pct"] = float(r.json()[0].get("longAccount",0))*100
    except Exception: pass
    out["institutional_signal"] = _derive(out)
    _set(f"d_{s}", out); return out
