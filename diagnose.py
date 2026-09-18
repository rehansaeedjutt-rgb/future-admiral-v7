import sys, os, traceback

print("=" * 60)
print("FUTURE ADMIRAL v7 - DIAGNOSTIC")
print("=" * 60)
print(f"\n[1] Python: {sys.version}")
print(f"    Executable: {sys.executable}")

print("\n[2] Checking imports...")
for name, mod in [("streamlit","streamlit"),("pandas","pandas"),("numpy","numpy"),("ccxt","ccxt"),("yfinance","yfinance"),("pandas_ta","pandas_ta"),("pydantic","pydantic"),("langchain_openai","langchain_openai"),("dotenv","dotenv"),("requests","requests"),("feedparser","feedparser"),("markdown","markdown")]:
    try:
        __import__(mod)
        print(f"    OK   {name}")
    except Exception as e:
        print(f"    FAIL {name}: {e}")

print("\n[3] Checking future_admiral_v7 package...")
try:
    import future_admiral_v7
    print(f"    OK   at: {future_admiral_v7.__file__}")
except Exception as e:
    print(f"    FAIL: {e}")

print("\n[4] Checking Ollama...")
try:
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])] if r.status_code==200 else []
    print(f"    OK   Models: {models}")
except Exception as e:
    print(f"    FAIL: {e}")

print("\n[5] Trying full pipeline...")
try:
    from future_admiral_v7.debate.engine import run_debate
    result = run_debate("BTC/USDT", "15m", ui=None)
    print(f"    OK   Bias: {result.get('bias')}, Conf: {result.get('confidence')}")
except Exception as e:
    print(f"    FAIL:")
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
