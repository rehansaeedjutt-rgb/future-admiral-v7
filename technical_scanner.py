"""Future Admiral v7 - Tier 1 Technical Scanner
NO LLM. Pure math filter on all coins.
"""
import csv, time, sys
from datetime import datetime
from pathlib import Path

from future_admiral_v7.data.market import MarketData


OUTPUT = Path("technical_scan.csv")


def _log(msg):
    print(msg, flush=True); sys.stdout.flush()


def technical_score(df):
    """Pure rule-based score. No LLM. Returns dict."""
    if df is None or len(df) < 50:
        return None

    close = df["close"]
    high, low, vol = df["high"], df["low"], df["volume"]
    last = float(close.iloc[-1])

    # EMA stack
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    ema200 = float(close.ewm(span=200).mean().iloc[-1]) if len(close) >= 200 else ema50

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    # ATR
    tr = (high - low).rolling(14).mean()
    atr = float(tr.iloc[-1])
    atr_pct = (atr / last) * 100 if last > 0 else 0

    # Volume ratio
    try:
        vol_ratio = float(vol.iloc[-1] / vol.tail(20).mean())
    except Exception:
        vol_ratio = 1.0

    # 24h change
    try:
        c24 = float(close.iloc[-96])
        change_24h = round((last / c24 - 1) * 100, 2)
    except Exception:
        change_24h = 0.0

    # 7d change
    try:
        c7d = float(close.iloc[-672]) if len(close) >= 672 else float(close.iloc[0])
        change_7d = round((last / c7d - 1) * 100, 2)
    except Exception:
        change_7d = 0.0

    # === SCORING ===
    score = 0
    reasons = []

    # Trend (max +4)
    if ema20 > ema50 > ema200:
        score += 4; reasons.append("bull_stack")
    elif ema20 > ema50:
        score += 2; reasons.append("bull_short")
    elif ema20 < ema50 < ema200:
        score -= 4; reasons.append("bear_stack")
    elif ema20 < ema50:
        score -= 2; reasons.append("bear_short")

    # RSI (max +3)
    if 45 <= rsi <= 65:
        score += 3; reasons.append("rsi_healthy")
    elif 30 <= rsi < 45:
        score += 2; reasons.append("rsi_accum")
    elif 65 < rsi <= 75:
        score += 1; reasons.append("rsi_strong")
    elif rsi > 80:
        score -= 3; reasons.append("rsi_overbought")
    elif rsi < 25:
        score -= 2; reasons.append("rsi_deep_oversold")

    # Volume (max +3)
    if vol_ratio > 2.0:
        score += 3; reasons.append("vol_spike")
    elif vol_ratio > 1.3:
        score += 2; reasons.append("vol_high")
    elif vol_ratio < 0.5:
        score -= 1; reasons.append("vol_dead")

    # Price action
    if -5 <= change_24h <= 8:
        score += 1; reasons.append("pa_stable")
    elif change_24h > 15:
        score -= 2; reasons.append("pump_risk")
    elif change_24h < -15:
        score += 1; reasons.append("dip_buy")

    # ATR — avoid too volatile
    if atr_pct > 8:
        score -= 1; reasons.append("atr_high")

    # 7d trend
    if 5 <= change_7d <= 25:
        score += 1; reasons.append("7d_uptrend")
    elif change_7d < -25:
        score -= 1; reasons.append("7d_downtrend")

    return {
        "price": round(last, 8),
        "ema20": round(ema20, 8),
        "ema50": round(ema50, 8),
        "ema200": round(ema200, 8),
        "rsi": round(rsi, 2),
        "atr_pct": round(atr_pct, 2),
        "vol_ratio": round(vol_ratio, 2),
        "change_24h": change_24h,
        "change_7d": change_7d,
        "score": score,
        "reasons": ";".join(reasons[:5]),
    }


def scan_all(limit=0, sleep_sec=0.3, quote="USDT"):
    """Technical-only scan. No LLM. Fast."""
    md = MarketData()
    symbols = md.get_all_tradable_symbols(quote)
    if limit and limit > 0:
        symbols = symbols[:limit]

    _log(f"Technical scan: {len(symbols)} symbols on {md.name} (NO LLM)...")

    results = []
    write_header = not OUTPUT.exists()

    with open(OUTPUT, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp","symbol","price","score","reasons",
                "rsi","atr_pct","vol_ratio","change_24h","change_7d",
                "ema20","ema50","ema200"
            ])

        for i, sym in enumerate(symbols, 1):
            try:
                tf = md.multi_tf(sym, "crypto")
                if not tf:
                    continue
                df = tf.get("15m")
                if df is None or (hasattr(df, "empty") and df.empty):
                    df = next(iter(tf.values()), None)
                if df is None or len(df) < 50:
                    continue

                feats = technical_score(df)
                if not feats:
                    continue

                row = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": sym,
                    **feats
                }
                writer.writerow([
                    row["timestamp"], row["symbol"], row["price"],
                    row["score"], row["reasons"], row["rsi"], row["atr_pct"],
                    row["vol_ratio"], row["change_24h"], row["change_7d"],
                    row["ema20"], row["ema50"], row["ema200"]
                ])
                f.flush()
                results.append(row)

                # Only print strong
                if feats["score"] >= 6:
                    _log(f"  [{i}/{len(symbols)}] {sym}  score={feats['score']}  RSI={feats['rsi']}  vol={feats['vol_ratio']}  {feats['reasons'][:40]}")

                time.sleep(sleep_sec)

            except Exception as e:
                continue

    results.sort(key=lambda r: r["score"], reverse=True)
    _log(f"\nTechnical scan complete. {len(results)} coins analyzed.")
    _log(f"Top 10 by score:")
    for r in results[:10]:
        _log(f"  {r['symbol']:<15} score={r['score']:>3}  RSI={r['rsi']:>6}  vol={r['vol_ratio']:>5}  {r['reasons']}")
    _log(f"\nFull results: {OUTPUT.resolve()}")
    return results


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--sleep", type=float, default=0.3)
    args = p.parse_args()
    scan_all(limit=args.limit, sleep_sec=args.sleep)
