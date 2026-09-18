from future_admiral_v7.llm.bridge import ask_json
from future_admiral_v7.schema import AnalystView

def run_analyst(role, context, focus_prompt, profile="quick"):
    prompt = f"""You are a {role}. Analyze briefly:
{context[:400]}

FOCUS: {focus_prompt}

Return EXACTLY this JSON:
{{"bias": "bullish" or "bearish" or "neutral", "confidence": 0.7, "score": 5}}

bias = view. confidence = 0.0-1.0. score = -10 to +10.
Only JSON, no explanation."""
    data = ask_json(prompt, profile=profile)
    try:
        return AnalystView(role=role, bias=data.get("bias", "neutral"),
                           confidence=float(data.get("confidence", 0.3)),
                           score=float(data.get("score", 0)),
                           key_points=[f"bias={data.get('bias')}"], risks=[])
    except Exception as e:
        return AnalystView(role=role, bias="neutral", confidence=0.3, score=0,
                           key_points=[f"err: {e}"], risks=[])
