from future_admiral_v7.llm.bridge import ask_json

def _debate(role, views, opponent, context):
    views_text = ", ".join(f"{v.role}={v.bias}" for v in views)
    prompt = f"""You are {role} in trading debate.

ANALYSTS: {views_text}
DATA: {context[:300]}

Return ONLY this JSON:
{{"thesis": "one sentence", "confidence": 0.6, "score": 4}}"""
    data = ask_json(prompt, profile="quick")
    return {"thesis": data.get("thesis", ""), "key_evidence": [],
            "confidence": float(data.get("confidence", 0.5)),
            "score": float(data.get("score", 0))}

def bull_round1(views, context): return _debate("Bull", views, None, context)
def bear_round1(views, context): return _debate("Bear", views, None, context)
def bull_round2(views, b, br, context): return _debate("Bull", views, br, context)
def bear_round2(views, b, br, context): return _debate("Bear", views, b, context)
