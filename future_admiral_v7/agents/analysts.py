"""Future Admiral v7 - Analyst agents"""
from future_admiral_v7.agents.base import run_analyst


def technical_agent(ctx, focus=""):
    return run_analyst("Technical Analyst", ctx,
                       focus or "Trend (EMA), RSI, MACD, support/resistance, ATR, volume.")


def news_agent(ctx, focus=""):
    return run_analyst("News Analyst", ctx,
                       focus or "Recent news impact, catalysts, timestamps.")


def risk_agent(ctx, focus=""):
    return run_analyst("Risk Officer", ctx,
                       focus or "Downside risk, invalidation, volatility.")


def fundamental_agent(ctx, focus=""):
    return run_analyst("Fundamental Analyst", ctx, focus or "Valuation, supply, adoption.")


def macro_agent(ctx, focus=""):
    return run_analyst("Macro Analyst", ctx, focus or "DXY, yields, VIX, risk regime.")


def sentiment_agent(ctx, focus=""):
    return run_analyst("Sentiment Analyst", ctx, focus or "Fear/greed, funding, retail heat.")


def onchain_agent(ctx, focus=""):
    return run_analyst("OnChain Analyst", ctx, focus or "Exchange flows, whales, OI.")
