import pandas_ta as ta
import pandas as pd
import numpy as np


def tf_features(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 50:
        return {}
    df = df.copy()
    df["ema20"] = ta.ema(df["close"], 20)
    df["ema50"] = ta.ema(df["close"], 50)
    df["ema200"] = ta.ema(df["close"], 200)
    df["rsi"] = ta.rsi(df["close"], 14)
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], 14)
    macd = ta.macd(df["close"])
    if macd is not None:
        df = df.join(macd)

    last = df.iloc[-1]
    trend = "range"
    if pd.notna(last["ema20"]) and pd.notna(last["ema50"]) and pd.notna(last["ema200"]):
        if last["ema20"] > last["ema50"] > last["ema200"]:
            trend = "bull"
        elif last["ema20"] < last["ema50"] < last["ema200"]:
            trend = "bear"

    def _f(v, d=0.0):
        return round(float(v), 4) if pd.notna(v) else d

    return {
        "close": _f(last["close"]),
        "ema20": _f(last["ema20"]),
        "ema50": _f(last["ema50"]),
        "ema200": _f(last["ema200"]),
        "rsi": _f(last["rsi"], 50.0),
        "atr": _f(last["atr"]),
        "macd_h": _f(last.get("MACDh_12_26_9", 0)),
        "trend": trend,
    }


def multi_tf_summary(tf_map: dict) -> dict:
    return {tf: tf_features(df) for tf, df in tf_map.items() if df is not None and len(df) >= 50}


def market_structure(df: pd.DataFrame, lookback: int = 100) -> dict:
    """Real support/resistance + swing levels from actual OHLCV."""
    if df is None or len(df) < lookback:
        return {}
    d = df.tail(lookback).copy()

    # Pivot-based S/R (real institutional method)
    highs = d["high"].values
    lows = d["low"].values

    pivot_highs = []
    pivot_lows = []
    for i in range(2, len(d) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            pivot_highs.append(float(highs[i]))
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            pivot_lows.append(float(lows[i]))

    # Cluster nearby levels (within 0.5% of each other)
    def cluster(levels, tol=0.005):
        if not levels:
            return []
        levels = sorted(levels)
        clusters = [[levels[0]]]
        for lvl in levels[1:]:
            if abs(lvl - clusters[-1][-1]) / clusters[-1][-1] < tol:
                clusters[-1].append(lvl)
            else:
                clusters.append([lvl])
        return [round(sum(c)/len(c), 4) for c in clusters]

    resistance = sorted(cluster(pivot_highs), reverse=True)[:3]
    support = sorted(cluster(pivot_lows))[:3]

    last_close = float(d["close"].iloc[-1])
    recent_high = float(d["high"].max())
    recent_low = float(d["low"].min())
    avg_vol = float(d["volume"].tail(20).mean()) if "volume" in d.columns else 0
    last_vol = float(d["volume"].iloc[-1]) if "volume" in d.columns else 0
    vol_ratio = round(last_vol / avg_vol, 2) if avg_vol > 0 else 1.0

    return {
        "last_close": round(last_close, 4),
        "recent_high": round(recent_high, 4),
        "recent_low": round(recent_low, 4),
        "support": support,
        "resistance": resistance,
        "volume_ratio": vol_ratio,
        "atr_pct": round((float(d["high"].iloc[-1] - d["low"].iloc[-1]) / last_close) * 100, 3),
    }
