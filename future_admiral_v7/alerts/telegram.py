from __future__ import annotations

import requests

from future_admiral_v7.config import cfg


def send_telegram(text: str) -> bool:
    if not cfg.TELEGRAM_TOKEN or not cfg.TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{cfg.TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": cfg.TELEGRAM_CHAT_ID,
            "text": text[:4000],
            "parse_mode": "Markdown",
        }, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def format_signal_message(sig: dict) -> str:
    tp = " / ".join(str(x) for x in (sig.get("take_profit") or [])[:3])
    return f"""*🚨 FUTURE ADMIRAL SIGNAL*

*{sig['symbol']}* · `{sig['timeframe']}`
Bias: *{sig['bias'].upper()}*
Confidence: {sig['confidence'] * 100:.0f}%

Entry: `{sig.get('entry')}`
SL: `{sig.get('stop_loss')}`
TP: `{tp}`
R:R: {sig.get('risk_reward')}
Size: {sig.get('position_size_pct')}% · Lev {sig.get('leverage')}x

*Reasons*
{chr(10).join('• ' + r for r in sig.get('reasons', [])[:5])}

*Risks*
{chr(10).join('• ' + r for r in sig.get('risks', [])[:5])}

_Invalidation_: {sig.get('invalidation', '-')}
"""
