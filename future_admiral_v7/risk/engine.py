from future_admiral_v7.schema import TradeSignal


def position_size(equity, risk_pct, entry, sl):
    risk_amt = equity * (risk_pct / 100.0)
    per_unit = abs(entry - sl)
    return risk_amt / per_unit if per_unit else 0.0


def finalize_signal(sig: TradeSignal, equity: float, max_risk_pct: float) -> TradeSignal:
    # Neutral / none — no trade
    if sig.bias == "neutral" or sig.trade_type == "none":
        sig.position_size_pct = 0.0
        sig.leverage = 1.0
        sig.risk_reward = 0.0
        return sig

    # Must have entry + SL
    if not sig.entry or not sig.stop_loss:
        sig.bias = "neutral"
        sig.trade_type = "none"
        sig.confidence = min(sig.confidence, 0.3)
        sig.reasons.append("Missing entry/SL → downgraded")
        sig.position_size_pct = 0.0
        return sig

    entry = float(sig.entry)
    sl = float(sig.stop_loss)

    # Validate SL direction
    if sig.bias == "long" and sl >= entry:
        sig.bias = "neutral"
        sig.trade_type = "none"
        sig.reasons.append("Invalid SL for long")
        sig.position_size_pct = 0.0
        return sig
    if sig.bias == "short" and sl <= entry:
        sig.bias = "neutral"
        sig.trade_type = "none"
        sig.reasons.append("Invalid SL for short")
        sig.position_size_pct = 0.0
        return sig

    # Clean take_profit: remove TPs on wrong side + dedupe
    clean_tp = []
    for tp in (sig.take_profit or []):
        try:
            tp = float(tp)
        except Exception:
            continue
        if sig.bias == "long" and tp > entry:
            if not clean_tp or abs(tp - clean_tp[-1]) / max(clean_tp[-1], 1) > 0.001:
                clean_tp.append(tp)
        elif sig.bias == "short" and tp < entry:
            if not clean_tp or abs(tp - clean_tp[-1]) / max(clean_tp[-1], 1) > 0.001:
                clean_tp.append(tp)

    sig.take_profit = clean_tp[:3]

    # R:R based on FIRST valid TP
    risk = abs(entry - sl)
    if not sig.take_profit or risk == 0:
        sig.bias = "neutral"
        sig.trade_type = "none"
        sig.reasons.append("No valid TP → downgraded")
        sig.position_size_pct = 0.0
        return sig

    reward = abs(sig.take_profit[0] - entry)
    rr = round(reward / risk, 2)
    sig.risk_reward = rr

    # Enforce min R:R
    MIN_RR = 1.5
    if rr < MIN_RR:
        sig.bias = "neutral"
        sig.trade_type = "none"
        sig.confidence = min(sig.confidence, 0.35)
        sig.reasons.append(f"R:R {rr} < {MIN_RR} → no trade")
        sig.position_size_pct = 0.0
        return sig

    # Size + leverage caps
    risk_pct = min(max_risk_pct, max(sig.position_size_pct or max_risk_pct, 0.25))
    sig.position_size_pct = round(risk_pct, 2)
    sig.leverage = max(1.0, min(sig.leverage or 1.0, 5.0))
    return sig
