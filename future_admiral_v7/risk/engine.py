from __future__ import annotations

from future_admiral_v7.schema import TradeSignal


def position_size(equity: float, risk_pct: float, entry: float, stop_loss: float) -> float:
    risk_amount = equity * (risk_pct / 100.0)
    per_unit = abs(entry - stop_loss)
    if per_unit == 0:
        return 0.0
    return risk_amount / per_unit


def finalize_signal(sig: TradeSignal, equity: float, max_risk_pct: float) -> TradeSignal:
    if sig.bias == "neutral":
        sig.position_size_pct = 0.0
        sig.leverage = 1.0
        sig.risk_reward = 0.0
        return sig

    if not sig.entry or not sig.stop_loss:
        sig.bias = "neutral"
        sig.confidence = min(sig.confidence, 0.3)
        sig.reasons.append("Missing entry or stop loss, so signal downgraded to neutral.")
        sig.position_size_pct = 0.0
        return sig

    sig.position_size_pct = round(min(max_risk_pct, max(sig.position_size_pct or 0.5, 0.25)), 2)
    if sig.take_profit:
        tp = sig.take_profit[0]
        reward = abs(tp - sig.entry)
        risk = abs(sig.entry - sig.stop_loss)
        sig.risk_reward = round(reward / risk, 2) if risk else 0.0
    sig.leverage = max(1.0, min(sig.leverage or 1.0, 10.0))
    return sig
