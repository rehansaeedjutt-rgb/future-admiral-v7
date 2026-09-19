"""Future Admiral v7 - Auto Trade Tracker v2
Correct lifecycle:
  - PENDING   : only when signal is neutral (no entry)
  - RUNNING   : entry was set, trade is live
  - TP1_HIT   : first target hit
  - TP2_HIT   : second target hit (after TP1)
  - SL_HIT    : stop loss hit (before TP1)
  - SL_TO_BE  : TP1 hit, then price returned to entry (breakeven)
  - EXPIRED   : duration passed
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

    # Normalize: ensure both lowercase and TitleCase keys exist on each row
    key_map = {
        "symbol": "Symbol", "timeframe": "Timeframe",
        "fut_bias": "Fut Bias", "fut_type": "Type",
        "fut_entry": "Entry", "fut_sl": "SL",
        "fut_tp1": "TP1", "fut_tp2": "TP2",
        "fut_rr": "R:R", "fut_conf": "Conf",
        "fut_duration_h": "Duration_h",
        "outcome": "Outcome", "pnl_pct": "PnL %",
        "timestamp": "Timestamp",
    }
    for row in rows:
        for lower_k, title_k in key_map.items():
            if lower_k in row and title_k not in row:
                row[title_k] = row[lower_k]

    # Ensure Outcome + PnL columns exist in fields
    for f in ["Outcome", "PnL %"]:
        if f not in fields:
            fields.append(f)

    return rows, fields


def _save(rows, fields):
    # Only write TitleCase columns — clean file
    TITLE_FIELDS = [
        "Timestamp", "Symbol", "Timeframe",
        "Fut Bias", "Type", "Entry", "SL", "TP1", "TP2",
        "R:R", "Conf", "Duration_h",
        "Spot Action", "Spot Rec", "Buy Trigger", "Avoid Above",
        "Fund Score", "Institutional", "Outcome", "PnL %", "Notes",
    ]
    with open(TRADES_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TITLE_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _get(row, *keys):
    """Try multiple key names."""
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def _compute_state(row, price, current_state):
    """Full state machine. Returns (new_state, pnl_pct, message)."""
    entry = _f(_get(row, "fut_entry", "Entry"))
    sl0 = _f(_get(row, "fut_sl", "SL"))
    tp1 = _f(_get(row, "fut_tp1", "TP1"))
    tp2 = _f(_get(row, "fut_tp2", "TP2"))
    bias = str(_get(row, "fut_bias", "Fut Bias") or "neutral").lower()

    # Neutral signal — no trade
    if bias not in ("long", "short") or not entry:
        return None, None, None

    # If already in TP1_HIT or SL_TO_BE, SL moves to entry
    tp1_done = current_state in ("TP1_HIT", "SL_TO_BE")
    effective_sl = entry if tp1_done else sl0
    sl_label = "SL_TO_BE" if tp1_done else "SL_HIT"

    if not sl0:
        return "RUNNING", None, "no SL defined"

    # LONG
    if bias == "long":
        if price <= effective_sl:
            pnl = 0.0 if tp1_done else round((sl0 - entry) / entry * 100, 2)
            return sl_label, pnl, f"price {price} <= {sl_label} {effective_sl}"
        if tp2 and price >= tp2:
            return "TP2_HIT", round((tp2 - entry) / entry * 100, 2), f"TP2 hit at {tp2}"
        if tp1 and price >= tp1 and not tp1_done:
            return "TP1_HIT", round((tp1 - entry) / entry * 100, 2), f"TP1 hit at {tp1}"
        # Entry is filled at market → trade is live
        return "RUNNING", None, f"price moved to {price}"

    # SHORT
    if bias == "short":
        if price >= effective_sl:
            pnl = 0.0 if tp1_done else round((entry - sl0) / entry * 100, 2)
            return sl_label, pnl, f"price {price} >= {sl_label} {effective_sl}"
        if tp2 and price <= tp2:
            return "TP2_HIT", round((entry - tp2) / entry * 100, 2), f"TP2 hit at {tp2}"
        if tp1 and price <= tp1 and not tp1_done:
            return "TP1_HIT", round((entry - tp1) / entry * 100, 2), f"TP1 hit at {tp1}"
        return "RUNNING", None, f"price moved to {price}"

    return None, None, None


def _maybe_expire(row, current_state, default_h=48):
    if current_state in FINAL_STATES:
        return None
    try:
        ts = _get(row, "Timestamp", "timestamp") or ""
        dur = _f(_get(row, "Duration_h", "fut_duration_h"), default_h) or default_h
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d %b %Y %H:%M", "%Y-%m-%d %H:%M"):
            try:
                t = datetime.strptime(str(ts).strip(), fmt)
                if datetime.now() - t > timedelta(hours=dur):
                    return "EXPIRED"
                break
            except ValueError:
                continue
    except Exception:
        pass
    return None


def track(auto_sync=True):
    rows, fields = _load()
    if not rows:
        _log("No trades to track."); return
    if "Outcome" not in fields: fields.append("Outcome")
    if "PnL %" not in fields: fields.append("PnL %")

    md = MarketData()
    _log(f"Tracking {len(rows)} signals on {md.name}...")

    updated = 0
    cache = {}
    for i, row in enumerate(rows, 1):
        sym = _get(row, "Symbol", "symbol")
        state = str(_get(row, "Outcome") or "PENDING").strip().upper()
        if not sym:
            continue
        if state in FINAL_STATES:
            continue

        # Expiry check
        exp = _maybe_expire(row, state)
        if exp:
            row["Outcome"] = exp
            updated += 1
            _log(f"  [{i}/{len(rows)}] {sym}: {state} -> EXPIRED")
            continue

        # Fetch current price
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

        new_state, pnl, msg = _compute_state(row, price, state)
        if new_state and new_state != state:
            row["Outcome"] = new_state
            if pnl is not None:
                row["PnL %"] = f"{pnl:+.2f}%"
            updated += 1
            _log(f"  [{i}/{len(rows)}] {sym}: {state} -> {new_state}  (price={price}, {msg})")

    _save(rows, fields)
    _log(f"\nTracker done. Updated {updated} signals.")

    if auto_sync:
        _log("\nAuto-syncing to Google Sheets...")
        try:
            r = subprocess.run([sys.executable, "sync_to_sheets.py"],
                               capture_output=True, text=True, timeout=90,
                               cwd=str(Path.cwd()))
            if r.stdout:
                print(r.stdout)
        except Exception as e:
            _log(f"Auto-sync failed: {e}")


if __name__ == "__main__":
    track()
