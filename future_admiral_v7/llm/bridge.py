"""Future Admiral v7 - LLM Bridge (Groq primary + Ollama fallback)"""
import json, os, re, sys, requests
from future_admiral_v7.config import cfg


def _log(msg):
    print(msg, flush=True); sys.stdout.flush()


GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq(prompt, max_tokens=3000, timeout=90, json_mode=False):
    """Groq gpt-oss: high max_tokens (reasoning consumes tokens)."""
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "reasoning_effort": "low",  # reduce hidden reasoning
    }
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"].get("content", "")
    return content or ""


def _call_ollama(prompt, model, max_tokens=800, timeout=120, json_mode=False):
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


def _try_providers(prompt, max_tokens, json_mode):
    """Try Groq → if empty/fail → Ollama. Returns (text, source)."""
    errors = []

    if GROQ_KEY:
        _log(f"[LLM] Groq {GROQ_MODEL}")
        try:
            text = _call_groq(prompt, max_tokens=max(max_tokens, 2000), json_mode=json_mode)
            if text.strip():
                return text, "groq"
            else:
                _log(f"[LLM] Groq returned EMPTY → trying Ollama")
                errors.append("groq: empty response")
        except Exception as e:
            errors.append(f"groq: {e}")
            _log(f"[LLM] Groq failed: {e} → Ollama")

    for model in ["llama3.2:3b", cfg.QUICK_MODEL]:
        _log(f"[LLM] Ollama {model}")
        try:
            text = _call_ollama(prompt, model, max_tokens=max_tokens, json_mode=json_mode)
            if text.strip():
                return text, f"ollama:{model}"
            errors.append(f"ollama:{model}: empty")
        except Exception as e:
            errors.append(f"ollama:{model}: {e}")
            _log(f"[LLM] {model} failed: {e}")

    raise RuntimeError(f"All LLMs failed: {errors}")


def ask(prompt, profile="quick"):
    text, source = _try_providers(prompt, max_tokens=1500, json_mode=False)
    _log(f"[LLM] <- {len(text)} chars from {source}")
    return text


def ask_json(prompt, profile="quick", retries=0):
    base = prompt + "\n\nCRITICAL: Reply with ONLY a valid JSON object. No prose, no markdown."
    try:
        raw, source = _try_providers(base, max_tokens=2500, json_mode=True)
        _log(f"[LLM] <- {len(raw)} chars from {source}")
    except Exception as e:
        _log(f"[LLM] ALL FAILED: {e}")
        return {}

    try:
        return json.loads(raw)
    except Exception:
        pass

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception as e:
            _log(f"[LLM] JSON parse err: {e}")
            fixed = re.sub(r",\s*}", "}", m.group(0))
            fixed = re.sub(r",\s*]", "]", fixed)
            try:
                return json.loads(fixed)
            except Exception:
                pass
    return {}
