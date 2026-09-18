"""Future Admiral v7 - Debate Engine (SPOT + FUTURES, full data)."""
import concurrent.futures, json, sys
from future_admiral_v7.config import cfg
from future_admiral_v7.data.market import MarketData
from future_admiral_v7.data.news import fetch_news
from future_admiral_v7.data.macro import fetch_macro
from future_admiral_v7.data.sentiment import fear_greed
from future_admiral_v7.data.coingecko import fetch_fundamentals
from future_admiral_v7.data.defillama import fetch_tvl, fetch_fees
from future_admiral_v7.data.derivatives import fetch_all_derivatives
from future_admiral_v7.data.onchain import fetch_exchange_flows
from future_admiral_v7.features.indicators import multi_tf_summary, market_structure
from future_admiral_v7.features.smc import smc_summary
from future_admiral_v7.agents import analysts, debaters
from future_admiral_v7.agents.master import admiral_final
from future_admiral_v7.agents.spot_analyst import run_spot_analyst, run_spot_debate
from future_admiral_v7.risk.engine import finalize_signal
from future_admiral_v7.audit.logger import log_event

def _p(msg):
    print(f"[ENGINE] {msg}", flush=True); sys.stdout.flush()

def _safe(fn, default, label, errors):
    try: return fn()
    except Exception as e:
        errors.append(f"{label}: {e}"); return default

def _pick(tf_map, tf):
    if not tf_map: return None
    if tf in tf_map and tf_map[tf] is not None and not tf_map[tf].empty:
        return tf_map[tf]
    for df in tf_map.values():
        if df is not None and not df.empty: return df
    return None

def _build_context(symbol, timeframe, tf_sum, structure, news, macro, fg, ob, fo):
    primary = tf_sum.get(timeframe) or (list(tf_sum.values())[0] if tf_sum else {})
    lines = [f"Symbol: {symbol}  TF: {timeframe}",
             f"Current: {structure.get('last_close', primary.get('close'))}",
             f"High: {structure.get('recent_high')}  Low: {structure.get('recent_low')}",
             f"Support: {structure.get('support', [])}",
             f"Resistance: {structure.get('resistance', [])}",
             f"Vol ratio: {structure.get('volume_ratio')}",
             "-- Multi-TF --"]
    for tf in ["1m","5m","15m","1h","4h","1d"]:
        if tf in tf_sum:
            f = tf_sum[tf]
            lines.append(f"{tf}: close={f.get('close')} trend={f.get('trend')} rsi={f.get('rsi')} atr={f.get('atr')}")
    if macro: lines.append(f"Macro: {json.dumps(macro, default=str)}")
    if fg: lines.append(f"F&G: {fg}")
    if ob: lines.append(f"OB: {ob}")
    if fo: lines.append(f"Funding/OI: {fo}")
    if news:
        lines.append("-- News --")
        for n in (news[:5] if isinstance(news, list) else []):
            t = n.get("title","") if isinstance(n, dict) else str(n)
            lines.append(f"* {t[:120]}")
    return "\n".join(lines)

def run_debate(symbol, timeframe="15m", ui=None):
    errors = []
    def say(msg):
        _p(msg)
        try:
            if ui is not None: ui.write(msg)
        except Exception: pass

    say("Step 1/7: Data ingestion (12 sources)")
    md = MarketData()
    try: kind = "crypto" if md.is_crypto(symbol) else "stock"
    except Exception: kind = "crypto"

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        f_tf = ex.submit(_safe, lambda: md.multi_tf(symbol, kind), {}, "multi_tf", errors)
        f_news = ex.submit(_safe, lambda: fetch_news(symbol), [], "news", errors)
        f_macro = ex.submit(_safe, lambda: fetch_macro(), {}, "macro", errors)
        f_fg = ex.submit(_safe, lambda: fear_greed(), {}, "fg", errors)
        f_ob = ex.submit(_safe, lambda: md.orderbook(symbol), {}, "ob", errors)
        f_fo = ex.submit(_safe, lambda: md.funding_oi(symbol), {}, "fo", errors)
        f_fund = ex.submit(_safe, lambda: fetch_fundamentals(symbol), {}, "fund", errors)
        f_deriv = ex.submit(_safe, lambda: fetch_all_derivatives(symbol), {}, "deriv", errors)
        f_tvl = ex.submit(_safe, lambda: fetch_tvl(symbol), {}, "tvl", errors)
        f_fees = ex.submit(_safe, lambda: fetch_fees(symbol), {}, "fees", errors)
        f_oc = ex.submit(_safe, lambda: fetch_exchange_flows(symbol), {}, "onchain", errors)
        tf_map = f_tf.result(); news = f_news.result(); macro = f_macro.result()
        fg = f_fg.result(); ob = f_ob.result(); fo = f_fo.result()
        fundamentals = f_fund.result(); deriv = f_deriv.result()
        tvl = f_tvl.result(); fees = f_fees.result(); onchain = f_oc.result()

    if not tf_map:
        empty_f = {"symbol":symbol,"timeframe":timeframe,"bias":"neutral",
                   "confidence":0.0,"trade_type":"none","reasons":[f"No data: {errors}"],
                   "risks":[],"errors":errors}
        empty_s = {"symbol":symbol,"recommendation":"wait","confidence":0.0,
                   "thesis":f"No data: {errors}"}
        return {"futures": empty_f, "spot": empty_s, "errors": errors}

    say("Step 2/7: Features + SMC")
    tf_sum = _safe(lambda: multi_tf_summary(tf_map), {}, "tf_sum", errors)
    primary = _pick(tf_map, timeframe)
    structure = _safe(lambda: market_structure(primary), {}, "structure", errors) if primary is not None else {}
    smc = _safe(lambda: smc_summary(primary), {}, "smc", errors) if primary is not None else {}

    current_price = structure.get("last_close") or (tf_sum.get(timeframe, {}) or {}).get("close")
    atr = (tf_sum.get(timeframe, {}) or {}).get("atr") or 0
    support = structure.get("support", []) or []
    resistance = structure.get("resistance", []) or []

    ctx_text = _build_context(symbol, timeframe, tf_sum, structure, news, macro, fg, ob, fo)

    say("Step 3/7: Analyst panel")
    from future_admiral_v7.schema import AnalystView
    views = []
    analyst_fns = [
        ("Technical Analyst", analysts.technical_agent, "Trend, RSI/MACD, S/R, ATR."),
        ("News Analyst", analysts.news_agent, "Recent news impact."),
        ("Risk Officer", analysts.risk_agent, "Downside risk, volatility."),
    ]
    for role, fn, focus in analyst_fns:
        _p(f"  -> {role}")
        try:
            v = fn(ctx_text, focus); views.append(v)
            _p(f"  <- {role}: {v.bias} ({v.confidence:.2f})")
        except Exception as e:
            errors.append(f"{role}: {e}")
            views.append(AnalystView(role=role, bias="neutral", confidence=0.3, score=0, key_points=[], risks=[]))

    say("Step 4/7: Futures Bull/Bear debate")
    try: bull_f = debaters.bull_round1(views, ctx_text)
    except Exception as e:
        errors.append(f"fut_bull: {e}"); bull_f = {"thesis":"","confidence":0.5,"score":0}
    try: bear_f = debaters.bear_round1(views, ctx_text)
    except Exception as e:
        errors.append(f"fut_bear: {e}"); bear_f = {"thesis":"","confidence":0.5,"score":0}

    say("Step 5/7: Futures Admiral")
    try:
        futures_sig = admiral_final(symbol, timeframe, ctx_text, views, bull_f, bear_f, views[-1],
                                     support, resistance, current_price, atr)
    except Exception as e:
        errors.append(f"admiral: {e}")
        from future_admiral_v7.schema import TradeSignal
        futures_sig = TradeSignal(symbol=symbol, timeframe=timeframe, bias="neutral",
                                  confidence=0.2, reasons=[f"admiral err: {e}"], risks=[],
                                  current_price=current_price)
    try:
        futures_sig = finalize_signal(futures_sig, equity=cfg.ACCOUNT_EQUITY,
                                       max_risk_pct=cfg.MAX_RISK_PER_TRADE)
    except Exception as e:
        errors.append(f"risk: {e}")
    futures_sig.agents_summary = {"analysts": [v.model_dump() for v in views],
                                   "bull": bull_f, "bear": bear_f,
                                   "context": {"structure": structure}}

    say("Step 6/7: SPOT analyst")
    try:
        spot_sig = run_spot_analyst(symbol, timeframe, ctx_text, views, current_price,
                                     support, resistance, atr, macro, news, fg,
                                     fundamentals, deriv, tvl, fees, onchain, smc)
    except Exception as e:
        errors.append(f"spot_analyst: {e}")
        from future_admiral_v7.schema import SpotSignal
        spot_sig = SpotSignal(symbol=symbol, timeframe=timeframe, current_price=current_price,
                              recommendation="wait", thesis=f"error: {e}")

    say("Step 7/7: SPOT Bull/Bear debate")
    try:
        spot_debate = run_spot_debate(symbol, ctx_text, spot_sig, current_price, support, resistance)
        spot_sig.bull_thesis = spot_debate["bull"]["thesis"]
        spot_sig.bull_confidence = spot_debate["bull"]["confidence"]
        spot_sig.bear_thesis = spot_debate["bear"]["thesis"]
        spot_sig.bear_confidence = spot_debate["bear"]["confidence"]
        if spot_sig.bull_confidence > spot_sig.bear_confidence + 0.15:
            spot_sig.verdict = "Bull case stronger"
        elif spot_sig.bear_confidence > spot_sig.bull_confidence + 0.15:
            spot_sig.verdict = "Bear case stronger"
        else:
            spot_sig.verdict = "Balanced — cautious stance"
    except Exception as e:
        errors.append(f"spot_debate: {e}")

    spot_sig.agents_summary = {"analysts": [v.model_dump() for v in views],
                                "context": {"structure": structure, "support": support, "resistance": resistance}}

    try: log_event("futures_signal", futures_sig.model_dump())
    except Exception: pass
    try: log_event("spot_signal", spot_sig.model_dump())
    except Exception: pass

    fut_out = futures_sig.model_dump(); fut_out["errors"] = errors
    spot_out = spot_sig.model_dump(); spot_out["errors"] = errors
    return {"futures": fut_out, "spot": spot_out, "errors": errors}
