"""Future Admiral v7 - Debate Engine"""
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
    print(f"[ENGINE] {msg}", flush=True)
    sys.stdout.flush()


def _safe(fn, default, label, errors):
    try:
        return fn()
    except Exception as e:
        errors.append(f"{label}: {type(e).__name__}: {e}")
        return default


def _pick(tf_map, tf):
    if not tf_map:
        return None
    if tf in tf_map and tf_map[tf] is not None and not tf_map[tf].empty:
        return tf_map[tf]
    for df in tf_map.values():
        if df is not None and not df.empty:
            return df
    return None


def run_debate(symbol, timeframe="15m", ui=None):
    errors = []

    def say(msg):
        _p(msg)
        try:
            if ui is not None:
                ui.write(msg)
        except Exception:
            pass

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
        f_fg = ex.submit(_safe, lambda: fear_greed(), {}, "fear_greed", errors)
        f_ob = ex.submit(_safe, lambda: md.orderbook(symbol), {}, "orderbook", errors)
        f_fo = ex.submit(_safe, lambda: md.funding_oi(symbol), {}, "funding_oi", errors)
        tf_map = f_tf.result()
        news = f_news.result()
        macro = f_macro.result()
        fg = f_fg.result()
        ob = f_ob.result()
        fo = f_fo.result()

    _p(f"Got {len(tf_map)} timeframes, {len(news)} news items")

    if not tf_map:
        say(f"No market data. Errors: {errors}")
        return {"symbol": symbol, "timeframe": timeframe, "bias": "neutral",
                "confidence": 0.0, "reasons": [f"No data: {errors}"], "risks": [], "errors": errors}

    say("Step 2/6: Features")
    tf_sum = _safe(lambda: multi_tf_summary(tf_map), {}, "tf_sum", errors)
    primary = _pick(tf_map, timeframe)
    structure = _safe(lambda: market_structure(primary), {}, "structure", errors) if primary is not None else {}

    context = {
        "symbol": symbol, "timeframe": timeframe,
        "multi_timeframe": tf_sum, "structure": structure,
        "news": news[:6] if isinstance(news, list) else news,
        "macro": macro, "fear_greed": fg, "orderbook": ob, "funding_oi": fo,
    }
    try:
        ctx_text = json.dumps(context, default=str)[:1200]
    except Exception:
        ctx_text = str(context)[:1200]

    say("Step 3/6: Running analysts")
    from future_admiral_v7.schema import AnalystView
    views = []
    analyst_fns = [
        ("Technical Analyst", analysts.technical_agent),
        ("News Analyst", analysts.news_agent),
        ("Risk Officer", analysts.risk_agent),
    ]
    for role, fn in analyst_fns:
        _p(f"  -> {role}")
        try:
            v = fn(ctx_text)
            views.append(v)
            _p(f"  <- {role}: {v.bias} ({v.confidence:.2f})")
        except Exception as e:
            errors.append(f"{role}: {e}")
            views.append(AnalystView(role=role, bias="neutral", confidence=0.3, score=0, key_points=[], risks=[]))

    try:
        log_event("analysts", {"symbol": symbol, "views": [v.model_dump() for v in views]})
    except Exception:
        pass

    say("Step 4/6: Bull/Bear debate")
    try:
        bull1 = debaters.bull_round1(views, ctx_text)
    except Exception as e:
        errors.append(f"bull: {e}")
        bull1 = {"thesis": "", "confidence": 0.5, "score": 0}
    try:
        bear1 = debaters.bear_round1(views, ctx_text)
    except Exception as e:
        errors.append(f"bear: {e}")
        bear1 = {"thesis": "", "confidence": 0.5, "score": 0}
    bull, bear = bull1, bear1

    say("Step 5/6: Admiral")
    try:
        signal = admiral_final(symbol, timeframe, ctx_text, views, bull, bear, views[-1])
    except Exception as e:
        errors.append(f"admiral: {e}")
        from future_admiral_v7.schema import TradeSignal
        signal = TradeSignal(symbol=symbol, timeframe=timeframe, bias="neutral",
                             confidence=0.2, reasons=[f"admiral err: {e}"], risks=[])

    say("Step 6/6: Risk engine")
    try:
        signal = finalize_signal(signal, equity=cfg.ACCOUNT_EQUITY, max_risk_pct=cfg.MAX_RISK_PER_TRADE)
    except Exception as e:
        errors.append(f"risk: {e}")

    try:
        signal.agents_summary = {
            "analysts": [v.model_dump() for v in views],
            "bull": bull, "bear": bear, "context": context, "errors": errors,
        }
    except Exception:
        pass

    try:
        log_event("signal", signal.model_dump())
    except Exception:
        pass

    out = signal.model_dump()
    out["errors"] = errors
    return out
