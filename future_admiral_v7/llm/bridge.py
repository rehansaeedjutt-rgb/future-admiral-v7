"""Future Admiral v7 - LLM Bridge (Ollama-only, clean)"""
import json, re, sys, requests
from future_admiral_v7.config import cfg


def _log(msg):
    print(msg, flush=True); sys.stdout.flush()


def _call_ollama(prompt, model, max_tokens=800, timeout=180, json_mode=False):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.1},
    }
    if json_mode:
        payload["format"] = "json"
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "")


def ask(prompt, profile="quick"):
    model = cfg.QUICK_MODEL if profile == "quick" else cfg.DEEP_MODEL
    _log(f"[LLM] {model}")
    text = _call_ollama(prompt, model, max_tokens=600)
    _log(f"[LLM] <- {len(text)} chars")
    return text


def ask_json(prompt, profile="quick", retries=0):
    model = cfg.QUICK_MODEL if profile == "quick" else cfg.DEEP_MODEL
    base = prompt + "\n\nReply ONLY with valid JSON."
    _log(f"[LLM] {model} (json)")
    try:
        raw = _call_ollama(base, model, max_tokens=800, json_mode=True)
        _log(f"[LLM] <- {len(raw)} chars")
    except Exception as e:
        _log(f"[LLM] failed: {e}")
        return {}
    try:
        return json.loads(raw)
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}
