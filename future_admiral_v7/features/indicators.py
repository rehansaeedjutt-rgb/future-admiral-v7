from __future__ import annotations

import pandas as pd

try:
    import pandas_ta as ta
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "pandas-ta is missing in the active Python environment. "
        "Run: .\\.venv313\\Scripts\\python.exe -m pip install pandas-ta"
    ) from exc


def tf_features(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 50:
        return {}
    data = df.copy()
    data["ema20"] = ta.ema(data["close"], 20)
    data["ema50"] = ta.ema(data["close"], 50)
    data["ema200"] = ta.ema(data["close"], 200)
    data["rsi"] = ta.rsi(data["close"], 14)
    data["atr"] = ta.atr(data["high"], data["low"], data["close"], 14)

    macd = ta.macd(data["close"])
    if macd is not None:
        data = data.join(macd)

    bb = ta.bbands(data["close"], 20, 2)
    if bb is not None:
        data = data.join(bb)

    last = data.iloc[-1]
    trend = "range"
    if last["ema20"] > last["ema50"] > last["ema200"]:
        trend = "bull"
    elif last["ema20"] < last["ema50"] < last["ema200"]:
        trend = "bear"

    return {
        "close": float(last["close"]),
        "ema20": float(last["ema20"]),
        "ema50": float(last["ema50"]),
        "ema200": float(last["ema200"]),
        "rsi": float(last["rsi"]) if pd.notna(last["rsi"]) else 50.0,
        "atr": float(last["atr"]) if pd.notna(last["atr"]) else 0.0,
        "macd_h": float(last.get("MACDh_12_26_9", 0)) if pd.notna(last.get("MACDh_12_26_9", 0)) else 0.0,
        "bb_up": float(last.get("BBU_20_2.0", last["close"])),
        "bb_lo": float(last.get("BBL_20_2.0", last["close"])),
        "vwap": float(last.get("vwap", last["close"])),
        "trend": trend,
    }


def multi_tf_summary(tf_map: dict) -> dict:
    summary = {}
    for tf, frame in tf_map.items():
        if frame is not None and len(frame) >= 50:
            summary[tf] = tf_features(frame)
    return summary


def market_structure(df: pd.DataFrame, lookback: int = 60) -> dict:
    if df is None or len(df) < lookback:
        return {}
    recent = df.tail(lookback)
    highs = recent["high"].nlargest(3).tolist()
    lows = recent["low"].nsmallest(3).tolist()
    return {
        "resistance": sorted(highs, reverse=True),
        "support": sorted(lows),
        "last_close": float(recent["close"].iloc[-1]),
    }
