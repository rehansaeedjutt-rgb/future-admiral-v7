"""Future Admiral v7 - Safe Discord alerts."""
import os, requests
from dotenv import load_dotenv
load_dotenv()

def _url():
    return os.getenv("DISCORD_WEBHOOK_URL", "").strip()

def send_discord(text, username="Future Admiral"):
    url = _url()
    if not url: return False
    try:
        r = requests.post(url, json={"username": username, "content": text[:1900]}, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False

def send_discord_embed(signal):
    """Safe embed — works even if fields missing."""
    url = _url()
    if not url: return False
    if not isinstance(signal, dict) or not signal:
        return False

    try:
        symbol = signal.get("symbol") or signal.get("ticker") or "UNKNOWN"
        timeframe = signal.get("timeframe") or "?"
        bias = str(signal.get("bias", "neutral")).lower()
        conf = float(signal.get("confidence") or 0)
        rr = signal.get("risk_reward") or 0
        entry = signal.get("entry") or "—"
        sl = signal.get("stop_loss") or "—"
        tp_list = signal.get("take_profit") or []
        if isinstance(tp_list, str):
            tp_list = [tp_list]
        tp = " / ".join(str(x) for x in tp_list[:2]) if tp_list else "—"
        size = signal.get("position_size_pct") or 0
        lev = signal.get("leverage") or 1
        inval = str(signal.get("invalidation") or "—")[:200]

        reasons_raw = signal.get("reasons") or []
        if isinstance(reasons_raw, str): reasons_raw = [reasons_raw]
        risks_raw = signal.get("risks") or []
        if isinstance(risks_raw, str): risks_raw = [risks_raw]

        reasons_text = ("\n".join(f"• {r}" for r in reasons_raw[:5]) or "—")[:1024]
        risks_text = ("\n".join(f"• {r}" for r in risks_raw[:5]) or "—")[:1024]

        color = {"long": 0x10B981, "short": 0xEF4444}.get(bias, 0x6B7280)

        embed = {
            "title": f"👑 {symbol} · {timeframe} · {bias.upper()}",
            "description": f"**Confidence:** {conf*100:.0f}%  ·  **R:R** {rr}",
            "color": color,
            "fields": [
                {"name": "Entry", "value": f"`{entry}`", "inline": True},
                {"name": "Stop Loss", "value": f"`{sl}`", "inline": True},
                {"name": "Take Profit", "value": f"`{tp}`", "inline": True},
                {"name": "Size / Lev", "value": f"{size}% · {lev}x", "inline": True},
                {"name": "Invalidation", "value": inval, "inline": False},
                {"name": "Reasons", "value": reasons_text, "inline": False},
                {"name": "Risks", "value": risks_text, "inline": False},
            ],
            "footer": {"text": "Future Admiral v7 · Institutional Desk"},
        }
        r = requests.post(url, json={"username": "Future Admiral", "embeds": [embed]}, timeout=10)
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"[DISCORD] error: {e}", flush=True)
        return False
