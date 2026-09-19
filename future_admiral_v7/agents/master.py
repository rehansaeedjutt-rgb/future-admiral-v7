from future_admiral_v7.llm.bridge import ask_json
from future_admiral_v7.schema import TradeSignal


def admiral_final(symbol, timeframe, context, analyst_views, bull, bear, risk_view,
                  support, resistance, current_price, atr):
    bias_summary = ", ".join(f"{v.role}={v.bias}({v.confidence:.1f})" for v in analyst_views)
    sup_str = ", ".join(str(s) for s in support[:3]) if support else "N/A"
    res_str = ", ".join(str(r) for r in resistance[:3]) if resistance else "N/A"

    # Pre-compute ATR-based risk distances (institutional)
    atr = atr or 0
    if current_price and atr and atr > 0:
        sl_long = round(current_price - 1.5 * atr, 4)
        sl_short = round(current_price + 1.5 * atr, 4)
        tp_long_1 = round(current_price + 2.25 * atr, 4)   # 1.5x risk
        tp_long_2 = round(current_price + 3.75 * atr, 4)   # 2.5x risk
        tp_short_1 = round(current_price - 2.25 * atr, 4)
        tp_short_2 = round(current_price - 3.75 * atr, 4)
    else:
        sl_long = sl_short = tp_long_1 = tp_long_2 = tp_short_1 = tp_short_2 = None

    # Duration rules based on timeframe
    duration_map = {
        "1m": "15 minutes to 1 hour",
        "5m": "30 minutes to 2 hours",
        "15m": "1 to 4 hours",
        "1h": "4 to 24 hours",
        "4h": "1 to 3 days",
        "1d": "3 to 14 days",
        "1w": "2 to 8 weeks",
    }
    duration_rule = duration_map.get(timeframe, "1 to 4 hours")

    prompt = f"""You are the ADMIRAL (CIO). Make the FINAL trading decision.

SYMBOL: {symbol}  TIMEFRAME: {timeframe}
CURRENT PRICE: {current_price}
ATR (volatility): {atr}
SUPPORT: {sup_str}
RESISTANCE: {res_str}

ANALYSTS: {bias_summary}
BULL: {bull.get('thesis','')[:150]}
BEAR: {bear.get('thesis','')[:150]}

ATR-BASED REFERENCE LEVELS (use these — R:R already >= 1.5):
- If LONG: entry≈{current_price}, SL≈{sl_long} (1.5x ATR below), TP1≈{tp_long_1}, TP2≈{tp_long_2}
- If SHORT: entry≈{current_price}, SL≈{sl_short} (1.5x ATR above), TP1≈{tp_short_1}, TP2≈{tp_short_2}

STRICT RULES:
0. PRICE PRECISION: Return FULL price values. Do NOT round or truncate.
   Example: DOGE=0.08723541, not 0.0872. SHIB=0.00001845, not 0.00001.
   Use ALL available decimal places from the current_price field.
1. Use the ATR-based levels above — they already give R:R >= 1.5.
2. If most analysts bullish → LONG. If bearish → SHORT. If split → neutral.
3. NEVER set SL further than 2.5x ATR from entry.
4. TP1 must give R:R >= 1.5. TP2 can be further.
5. duration_hours: 15m→2-8, 1h→8-48, 4h→24-120, 1d→72-720.
6. trade_type: "futures" if directional & duration<=48h, "spot" if bullish & longer, else "none".

Return ONLY JSON:
{{
  "bias": "long"|"short"|"neutral",
  "confidence": 0.0-1.0,
  "trade_type": "spot"|"futures"|"none",
  "duration_hours": number,
  "reasoning_duration": "short text",
  "entry": number,
  "stop_loss": number,
  "take_profit": [number, number],
  "invalidation": "text",
  "position_size_pct": 0.5-2.0,
  "leverage": 1-5,
  "reasons": ["reason with number", "reason"],
  "risks": ["risk", "risk"]
}}"""

    data = ask_json(prompt, profile="quick")

    try:
        tp = data.get("take_profit") or []
        if not isinstance(tp, list):
            tp = [tp] if tp else []

        # Override LLM-rounded values with precise market values
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

    return TradeSignal(
            symbol=symbol, timeframe=timeframe,
            bias=data.get("bias", "neutral"),
            confidence=float(data.get("confidence", 0.3)),
            trade_type=data.get("trade_type", "none"),
            duration_hours=float(data.get("duration_hours", 0)),
            reasoning_duration=data.get("reasoning_duration", ""),
            current_price=current_price,
            entry=data.get("entry"),
            stop_loss=data.get("stop_loss"),
            take_profit=[float(x) for x in tp if x],
            invalidation=data.get("invalidation", ""),
            support=support[:3],
            resistance=resistance[:3],
            position_size_pct=float(data.get("position_size_pct", 0)),
            leverage=float(data.get("leverage", 1)),
            reasons=data.get("reasons") or [f"Analysts: {bias_summary}"],
            risks=data.get("risks") or [],
        )
    except Exception as e:
        return TradeSignal(symbol=symbol, timeframe=timeframe, bias="neutral",
                           confidence=0.2, reasons=[f"admiral err: {e}"], risks=[],
                           current_price=current_price)
