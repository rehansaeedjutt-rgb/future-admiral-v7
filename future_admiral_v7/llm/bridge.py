import json, re, sys, requests
from future_admiral_v7.config import cfg

def _log(msg):
    print(msg, flush=True); sys.stdout.flush()

def _call_ollama(prompt, model, max_tokens=500, timeout=120, json_mode=False):
    url = "http://localhost:11434/api/chat"
    payload = {"model": model, "messages": [{"role":"user","content":prompt}],
               "stream": False, "options": {"num_predict": max_tokens, "temperature": 0.1}}
    if json_mode: payload["format"] = "json"
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "")

def _model_chain(profile):
    return ["llama3.2:3b", cfg.QUICK_MODEL]

def ask(prompt, profile="quick"):
    for model in _model_chain(profile):
        _log(f"[LLM:{profile}] -> {model}")
        try:
            r = _call_ollama(prompt, model, max_tokens=500, timeout=120)
            _log(f"[LLM:{profile}] <- {len(r)} chars")
            return r
        except Exception as e:
            _log(f"[LLM:{profile}] {model} failed: {e}")
    raise RuntimeError("All models failed")

def ask_json(prompt, profile="quick", retries=0):
    base = prompt + "\n\nRespond ONLY with valid JSON."
    for model in _model_chain(profile):
        for attempt in range(retries + 1):
            _log(f"[LLM:{profile}] {model} try {attempt+1}")
            try:
                raw = _call_ollama(base, model, max_tokens=500, timeout=120, json_mode=True)
                _log(f"[LLM:{profile}] <- {len(raw)} chars")
            except Exception as e:
                _log(f"[LLM:{profile}] call failed: {e}")
                break
            try:
                return json.loads(raw)
            except Exception as e:
                _log(f"[LLM:{profile}] parse err: {e}")
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    try: return json.loads(m.group(0))
                    except Exception: pass
    _log(f"[LLM:{profile}] ALL FAILED")
    return {}
