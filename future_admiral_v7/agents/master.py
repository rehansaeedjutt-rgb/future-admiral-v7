from future_admiral_v7.llm.bridge import ask_json
from future_admiral_v7.schema import TradeSignal

def admiral_final(symbol, timeframe, context, analyst_views, bull, bear, risk_view):
    bias_summary = ", ".join(f"{v.role}={v.bias}({v.confidence:.1f})" for v in analyst_views)
    prompt = f"""You are Admiral (CIO). Decide trade for {symbol} {timeframe}.

ANALYSTS: {bias_summary}
BULL: {bull.get('thesis','')[:200]}
BEAR: {bear.get('thesis','')[:200]}

Return EXACTLY this JSON:
{{
  "bias": "long" or "short" or "neutral",
  "confidence": 0.65,
  "entry": 64000,
  "stop_loss": 63000,
  "take_profit": [65000, 67000],
  "position_size_pct": 1.0,
  "leverage": 3
}}

Rules:
- Analysts disagree -> bias="neutral", confidence<0.4
- stop_loss ALWAYS for long/short
- Only JSON"""
    data = ask_json(prompt, profile="quick")
    try:
        return TradeSignal(symbol=symbol, timeframe=timeframe,
                           bias=data.get("bias", "neutral"),
                           confidence=float(data.get("confidence", 0.3)),
                           entry=data.get("entry"), stop_loss=data.get("stop_loss"),
                           take_profit=data.get("take_profit") or [],
                           position_size_pct=float(data.get("position_size_pct", 0)),
                           leverage=float(data.get("leverage", 1)),
                           reasons=[f"Analysts: {bias_summary}"], risks=[])
    except Exception as e:
        return TradeSignal(symbol=symbol, timeframe=timeframe, bias="neutral",
                           confidence=0.2, reasons=[f"err: {e}"], risks=[])
