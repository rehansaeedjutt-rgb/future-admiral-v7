"""Future Admiral v7 - Precision fix
Replaces LLM-rounded prices with actual market prices.
"""
from pathlib import Path

# ============================================
# FIX 1: master.py - Full precision rule + actual price override
# ============================================
p = Path("future_admiral_v7/agents/master.py")
c = p.read_text(encoding="utf-8")

# Add precision rule to prompt
old_rules = "STRICT RULES:"
new_rules = """STRICT RULES:
0. PRICE PRECISION: Return FULL price values. Do NOT round. Use all decimals from current_price.
   Example: DOGE=0.08723541, not 0.0872."""

if old_rules in c and "PRICE PRECISION" not in c:
    c = c.replace(old_rules, new_rules, 1)
    print("[OK] master.py - precision rule added")

# Override LLM entry/sl/tp with market-based values if wildly off
old_return = """    return TradeSignal("""
new_return = """    # Override LLM-rounded values with precise market values
    if current_price:
        if not data.get("entry") or abs(float(data.get("entry") or 0) - current_price) / current_price > 0.005:
            data["entry"] = current_price
        if data.get("stop_loss"):
            sl_val = float(data["stop_loss"])
            # Fix rounding: if SL rounds to entry, push away
            if abs(sl_val - current_price) / current_price < 0.002:
                if data.get("bias") == "long":
                    data["stop_loss"] = round(current_price * 0.99, 8)
                elif data.get("bias") == "short":
                    data["stop_loss"] = round(current_price * 1.01, 8)
        # Fix TPs
        tps = data.get("take_profit") or []
        fixed_tps = []
        for tp in tps:
            try:
                tp_val = float(tp)
                if abs(tp_val - current_price) / current_price < 0.001:
                    if data.get("bias") == "long":
                        tp_val = round(current_price * 1.02, 8)
                    elif data.get("bias") == "short":
                        tp_val = round(current_price * 0.98, 8)
                fixed_tps.append(tp_val)
            except Exception:
                pass
        if fixed_tps:
            data["take_profit"] = fixed_tps

    return TradeSignal("""

if old_return in c and "Override LLM-rounded values" not in c:
    c = c.replace(old_return, new_return, 1)
    print("[OK] master.py - market price override added")

p.write_text(c, encoding="utf-8")

# ============================================
# FIX 2: app.py - Replace em-dash with simple dash
# ============================================
p2 = Path("app.py")
c2 = p2.read_text(encoding="utf-8")

# Replace all em-dashes with simple ASCII dash
c2 = c2.replace("\u2014", "—")  # keep as is but ensure consistency
# Actually just avoid replacing — Python handles unicode fine
# The issue was PowerShell escaping, not the em-dash itself

# Add precision formatting helper if not exists
if "_fmt_price" not in c2:
    # Insert helper after imports
    insert_after = "TRADES_FILE = Path(\"paper_trades.csv\")"
    helper = """TRADES_FILE = Path("paper_trades.csv")

def _fmt_price(v):
    \"\"\"Format price with full precision, trimming trailing zeros.\"\"\"
    if v is None:
        return "—"
    try:
        f = float(v)
        # For small numbers (< 1), show more decimals
        if abs(f) < 0.01:
            return f"{f:.8f}".rstrip("0").rstrip(".")
        elif abs(f) < 1:
            return f"{f:.6f}".rstrip("0").rstrip(".")
        elif abs(f) < 100:
            return f"{f:.4f}".rstrip("0").rstrip(".")
        else:
            return f"{f:.2f}"
    except Exception:
        return str(v)"""
    if insert_after in c2:
        c2 = c2.replace(insert_after, helper, 1)
        print("[OK] app.py - _fmt_price helper added")

p2.write_text(c2, encoding="utf-8")

print("")
print("=== All fixes applied ===")
