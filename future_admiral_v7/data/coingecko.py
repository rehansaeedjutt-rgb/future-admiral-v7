"""CoinGecko free API."""
import requests, time
_cached = {}; _cache_ts = {}; TTL = 300

def _get(k):
    if k in _cached and time.time() - _cache_ts.get(k, 0) < TTL: return _cached[k]
    return None
def _set(k, v):
    _cached[k] = v; _cache_ts[k] = time.time()

def _cgid(symbol):
    s = symbol.split("/")[0].lower()
    return {
        "btc":"bitcoin","eth":"ethereum","sol":"solana","xrp":"ripple",
        "ada":"cardano","doge":"dogecoin","bnb":"binancecoin","avax":"avalanche-2",
        "dot":"polkadot","matic":"matic-network","link":"chainlink","uni":"uniswap",
        "atom":"cosmos","ltc":"litecoin","trx":"tron","near":"near",
        "apt":"aptos","arb":"arbitrum","op":"optimism","sui":"sui",
        "inj":"injective-protocol","ton":"the-open-network","shib":"shiba-inu",
        "pepe":"pepe","aave":"aave","mkr":"maker","crv":"curve-dao-token",
        "ldo":"lido-dao","rpl":"rocket-pool","fil":"filecoin",
    }.get(s, s)

def fetch_fundamentals(symbol):
    cg = _cgid(symbol)
    cached = _get(f"f_{cg}")
    if cached: return cached
    try:
        r = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{cg}",
            params={"localization":"false","tickers":"false","market_data":"true",
                    "community_data":"true","developer_data":"true","sparkline":"false"},
            timeout=15, headers={"User-Agent":"FutureAdmiral/7"})
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "id": cg}
        d = r.json()
        md = d.get("market_data", {}); dev = d.get("developer_data", {}); comm = d.get("community_data", {})
        out = {
            "id": cg, "name": d.get("name", ""), "market_cap_rank": d.get("market_cap_rank"),
            "market_cap_usd": md.get("market_cap", {}).get("usd"),
            "fdv_usd": md.get("fully_diluted_valuation", {}).get("usd"),
            "circulating_supply": md.get("circulating_supply"), "max_supply": md.get("max_supply"),
            "supply_ratio": round((md.get("circulating_supply") or 0) / (md.get("max_supply") or md.get("total_supply") or 1), 4),
            "price_change_24h_pct": md.get("price_change_percentage_24h"),
            "price_change_7d_pct": md.get("price_change_percentage_7d"),
            "price_change_30d_pct": md.get("price_change_percentage_30d"),
            "ath_change_pct": md.get("ath_change_percentage", {}).get("usd"),
            "atl_change_pct": md.get("atl_change_percentage", {}).get("usd"),
            "volume_24h_usd": md.get("total_volume", {}).get("usd"),
            "github_stars": dev.get("stars"), "github_commits_4w": dev.get("commit_count_4_weeks"),
            "twitter_followers": comm.get("twitter_followers"), "reddit_subscribers": comm.get("reddit_subscribers"),
        }
        score = 50
        rank = out.get("market_cap_rank") or 9999
        if rank <= 10: score += 20
        elif rank <= 50: score += 10
        elif rank > 200: score -= 10
        sr = out.get("supply_ratio") or 0
        if sr > 0.9: score += 10
        elif sr < 0.4: score -= 10
        if (out.get("github_commits_4w") or 0) > 50: score += 10
        elif (out.get("github_commits_4w") or 0) > 10: score += 5
        if (out.get("twitter_followers") or 0) > 1_000_000: score += 10
        elif (out.get("twitter_followers") or 0) > 100_000: score += 5
        vol = out.get("volume_24h_usd") or 0; mc = out.get("market_cap_usd") or 1
        if vol/mc > 0.1: score += 5
        elif vol/mc < 0.01: score -= 5
        out["fundamental_score"] = max(0, min(100, score))
        _set(f"f_{cg}", out); return out
    except Exception as e:
        return {"error": str(e), "id": cg}

def fetch_global():
    cached = _get("global")
    if cached: return cached
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        if r.status_code != 200: return {}
        d = r.json().get("data", {})
        out = {"total_market_cap_usd": d.get("total_market_cap", {}).get("usd"),
               "btc_dominance": d.get("market_cap_percentage", {}).get("btc"),
               "eth_dominance": d.get("market_cap_percentage", {}).get("eth"),
               "market_cap_change_24h_pct": d.get("market_cap_change_percentage_24h_usd")}
        _set("global", out); return out
    except Exception:
        return {}
