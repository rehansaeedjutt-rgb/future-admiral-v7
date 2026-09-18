import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class Config:
    OLLAMA_URL = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434/v1"
    QUICK_MODEL = os.getenv("OLLAMA_QUICK_MODEL") or "qwen2.5:0.5b"
    DEEP_MODEL = os.getenv("OLLAMA_DEEP_MODEL") or "qwen2.5:0.5b"

    DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL") or ""

    ACCOUNT_EQUITY = float(os.getenv("ACCOUNT_EQUITY") or "10000")
    MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE") or "1.0")
    MAX_PORTFOLIO_HEAT = float(os.getenv("MAX_PORTFOLIO_HEAT") or "6.0")

    TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
    HOME = os.path.expanduser("~/.future_admiral")
    AUDIT_LOG = os.path.join(HOME, "audit.jsonl")

    @classmethod
    def ensure_dirs(cls):
        os.makedirs(cls.HOME, exist_ok=True)
        os.makedirs("reports", exist_ok=True)

cfg = Config()
cfg.ensure_dirs()