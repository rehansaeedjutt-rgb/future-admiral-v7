"""Future Admiral v7 - Batch Scanner
Tier 2: LLM scan on top candidates from technical_scan.csv
"""
import csv, time, sys
from datetime import datetime
from pathlib import Path

from future_admiral_v7.data.market import MarketData
from future_admiral_v7.llm.bridge import ask_json


SCAN_OUTPUT = Path("scan_results.csv")

QUICK_PROMPT = """You are a quant analyst. Quick bias call.

Symbol: {symbol}
Price: {price}
RSI(15m): {rsi}
Trend: {trend}
EMA20: {ema20}
EMA50: {ema50}
ATR: {atr}
24h change: {change_24h}%
Volume ratio: {vol_ratio}

Rules:
- bullish if EMA20 > EMA50 and RSI 45-65
- bearish if EMA20 < EMA50 and RSI 35-55
- otherwise neutral
- score -10 (bearish) to +10 (bullish)

Return ONLY JSON: {{"bias":"bullish"|"bearish"|"neutral","score":5,"confidence":0.6}}"""


def _log(msg):
    print(msg, flush=True); sys.stdout.flush()


def _safe_float(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except Exception:
        return default


def quick_features(tf_map):
    if not tf_map:
        return None
    df = tf_map.get("15m")
    if df is None or (hasattr(df, "empty") and df.empty):
        df = next(iter(tf_map.values()), None)
    if df is None or len(df) < 50:
        return None

    close = df["close"]
    last = float(close.iloc[-1])

    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    high, low = df["high"], df["low"]
    tr = (high - low).rolling(14).mean()
    atr = float(tr.iloc[-1])

    trend = "range"
    if ema20 > ema50: trend = "bull"
    elif ema20 < ema50: trend = "bear"

    try:
        c24 = float(close.iloc[-96])
        change_24h = round((last / c24 - 1) * 100, 2)
    except Exception:
        change_24h = 0.0

    try:
        v = df["volume"]
        vol_ratio = round(float(v.iloc[-1] / v.tail(20).mean()), 2)
    except Exception:
        vol_ratio = 1.0

    return {
        "price": round(last, 6),
        "ema20": round(ema20, 6),
        "ema50": round(ema50, 6),
        "rsi": round(rsi, 2),
        "atr": round(atr, 6),
        "trend": trend,
        "change_24h": change_24h,
        "vol_ratio": vol_ratio,
    }


def _get_symbols_from_technical(limit, md, quote):
    """Prefer top candidates from technical_scan.csv."""
    tech_csv = Path("technical_scan.csv")
    if tech_csv.exists():
        try:
            import pandas as pd
            df = pd.read_csv(tech_csv)
            df = df.sort_values("score", ascending=False).drop_duplicates("symbol")
            symbols = df["symbol"].tolist()
            if limit and limit > 0:
                symbols = symbols[:limit]
            _log(f"Using {len(symbols)} top candidates from technical_scan.csv")
            return symbols
        except Exception as e:
            _log(f"Could not read technical_scan.csv: {e}")

    _log("Falling back to all exchange symbols")
    symbols = md.get_all_tradable_symbols(quote)
    if limit and limit > 0:
        symbols = symbols[:limit]
    return symbols


def scan(limit=0, sleep_sec=3.0, min_score=5, quote="USDT"):
    md = MarketData()
    symbols = _get_symbols_from_technical(limit, md, quote)
    _log(f"Scanning {len(symbols)} symbols on {md.name}...")

    results = []
    write_header = not SCAN_OUTPUT.exists()

    with open(SCAN_OUTPUT, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp","symbol","price","bias","score","confidence",
                "rsi","trend","ema20","ema50","change_24h","vol_ratio"
            ])

        for i, sym in enumerate(symbols, 1):
            t0 = time.time()
            try:
                tf = md.multi_tf(sym, "crypto")
                if not tf:
                    _log(f"  [{i}/{len(symbols)}] {sym}  (no data)")
                    continue

                feats = quick_features(tf)
                if not feats:
                    _log(f"  [{i}/{len(symbols)}] {sym}  (insufficient data)")
                    continue

                prompt = QUICK_PROMPT.format(symbol=sym, **feats)
                resp = ask_json(prompt, profile="quick") or {}

                bias = str(resp.get("bias", "neutral")).lower()
                if bias not in ("bullish","bearish","neutral"): bias = "neutral"
                score = _safe_float(resp.get("score"), 0)
                conf = _safe_float(resp.get("confidence"), 0)

                if feats["trend"] == "bear" and bias == "bullish" and feats["rsi"] > 70:
                    bias = "neutral"; score = 0

                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    sym, feats["price"], bias, round(score, 2), round(conf, 2),
                    feats["rsi"], feats["trend"], feats["ema20"], feats["ema50"],
                    feats["change_24h"], feats["vol_ratio"]
                ])
                f.flush()

                if score >= min_score:
                    row = {
                        "symbol": sym, "price": feats["price"], "bias": bias,
                        "score": round(score, 2), "confidence": round(conf, 2),
                        "rsi": feats["rsi"], "trend": feats["trend"],
                        "change_24h": feats["change_24h"], "vol_ratio": feats["vol_ratio"]
                    }
                    results.append(row)
                    _log(f"  [{i}/{len(symbols)}] {sym}  bias={bias}  score={score:.1f}  conf={conf:.2f}  RSI={feats['rsi']}")
                else:
                    _log(f"  [{i}/{len(symbols)}] {sym}  (score={score:.1f})")

                elapsed = time.time() - t0
                if elapsed < sleep_sec:
                    time.sleep(sleep_sec - elapsed)

            except Exception as e:
                _log(f"  [{i}/{len(symbols)}] {sym}  ERROR: {str(e)[:80]}")
                continue

    _log(f"\nScan complete. {len(results)} strong signals (score >= {min_score}).")
    _log(f"All results saved to: {SCAN_OUTPUT.resolve()}")
    return sorted(results, key=lambda r: r["score"], reverse=True)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--sleep", type=float, default=3.0)
    p.add_argument("--min-score", type=int, default=5)
    args = p.parse_args()
    scan(limit=args.limit, sleep_sec=args.sleep, min_score=args.min_score)
