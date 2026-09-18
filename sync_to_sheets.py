"""Future Admiral v7 - Google Sheets Auto-Sync"""
import os
import csv
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TRADES_FILE = Path("paper_trades.csv")
SYNC_STATE = Path(".gsheet_sync_state.json")
WEBHOOK_URL = os.getenv("GSHEET_WEBHOOK_URL", "").strip()


def _load_state():
    if SYNC_STATE.exists():
        try:
            return json.loads(SYNC_STATE.read_text())
        except Exception:
            pass
    return {"last_synced": 0}


def _save_state(state):
    SYNC_STATE.write_text(json.dumps(state))


def _read_csv():
    if not TRADES_FILE.exists():
        return []
    try:
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _push_row(row):
    try:
        r = requests.post(
            WEBHOOK_URL,
            json=row,
            timeout=20,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code == 200:
            try:
                data = r.json()
                return data.get("status") == "ok"
            except Exception:
                return True
        return False
    except Exception as e:
        print(f"[SYNC] Error: {e}")
        return False


def sync():
    if not WEBHOOK_URL:
        print("[SYNC] GSHEET_WEBHOOK_URL not set in .env")
        return

    rows = _read_csv()
    if not rows:
        print("[SYNC] No trades yet.")
        return

    state = _load_state()
    last = state.get("last_synced", 0)
    new_rows = rows[last:]

    if not new_rows:
        print(f"[SYNC] Already up to date. Total: {len(rows)}")
        return

    print(f"[SYNC] Pushing {len(new_rows)} new row(s)...")
    pushed = 0
    for row in new_rows:
        if _push_row(row):
            pushed += 1
            print(f"  [OK] {row.get('symbol')} {row.get('fut_bias')} @ {row.get('timestamp')}")
        else:
            print(f"  [FAIL] {row.get('symbol')} - will retry")
            break

    state["last_synced"] = last + pushed
    _save_state(state)
    print(f"[SYNC] Done. Synced {pushed}/{len(new_rows)}. Total: {state['last_synced']}")


if __name__ == "__main__":
    sync()
