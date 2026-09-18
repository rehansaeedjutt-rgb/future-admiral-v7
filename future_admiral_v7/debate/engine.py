"""Future Admiral v7 - Debate Engine (rich context, real prices)"""
import concurrent.futures, json, sys
from future_admiral_v7.config import cfg
from future_admiral_v7.data.market import MarketData
from future_admiral_v7.data.news import fetch_news
from future_admiral_v7.data.macro import fetch_macro
from future_admiral_v7.data.sentiment import fear_greed
from future_admiral_v7.features.indicators import multi_tf_summary, market_structure
from future_admiral_v7.agents import analysts, debaters
from future_admiral_v7.agents.master import admiral_final
from future_admiral_v7.risk.engine import finalize_signal
from future_admiral_v7.audit.logger import log_event


def _p(msg):
    print(f"[ENGINE] {msg}", flush=True); sys.stdout.flush()


def _safe(fn, default, label, errors):
    try:
        return fn()
    except Exception as e:
        errors.append(f"{label}: {e}")
        return default


def _pick(tf_map, tf):
    if not tf_map: return None
    if tf in tf_map and tf_map[tf] is not None and not tf_map[tf].empty:
        return tf_map[tf]
    for df in tf_map.values():
        if df is not None and not df.empty:
            return df
    return None


def _build_context(symbol, timeframe, tf_sum, structure, news, macro, fg, ob, fo):
    """Compact but rich context with REAL numbers only."""
    primary = tf_sum.get(timeframe) or (list(tf_sum.values())[0] if tf_sum else {})
    lines = []
    lines.append(f"Symbol: {symbol}")
    lines.append(f"Timeframe: {timeframe}")
    lines.append(f"Current price: {structure.get('last_close', primary.get('close'))}")
    lines.append(f"Recent high (100 bars): {structure.get('recent_high')}")
    lines.append(f"Recent low (100 bars): {structure.get('recent_low')}")
    lines.append(f"Support levels: {structure.get('support', [])}")
    lines.append(f"Resistance levels: {structure.get('resistance', [])}")
    lines.append(f"Volume ratio (last/avg20): {structure.get('volume_ratio')}")
    lines.append("")
    lines.append("-- Multi-timeframe trend --")
    for tf in ["1m","5m","15m","1h","4h","1d"]:
        if tf in tf_sum:
            f = tf_sum[tf]
            lines.append(f"{tf}: close={f.get('close')} trend={f.get('trend')} rsi={f.get('rsi')} atr={f.get('atr')} ema20={f.get('ema20')} ema50={f.get('ema50')}")
    lines.append("")
    if macro:
        lines.append(f"Macro: {json.dumps(macro, default=str)}")
    if fg:
        lines.append(f"Fear&Greed: {fg}")
    if ob:
        lines.append(f"Orderbook: {ob}")
    if fo:
        lines.append(f"Funding/OI: {fo}")
    if news:
        lines.append("-- Recent news headlines --")
        for n in (news[:5] if isinstance(news, list) else []):
            t = n.get("title", "") if isinstance(n, dict) else str(n)
            lines.append(f"* {t[:120]}")
    return "\n".join(lines)


def run_debate(symbol, timeframe="15m", ui=None):
    errors = []
    def say(msg):
        _p(msg)
        try:
            if ui is not None: ui.write(msg)
        except Exception: pass

    say("Step 1/6: Data ingestion")
    md = MarketData()
    try:
        kind = "crypto" if md.is_crypto(symbol) else "stock"
    except Exception:
        kind = "crypto"

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        f_tf = ex.submit(_safe, lambda: md.multi_tf(symbol, kind), {}, "multi_tf", errors)
        f_news = ex.submit(_safe, lambda: fetch_news(symbol), [], "news", errors)
        f_macro = ex.submit(_safe, lambda: fetch_macro(), {}, "macro", errors)
        f_fg = ex.submit(_safe, lambda: fear_greed(), {}, "fg", errors)
        f_ob = ex.submit(_safe, lambda: md.orderbook(symbol), {}, "ob", errors)
        f_fo = ex.submit(_safe, lambda: md.funding_oi(symbol), {}, "fo", errors)
        tf_map, news, macro, fg, ob, fo = f_tf.result(), f_news.result(), f_macro.result(), f_fg.result(), f_ob.result(), f_fo.result()

    if not tf_map:
        return {"symbol": symbol, "timeframe": timeframe, "bias": "neutral",
                "confidence": 0.0, "trade_type": "none",
                "reasons": [f"No data: {errors}"], "risks": [], "errors": errors}

    say("Step 2/6: Features + market structure")
    tf_sum = _safe(lambda: multi_tf_summary(tf_map), {}, "tf_sum", errors)
    primary = _pick(tf_map, timeframe)
    structure = _safe(lambda: market_structure(primary), {}, "structure", errors) if primary is not None else {}

    current_price = structure.get("last_close") or (tf_sum.get(timeframe, {}) or {}).get("close")
    atr = (tf_sum.get(timeframe, {}) or {}).get("atr") or 0
    support = structure.get("support", []) or []
    resistance = structure.get("resistance", []) or []

    ctx_text = _build_context(symbol, timeframe, tf_sum, structure, news, macro, fg, ob, fo)
    _p(f"Context size: {len(ctx_text)} chars")

    say("Step 3/6: Analysts")
    from future_admiral_v7.schema import AnalystView
    views = []
    analyst_fns = [
        ("Technical Analyst", analysts.technical_agent,
         "Focus: trend (EMA stack), momentum (RSI/MACD), support/resistance levels, ATR."),
        ("News Analyst", analysts.news_agent,
         "Focus: recent news impact on price. Use headline timestamps."),
        ("Risk Officer", analysts.risk_agent,
         "Focus: downside risk, invalidation levels, volatility (ATR), volume anomalies."),
    ]
    for role, fn, focus in analyst_fns:
        _p(f"  -> {role}")
        try:
            v = fn(ctx_text, focus)
            views.append(v)
            _p(f"  <- {role}: {v.bias} ({v.confidence:.2f})")
        except Exception as e:
            errors.append(f"{role}: {e}")
            views.append(AnalystView(role=role, bias="neutral", confidence=0.3, score=0, key_points=[], risks=[]))

    say("Step 4/6: Bull/Bear debate")
    try: bull = debaters.bull_round1(views, ctx_text)
    except Exception as e:
        errors.append(f"bull: {e}"); bull = {"thesis": "", "confidence": 0.5, "score": 0}
    try: bear = debaters.bear_round1(views, ctx_text)
    except Exception as e:
        errors.append(f"bear: {e}"); bear = {"thesis": "", "confidence": 0.5, "score": 0}

    say("Step 5/6: Admiral (final decision)")
    try:
        signal = admiral_final(symbol, timeframe, ctx_text, views, bull, bear, views[-1],
                               support, resistance, current_price, atr)
    except Exception as e:
        errors.append(f"admiral: {e}")
        from future_admiral_v7.schema import TradeSignal
        signal = TradeSignal(symbol=symbol, timeframe=timeframe, bias="neutral",
                             confidence=0.2, reasons=[f"admiral err: {e}"], risks=[],
                             current_price=current_price)

    say("Step 6/6: Risk engine")
    try:
        signal = finalize_signal(signal, equity=cfg.ACCOUNT_EQUITY, max_risk_pct=cfg.MAX_RISK_PER_TRADE)
    except Exception as e:
        errors.append(f"risk: {e}")

    try:
        signal.agents_summary = {
            "analysts": [v.model_dump() for v in views],
            "bull": bull, "bear": bear,
            "context": {"structure": structure, "tf_summary": tf_sum, "support": support, "resistance": resistance},
            "errors": errors,
        }
    except Exception: pass

    try: log_event("signal", signal.model_dump())
    except Exception: pass

    out = signal.model_dump()
    out["errors"] = errors
    return out
