"""Future Admiral v7 - SPOT Analyst + Action Plan Generator."""
from future_admiral_v7.llm.bridge import ask_json
from future_admiral_v7.schema import SpotSignal, ActionPlan


def _list(v):
    """Coerce string/dict to list. LLM sometimes returns plain string."""
    if v is None: return []
    if isinstance(v, list): return v
    if isinstance(v, str): return [v] if v.strip() else []
    if isinstance(v, dict): return [v]
    return []


def _compact_fund(f):
    if not f or f.get("error"): return "N/A"
    return (f"Rank #{f.get('market_cap_rank')} | MCap ${(f.get('market_cap_usd') or 0)/1e9:.2f}B | "
            f"Supply {f.get('supply_ratio',0)*100:.0f}% | "
            f"24h/7d/30d: {f.get('price_change_24h_pct')}/{f.get('price_change_7d_pct')}/{f.get('price_change_30d_pct')}% | "
            f"Score {f.get('fundamental_score')}/100")


def _compact_deriv(d):
    if not d: return "N/A"
    return (f"Funding {d.get('funding_rate')} | OI 24h {d.get('open_interest_change_24h_pct')}% | "
            f"L/S {d.get('long_short_ratio')} | Top long {d.get('top_trader_long_pct')}% | "
            f"Signal {d.get('institutional_signal')}")


def _compact_tvl(t):
    if not t or not t.get("available"): return "N/A"
    return f"TVL ${(t.get('tvl_now') or 0)/1e6:.1f}M | 7d {t.get('tvl_change_7d_pct')}% | 30d {t.get('tvl_change_30d_pct')}%"


def _compact_fees(f):
    if not f or not f.get("available"): return "N/A"
    return f"Fees24h ${(f.get('total_24h') or 0)/1e3:.1f}K | 7d delta {f.get('change_7d')}%"


def _compact_onchain(o):
    if not o or not o.get("available"): return "N/A"
    return f"{o.get('exchange_netflow_signal')} - {'; '.join(o.get('notes',[]))}"


def _compact_smc(s):
    if not s: return "N/A"
    obs = s.get("order_blocks",[])[:1]; fvgs = s.get("fvgs",[])[:1]
    liq = s.get("liquidity",{})
    return f"OB {obs} | FVG {fvgs} | EqLows {liq.get('equal_lows',[])}"


def run_spot_analyst(symbol, timeframe, ctx_text, analyst_views, current_price,
                     support, resistance, atr, macro, news, fg,
                     fundamentals, derivatives, tvl, fees, onchain, smc):
    bias_summary = ", ".join(f"{v.role}={v.bias}({v.confidence:.1f})" for v in analyst_views)
    sup_str = ", ".join(str(s) for s in support[:3]) if support else "N/A"
    res_str = ", ".join(str(r) for r in resistance[:3]) if resistance else "N/A"

    news_block = ""
    if news and isinstance(news, list):
        for n in news[:3]:
            t = n.get("title", "") if isinstance(n, dict) else str(n)
            news_block += f"* {t[:100]}\n"

    prompt = f"""SPOT ANALYST for {symbol}. Price {current_price}, ATR {atr}, TF {timeframe}.
Support {sup_str} | Resistance {res_str}

FUND: {_compact_fund(fundamentals)}
DERIV: {_compact_deriv(derivatives)}
TVL: {_compact_tvl(tvl)} | FEES: {_compact_fees(fees)}
ONCHAIN: {_compact_onchain(onchain)}
SMC: {_compact_smc(smc)}
MACRO: {macro}
F&G: {fg}
NEWS:
{news_block or 'none'}

ANALYSTS: {bias_summary}

RULES: fund<40 -> no buy_now | inst bearish -> wait | entry zone BELOW current for buy_now
Targets: 1d~0.5-1.5xATR, 5d~1-2xATR, 10d~2-3xATR, 30d~3-5xATR

ACTION PLAN (MUST have exact numbers):
- BUY_NOW: entry + immediate SL
- WAIT_FOR_PRICE: exact buy_trigger_price (specific number)
- HOLD: hold_until_price + sell_if_drops_below
- avoid_above_price: don't chase above this
- why_this_action: 2-3 reasons with numbers

Return ONLY JSON:
{{"recommendation":"buy_now"|"buy_dip"|"wait"|"avoid","confidence":0.0-1.0,
"entry_zone_low":num,"entry_zone_high":num,"stop_loss":num,"invalidation":"text",
"target_1d":num,"target_5d":num,"target_10d":num,"target_30d":num,
"prob_1d":0.0,"prob_5d":0.0,"prob_10d":0.0,"prob_30d":0.0,
"fundamental_score":0-100,"institutional_signal":"bullish"|"neutral"|"bearish",
"institutional_evidence":["..."],"onchain_evidence":["..."],
"catalysts":[{{"event":"...","timeframe":"1d","impact":"high","confidence":0.7}}],
"thesis":"2 sentences","reasons":["r1","r2"],"risks":["rk1"],"news_summary":["n1"],
"action_plan":{{"action":"BUY_NOW"|"WAIT_FOR_PRICE"|"HOLD"|"SELL_AT_PRICE"|"AVOID",
"headline":"clear one line","plain_explanation":"2 lines why",
"buy_trigger_price":num|null,"buy_trigger_condition":"text","avoid_above_price":num|null,
"hold_until_price":num|null,"sell_if_drops_below":num|null,
"wait_days_min":0,"wait_days_max":0,"sell_by_day":0,"time_explanation":"text",
"why_this_action":["r1 with number","r2 with number"],"what_would_change_mind":"trigger"}}}}"""

    try:
        data = ask_json(prompt, profile="quick") or {}
    except Exception as e:
        data = {"_error": str(e)}

    if fundamentals and not fundamentals.get("error"):
        data.setdefault("fundamental_score", fundamentals.get("fundamental_score", 50))
    if derivatives:
        data.setdefault("institutional_signal", derivatives.get("institutional_signal", "neutral"))

    return _build_signal(symbol, timeframe, current_price, data, atr, support, resistance)


def _build_signal(symbol, timeframe, current_price, data, atr, support, resistance):
    def _f(v, d=None):
        try: return float(v) if v is not None else d
        except Exception: return d
    def _i(v, d=0):
        try: return int(float(v)) if v is not None else d
        except Exception: return d

    rec = data.get("recommendation", "wait")
    if rec not in ("buy_now", "buy_dip", "wait", "avoid"): rec = "wait"
    conf = _f(data.get("confidence"), 0.0) or 0.0
    fund = _i(data.get("fundamental_score"), 50)
    ez_hi = _f(data.get("entry_zone_high"))

    if conf < 0.5 and rec in ("buy_now", "buy_dip"): rec = "wait"
    if fund < 40 and rec == "buy_now": rec = "wait"
    if current_price and ez_hi and rec == "buy_now" and ez_hi > current_price * 1.02:
        rec = "buy_dip"

    inst = data.get("institutional_signal", "neutral")
    if inst not in ("bullish", "neutral", "bearish"): inst = "neutral"

    ap_raw = data.get("action_plan") or {}
    if not ap_raw or not ap_raw.get("action"):
        ap_raw = _fallback_action_plan(rec, current_price, atr, support, resistance, fund, inst)

    ap_action = ap_raw.get("action", "AVOID")
    valid_actions = ("BUY_NOW","WAIT_FOR_PRICE","HOLD","SELL_NOW","SELL_AT_PRICE",
                     "SELL_BY_TIME","AVOID","SET_ALERT")
    if ap_action not in valid_actions: ap_action = "AVOID"

    action_plan = ActionPlan(
        action=ap_action,
        headline=ap_raw.get("headline", ""),
        plain_explanation=ap_raw.get("plain_explanation", ""),
        buy_trigger_price=_f(ap_raw.get("buy_trigger_price")),
        buy_trigger_condition=ap_raw.get("buy_trigger_condition", "") if isinstance(ap_raw.get("buy_trigger_condition"), str) else "",
        avoid_above_price=_f(ap_raw.get("avoid_above_price")),
        hold_until_price=_f(ap_raw.get("hold_until_price")),
        sell_if_drops_below=_f(ap_raw.get("sell_if_drops_below")),
        wait_days_min=_i(ap_raw.get("wait_days_min"), 0),
        wait_days_max=_i(ap_raw.get("wait_days_max"), 0),
        sell_by_day=_i(ap_raw.get("sell_by_day"), 0),
        time_explanation=ap_raw.get("time_explanation", "") if isinstance(ap_raw.get("time_explanation"), str) else "",
        why_this_action=_list(ap_raw.get("why_this_action")),
        what_would_change_mind=ap_raw.get("what_would_change_mind", "") if isinstance(ap_raw.get("what_would_change_mind"), str) else "",
    )

    return SpotSignal(
        symbol=symbol, timeframe=timeframe, current_price=current_price,
        recommendation=rec, confidence=conf,
        entry_zone_low=_f(data.get("entry_zone_low")),
        entry_zone_high=ez_hi, stop_loss=_f(data.get("stop_loss")),
        invalidation=data.get("invalidation", "") if isinstance(data.get("invalidation"), str) else "",
        target_1d=_f(data.get("target_1d")), target_5d=_f(data.get("target_5d")),
        target_10d=_f(data.get("target_10d")), target_30d=_f(data.get("target_30d")),
        prob_1d=_f(data.get("prob_1d"), 0.0) or 0.0,
        prob_5d=_f(data.get("prob_5d"), 0.0) or 0.0,
        prob_10d=_f(data.get("prob_10d"), 0.0) or 0.0,
        prob_30d=_f(data.get("prob_30d"), 0.0) or 0.0,
        fundamental_score=fund, institutional_signal=inst,
        institutional_evidence=_list(data.get("institutional_evidence")),
        onchain_evidence=_list(data.get("onchain_evidence")),
        catalysts=_list(data.get("catalysts")),
        thesis=data.get("thesis", "") if isinstance(data.get("thesis"), str) else "",
        reasons=_list(data.get("reasons")),
        risks=_list(data.get("risks")),
        news_summary=_list(data.get("news_summary")),
        action_plan=action_plan,
    )


def _fallback_action_plan(rec, price, atr, support, resistance, fund, inst):
    if not price:
        return {"action":"AVOID","headline":"Insufficient data",
                "plain_explanation":"Wait for next update",
                "why_this_action":["Price data missing"],
                "what_would_change_mind":"Price becomes available"}

    if rec in ("buy_now", "buy_dip") and fund >= 50 and inst != "bearish":
        ez_lo = round(price * 0.99, 4)
        ez_hi = round(price * 1.001, 4)
        trigger = round(ez_lo, 4)
        return {
            "action": "BUY_NOW" if rec == "buy_now" else "WAIT_FOR_PRICE",
            "headline": f"Buy zone ${ez_lo}-${ez_hi}" if rec == "buy_now" else f"Wait for pullback to ${trigger}",
            "plain_explanation": f"Fundamental score {fund}/100, institutional signal {inst}. Entry near support.",
            "buy_trigger_price": trigger if rec == "buy_dip" else None,
            "buy_trigger_condition": f"if holds above {trigger} for 2-4h" if rec == "buy_dip" else "",
            "avoid_above_price": round(price * 1.03, 4),
            "wait_days_min": 1 if rec == "buy_dip" else 0,
            "wait_days_max": 4 if rec == "buy_dip" else 1,
            "time_explanation": "Short-term entry window",
            "why_this_action": [
                f"Fundamental score {fund}/100",
                f"Current price {price} near support",
                f"Institutional signal: {inst}",
            ],
            "what_would_change_mind": f"Close below {round(price * 0.97, 4)} invalidates",
        }

    if fund >= 50 and inst == "bullish":
        return {"action":"SET_ALERT",
                "headline": f"Watch {price} - wait for confirmation",
                "plain_explanation":"Signals mixed. Wait for stronger setup.",
                "avoid_above_price": round(price * 1.03, 4),
                "why_this_action":[f"Fund {fund}/100","Mixed signals"],
                "what_would_change_mind":"Clear breakout or breakdown"}

    if fund < 40 or inst == "bearish":
        return {"action":"AVOID",
                "headline":"Avoid - weak fundamentals or bearish flow",
                "plain_explanation": f"Fund score {fund}/100, institutional {inst}. Risk too high.",
                "why_this_action":[f"Fund {fund}/100", f"Institutional {inst}"],
                "what_would_change_mind":"Fundamental improvement + bullish flow"}

    return {"action":"WAIT","headline":"No clear edge - wait",
            "plain_explanation":"Market conditions unclear. Observe only.",
            "wait_days_min":2,"wait_days_max":5,
            "time_explanation":"Need more data for conviction",
            "why_this_action":["Mixed signals"],
            "what_would_change_mind":"Clear direction"}


def run_spot_debate(symbol, ctx_text, spot_view, current_price, support, resistance):
    sup_str = ", ".join(str(s) for s in support[:3]) if support else "N/A"
    res_str = ", ".join(str(r) for r in resistance[:3]) if resistance else "N/A"

    bull_prompt = f"""SPOT BULL for {symbol}. Price {current_price} | Sup {sup_str} | Res {res_str}
Rec: {spot_view.recommendation} | Fund: {spot_view.fundamental_score}/100 | Inst: {spot_view.institutional_signal}
Give strongest honest bull case in 2-3 sentences.
JSON only: {{"thesis":"...","confidence":0.0-1.0}}"""

    bear_prompt = f"""SPOT BEAR for {symbol}. Price {current_price} | Sup {sup_str} | Res {res_str}
Rec: {spot_view.recommendation} | Fund: {spot_view.fundamental_score}/100
Give strongest honest bear case in 2-3 sentences.
JSON only: {{"thesis":"...","confidence":0.0-1.0}}"""

    try:
        bull = ask_json(bull_prompt, profile="quick") or {}
    except Exception:
        bull = {}
    try:
        bear = ask_json(bear_prompt, profile="quick") or {}
    except Exception:
        bear = {}

    return {
        "bull": {"thesis": bull.get("thesis", "") if isinstance(bull.get("thesis"), str) else "",
                 "confidence": float(bull.get("confidence", 0.5)) if bull.get("confidence") else 0.5},
        "bear": {"thesis": bear.get("thesis", "") if isinstance(bear.get("thesis"), str) else "",
                 "confidence": float(bear.get("confidence", 0.5)) if bear.get("confidence") else 0.5},
    }
