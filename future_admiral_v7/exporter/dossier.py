from __future__ import annotations

import html
import json
import os
from datetime import datetime

import markdown


def json_prettify(obj) -> str:
    try:
        return json.dumps(obj, indent=2, default=str)[:4000]
    except Exception:
        return str(obj)[:4000]


def signal_to_md(sig: dict) -> str:
    tp = " / ".join(str(x) for x in (sig.get("take_profit") or []))
    return f"""**Symbol:** {sig['symbol']} · **TF:** {sig['timeframe']}
**Bias:** {sig['bias'].upper()} · **Confidence:** {sig['confidence'] * 100:.0f}%

- **Entry:** `{sig.get('entry')}`
- **Stop Loss:** `{sig.get('stop_loss')}`
- **Take Profit:** `{tp}`
- **R:R:** {sig.get('risk_reward')}
- **Size:** {sig.get('position_size_pct')}% · **Lev:** {sig.get('leverage')}x

**Reasons**
{chr(10).join('- ' + r for r in sig.get('reasons', []))}

**Risks**
{chr(10).join('- ' + r for r in sig.get('risks', []))}

**Invalidation:** {sig.get('invalidation', '-')}
"""


def save_dossier(signal: dict) -> str:
    context = signal.get("agents_summary", {}).get("context", {})
    context_html = html.escape(json_prettify(context))
    verdict_html = markdown.markdown(signal_to_md(signal))

    tpl = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{signal['symbol']} · Future Admiral Dossier</title>
  <style>
    body {{background:#0b0f19; color:#e2e8f0; font-family:'Segoe UI', Arial, sans-serif; padding:40px;}}
    .box {{max-width:1000px; margin:auto; background:#111827; padding:40px; border-radius:12px;}}
    h1 {{color:#38bdf8;}}
    h2 {{color:#34d399; border-left:4px solid #34d399; padding-left:10px;}}
    .sig {{background:#064e3b; border-left:6px solid #10b981; padding:24px; border-radius:8px;}}
    .ctx {{background:#030712; padding:20px; border-radius:8px; color:#9ca3af; font-size:.85em; white-space:pre-wrap;}}
    .ft {{margin-top:40px; color:#6b7280; text-align:center; border-top:1px solid #1f2937; padding-top:16px;}}
  </style>
</head>
<body>
  <div class="box">
    <h1>{signal['symbol']} · Future Admiral v7</h1>
    <h2>Admiral's Final Verdict</h2>
    <div class="sig">{verdict_html}</div>
    <h2>Ingested Context</h2>
    <div class="ctx">{context_html}</div>
    <div class="ft">Generated {datetime.utcnow().isoformat()} UTC · Future Admiral v7</div>
  </div>
</body>
</html>
"""
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{signal['symbol'].replace('/', '_')}_{signal['timeframe']}.html"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(tpl)
    return path
