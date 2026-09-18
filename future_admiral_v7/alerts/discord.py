import os

import requests
from dotenv import load_dotenv

load_dotenv()


def _url() -> str:
    return os.getenv("DISCORD_WEBHOOK_URL", "").strip()


def send_discord(text: str, username: str = "Future Admiral") -> bool:
    url = _url()
    if not url:
        return False
    try:
        r = requests.post(
            url,
            json={
                "username": username,
                "content": text[:1900],
            },
            timeout=10,
        )
        return r.status_code in (200, 204)
    except Exception:
        return False


def send_discord_embed(signal: dict) -> bool:
    """Professional embed card — Wall Street style."""
    url = _url()
    if not url:
        return False

    bias = signal.get("bias", "neutral")
    color = {"long": 0x10B981, "short": 0xEF4444, "neutral": 0x6B7280}.get(bias, 0x6B7280)
    tp = " / ".join(str(x) for x in (signal.get("take_profit") or [])[:3]) or "-"

    embed = {
        "title": f"👑 {signal['symbol']} · {signal['timeframe']} · {bias.upper()}",
        "description": f"**Confidence:** {signal['confidence']*100:.0f}%  ·  **R:R** {signal.get('risk_reward', 0)}",
        "color": color,
        "fields": [
            {"name": "Entry", "value": f"`{signal.get('entry', '-')}`", "inline": True},
            {"name": "Stop Loss", "value": f"`{signal.get('stop_loss', '-')}`", "inline": True},
            {"name": "Take Profit", "value": f"`{tp}`", "inline": True},
            {"name": "Size / Lev", "value": f"{signal.get('position_size_pct', 0)}% · {signal.get('leverage', 1)}x", "inline": True},
            {"name": "Invalidation", "value": (signal.get("invalidation") or "-")[:200], "inline": False},
            {"name": "Reasons", "value": "\n".join(f"• {r}" for r in (signal.get("reasons") or [])[:5])[:1024] or "-", "inline": False},
            {"name": "Risks", "value": "\n".join(f"• {r}" for r in (signal.get("risks") or [])[:5])[:1024] or "-", "inline": False},
        ],
        "footer": {"text": "Future Admiral v7 · Institutional Desk"},
    }

    try:
        r = requests.post(url, json={"username": "Future Admiral", "embeds": [embed]}, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False
