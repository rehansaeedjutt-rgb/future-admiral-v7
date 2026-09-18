from future_admiral_v7.llm.bridge import ask_json
from future_admiral_v7.schema import AnalystView


def run_analyst(role, context, focus_prompt, profile="quick"):
    prompt = f"""You are a {role} at an institutional trading desk.

REAL MARKET DATA:
{context}

FOCUS: {focus_prompt}

Analyze using the ACTUAL numbers above. Consider:
- Current price vs support/resistance
- Trend (EMA stack), momentum (RSI, MACD)
- Volume behavior, ATR (volatility)
- News and sentiment if provided

Return ONLY this JSON:
{{"bias": "bullish" or "bearish" or "neutral", "confidence": 0.65, "score": 5, "key_points": ["point using real numbers"], "risks": ["risk"]}}

Rules:
- Use ACTUAL prices from data (never invent numbers)
- bias must reflect data direction, not default to neutral
- score: -10 (max bearish) to +10 (max bullish)
- key_points: reference specific prices/indicators from data
- Only JSON, no prose"""

    data = ask_json(prompt, profile=profile)
    try:
        bias = str(data.get("bias", "neutral")).lower()
        if bias not in ("bullish", "bearish", "neutral"):
            bias = "neutral"
        return AnalystView(
            role=role,
            bias=bias,
            confidence=float(data.get("confidence", 0.3)),
            score=float(data.get("score", 0)),
            key_points=data.get("key_points") or [f"bias={bias}"],
            risks=data.get("risks") or [],
        )
    except Exception as e:
        return AnalystView(role=role, bias="neutral", confidence=0.3, score=0,
                           key_points=[f"parse err: {e}"], risks=[])
