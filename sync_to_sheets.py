"""Future Admiral v7 - Full Sheet Sync"""
import csv
import requests
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

TRADES_FILE = Path("paper_trades.csv")
WEBHOOK_URL = os.getenv("GSHEET_WEBHOOK_URL", "").strip()


def _log(msg):
    print(msg, flush=True)


def sync():
    if not WEBHOOK_URL:
        _log("[SYNC] GSHEET_WEBHOOK_URL not set in .env")
        return
    if not TRADES_FILE.exists():
        _log("[SYNC] No paper_trades.csv yet.")
        return

    with open(TRADES_FILE, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        _log("[SYNC] No trades yet.")
        return

    payload = {"mode": "full_sync", "rows": rows}

    _log(f"[SYNC] Pushing {len(rows)} rows (full sync)...")
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=60,
                          headers={"Content-Type": "application/json"})
        if r.status_code == 200:
            try:
                data = r.json()
                if data.get("status") == "ok":
                    _log(f"[SYNC] Done. Sheet now has {data.get('count', '?')} rows.")
                else:
                    _log(f"[SYNC] Apps Script error: {data.get('message')}")
            except Exception:
                _log(f"[SYNC] Response: {r.text[:200]}")
        else:
            _log(f"[SYNC] HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        _log(f"[SYNC] Request failed: {e}")


if __name__ == "__main__":
    sync()
