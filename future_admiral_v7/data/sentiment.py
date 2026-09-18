from __future__ import annotations

import requests


def fear_greed() -> dict:
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8)
        data = resp.json().get("data", [])
        if data:
            item = data[0]
            return {"value": int(item.get("value", 50)), "label": item.get("value_classification", "neutral")}
    except Exception:
        pass
    return {"value": 50, "label": "neutral"}


def social_volume(symbol: str) -> dict:
    return {"note": "proxy via volume spike", "symbol": symbol}
