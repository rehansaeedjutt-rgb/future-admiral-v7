from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from future_admiral_v7.config import cfg


def log_event(event_type: str, payload: dict):
    os.makedirs(os.path.dirname(cfg.AUDIT_LOG), exist_ok=True)
    with open(cfg.AUDIT_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "payload": payload,
        }, default=str) + "\n")
