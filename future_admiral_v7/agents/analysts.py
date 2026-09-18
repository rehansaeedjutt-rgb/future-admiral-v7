from future_admiral_v7.agents.base import run_analyst


def technical_agent(ctx: str):
    return run_analyst(
        "Technical Analyst",
        ctx,
        "Analyze multi-timeframe trend, RSI, EMA stack, MACD, ATR, support/resistance and structural bias.",
    )


def fundamental_agent(ctx: str):
    return run_analyst(
        "Fundamental Analyst",
        ctx,
        "Analyze valuation, growth, supply, business quality, and catalyst relevance where available.",
    )


def news_agent(ctx: str):
    return run_analyst(
        "News Analyst",
        ctx,
        "Only use news newer than 48 hours. Weight by credibility and catalyst quality.",
    )


def macro_agent(ctx: str):
    return run_analyst(
        "Macro Analyst",
        ctx,
        "Assess risk-on vs risk-off regime using VIX, DXY, US10Y, SPX, gold and global liquidity context.",
    )


def sentiment_agent(ctx: str):
    return run_analyst(
        "Sentiment Analyst",
        ctx,
        "Analyze fear and greed, funding rate, orderbook imbalance, and crowd sentiment.",
    )


def onchain_agent(ctx: str):
    return run_analyst(
        "OnChain Analyst",
        ctx,
        "Assess exchange flows, whale activity, funding, and open interest dynamics.",
    )


def risk_agent(ctx: str):
    return run_analyst(
        "Risk Officer",
        ctx,
        "Identify invalidation levels, drawdown risk, correlation risk, and event risk.",
    )
