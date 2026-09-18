"""Smart Money Concepts."""
import pandas as pd

def find_order_blocks(df, lookback=50):
    if df is None or len(df) < lookback: return []
    d = df.tail(lookback).copy(); obs = []
    for i in range(2, len(d) - 2):
        prev = d.iloc[i]; nxt = d.iloc[i+1]
        if prev["close"] < prev["open"]:
            if (nxt["close"] - nxt["open"]) / nxt["open"] > 0.015:
                obs.append({"type":"bullish_ob","low":round(float(prev["low"]),4),
                            "high":round(float(prev["high"]),4),"index":i})
        if prev["close"] > prev["open"]:
            if (nxt["close"] - nxt["open"]) / nxt["open"] < -0.015:
                obs.append({"type":"bearish_ob","low":round(float(prev["low"]),4),
                            "high":round(float(prev["high"]),4),"index":i})
    return obs[-4:]

def find_fvg(df, lookback=30):
    if df is None or len(df) < lookback: return []
    d = df.tail(lookback).copy(); fvgs = []
    for i in range(2, len(d)):
        p2 = d.iloc[i-2]; cur = d.iloc[i]
        if cur["low"] > p2["high"]:
            fvgs.append({"type":"bullish_fvg","low":round(float(p2["high"]),4),
                         "high":round(float(cur["low"]),4)})
        if cur["high"] < p2["low"]:
            fvgs.append({"type":"bearish_fvg","low":round(float(cur["high"]),4),
                         "high":round(float(p2["low"]),4)})
    return fvgs[-4:]

def find_liquidity_zones(df, lookback=50):
    if df is None or len(df) < lookback: return {}
    d = df.tail(lookback); highs = d["high"].values; lows = d["low"].values
    eh = []; el = []
    for i in range(len(highs) - 1):
        for j in range(i+1, min(i+10, len(highs))):
            if abs(highs[i] - highs[j]) / highs[i] < 0.002:
                eh.append(round(float((highs[i]+highs[j])/2), 4))
            if abs(lows[i] - lows[j]) / lows[i] < 0.002:
                el.append(round(float((lows[i]+lows[j])/2), 4))
    return {"equal_highs": sorted(set(eh), reverse=True)[:3],
            "equal_lows": sorted(set(el))[:3]}

def smc_summary(df):
    return {"order_blocks": find_order_blocks(df),
            "fvgs": find_fvg(df),
            "liquidity": find_liquidity_zones(df)}
