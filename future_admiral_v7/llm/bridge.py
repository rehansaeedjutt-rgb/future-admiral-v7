"""Future Admiral v7 - LLM Bridge (Groq primary + Ollama fallback)"""
import json, os, re, sys, time, requests
from dotenv import load_dotenv
load_dotenv()

def _log(msg):
    print(msg, flush=True); sys.stdout.flush()

GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = os.getenv("OLLAMA_QUICK_MODEL", "llama3.2:3b")


def _call_groq(prompt, max_tokens=2500, timeout=90):
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "reasoning_effort": "low",
    }
    for attempt in range(3):
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=timeout)
        if r.status_code == 429:
            wait = 2 ** attempt * 5
            _log(f"[LLM] Groq 429 rate limit - waiting {wait}s (attempt {attempt+1}/3)")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"].get("content", "") or ""
    raise RuntimeError("Groq rate limit exceeded after 3 retries")


def _call_ollama(prompt, max_tokens=800, timeout=360, json_mode=False):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.1},
    }
    if json_mode:
        payload["format"] = "json"
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "")


def _try_providers(prompt, max_tokens):
    errors = []
    if GROQ_KEY:
        _log(f"[LLM] Groq {GROQ_MODEL}")
        try:
            text = _call_groq(prompt, max_tokens=max(max_tokens, 2000))
            if text.strip():
                return text, "groq"
            _log("[LLM] Groq EMPTY -> Ollama")
        except Exception as e:
            errors.append(f"groq: {str(e)[:80]}")
            _log(f"[LLM] Groq failed: {str(e)[:80]} -> Ollama")

    # Ollama fallback disabled by default (unreliable for signals)
    if os.getenv("ALLOW_OLLAMA_FALLBACK", "").lower() == "true":
        _log(f"[LLM] Ollama {OLLAMA_MODEL}")
        try:
            text = _call_ollama(prompt, max_tokens=max_tokens, json_mode=True)
            if text.strip():
                return text, "ollama"
        except Exception as e:
            errors.append(f"ollama: {str(e)[:80]}")

    raise RuntimeError(f"All LLMs failed: {errors}")


def ask(prompt, profile="quick"):
    text, src = _try_providers(prompt, max_tokens=1500)
    _log(f"[LLM] <- {len(text)} chars from {src}")
    return text


def ask_json(prompt, profile="quick", retries=0):
    base = prompt + "\n\nReply ONLY with valid JSON. No prose, no markdown."
    try:
        raw, src = _try_providers(base, max_tokens=2500)
        _log(f"[LLM] <- {len(raw)} chars from {src}")
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
            fixed = re.sub(r",\s*}", "}", m.group(0))
            fixed = re.sub(r",\s*]", "]", fixed)
            try:
                return json.loads(fixed)
            except Exception:
                _log(f"[LLM] parse err: {e}")
    return {}
