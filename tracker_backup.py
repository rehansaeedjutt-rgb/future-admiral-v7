"""Future Admiral v7 - Auto Trade Tracker
Enhanced: RUNNING detection, TP1/TP2 hit, SL_HIT, SL_TO_BE (breakeven).
Auto-syncs to Google Sheets at the end.
"""
import csv, sys, subprocess
from datetime import datetime, timedelta
from pathlib import Path

from future_admiral_v7.data.market import MarketData

TRADES_FILE = Path("paper_trades.csv")
FINAL_STATES = {"TP2_HIT", "SL_HIT", "SL_TO_BE", "EXPIRED", "CANCELLED"}


def _log(msg):
    print(msg, flush=True); sys.stdout.flush()


def _f(v, default=None):
    try:
        return float(v) if v not in (None, "", "None") else default
    except Exception:
        return default


def _load():
    if not TRADES_FILE.exists():
        return [], []
    with open(TRADES_FILE, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fields = r.fieldnames or []
    return rows, fields


def _save(rows, fields):
    with open(TRADES_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _check(row, price, current_state):
    """State machine for trade lifecycle.
    Returns (new_state, pnl_pct, message).
    """
    entry = _f(row.get("fut_entry"))
    sl_orig = _f(row.get("fut_sl"))
    tp1 = _f(row.get("fut_tp1"))
    tp2 = _f(row.get("fut_tp2"))
    bias = (row.get("fut_bias") or "neutral").lower()

    if not entry or not sl_orig or bias not in ("long", "short"):
        return None, None, None

    tp1_already = current_state in ("TP1_HIT", "SL_TO_BE")
    effective_sl = entry if tp1_already else sl_orig
    sl_label = "SL_TO_BE" if tp1_already else "SL_HIT"

    if bias == "long":
        if price <= effective_sl:
            pnl = 0.0 if tp1_already else round((sl_orig - entry) / entry * 100, 2)
            return sl_label, pnl, f"price {price} <= {sl_label} at {effective_sl}"
        if tp2 and price >= tp2:
            return "TP2_HIT", round((tp2 - entry) / entry * 100, 2), f"TP2 hit at {tp2}"
        if tp1 and price >= tp1 and not tp1_already:
            return "TP1_HIT", round((tp1 - entry) / entry * 100, 2), f"TP1 hit at {tp1}"
        # Still in play
        if abs(price - entry) / entry > 0.001:  # >0.1% move
            return "RUNNING", None, f"price moved to {price}"
        return "PENDING", None, None

    if bias == "short":
        if price >= effective_sl:
            pnl = 0.0 if tp1_already else round((entry - sl_orig) / entry * 100, 2)
            return sl_label, pnl, f"price {price} >= {sl_label} at {effective_sl}"
        if tp2 and price <= tp2:
            return "TP2_HIT", round((entry - tp2) / entry * 100, 2), f"TP2 hit at {tp2}"
        if tp1 and price <= tp1 and not tp1_already:
            return "TP1_HIT", round((entry - tp1) / entry * 100, 2), f"TP1 hit at {tp1}"
        if abs(price - entry) / entry > 0.001:
            return "RUNNING", None, f"price moved to {price}"
        return "PENDING", None, None

    return None, None, None


def _maybe_expire(row, current_state, default_hours=48):
    """Check if trade expired based on duration."""
    if current_state in FINAL_STATES:
        return None
    try:
        ts = row.get("Timestamp") or row.get("timestamp") or ""
        dur = _f(row.get("Duration_h"), default_hours) or default_hours
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d %b %Y %H:%M", "%Y-%m-%d %H:%M"):
            try:
                t = datetime.strptime(ts.strip(), fmt)
                if datetime.now() - t > timedelta(hours=dur):
                    return "EXPIRED"
                break
            except ValueError:
                continue
    except Exception:
        pass
    return None


def track(expire_hours_default=48, auto_sync=True):
    rows, fields = _load()
    if not rows:
        _log("No trades to track."); return

    if "Outcome" not in fields:
        fields.append("Outcome")
    if "PnL %" not in fields:
        fields.append("PnL %")

    md = MarketData()
    _log(f"Tracking {len(rows)} signals on {md.name}...")

    updated = 0
    cache = {}
    for i, row in enumerate(rows, 1):
        sym = row.get("Symbol") or row.get("symbol")
        state = (row.get("Outcome") or "PENDING").strip().upper()
        if not sym:
            continue
        if state in FINAL_STATES:
            continue

        # Expiry check first
        exp = _maybe_expire(row, state, expire_hours_default)
        if exp:
            row["Outcome"] = exp
            updated += 1
            _log(f"  [{i}/{len(rows)}] {sym}: {state} -> EXPIRED")
            continue

        # Fetch price
        if sym not in cache:
            try:
                df = md.crypto_ohlcv(sym, "15m", 5)
                cache[sym] = float(df["close"].iloc[-1]) if df is not None and len(df) > 0 else None
            except Exception as e:
                cache[sym] = None
                _log(f"  [{i}/{len(rows)}] {sym}: price error - {str(e)[:60]}")
        price = cache.get(sym)
        if price is None:
            continue

        new_state, pnl, msg = _check(row, price, state)
        if new_state and new_state != state:
            row["Outcome"] = new_state
            if pnl is not None:
                row["PnL %"] = f"{pnl:+.2f}%"
            updated += 1
            _log(f"  [{i}/{len(rows)}] {sym}: {state} -> {new_state}  ({msg})")

    _save(rows, fields)
    _log(f"\nTracker done. Updated {updated} signals.")

    if auto_sync:
        _log("\nAuto-syncing to Google Sheets...")
        try:
            r = subprocess.run(
                [sys.executable, "sync_to_sheets.py"],
                capture_output=True, text=True, timeout=90, cwd=str(Path.cwd())
            )
            out = (r.stdout or "").strip()
            if out:
                print(out)
        except Exception as e:
            _log(f"Auto-sync failed: {e}")


if __name__ == "__main__":
    track()
