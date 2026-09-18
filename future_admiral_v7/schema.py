from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime, timezone


class AnalystView(BaseModel):
    role: str
    bias: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(ge=0, le=1)
    score: float = Field(ge=-10, le=10)
    key_points: List[str] = []
    risks: List[str] = []


class TradeSignal(BaseModel):
    symbol: str
    timeframe: str
    bias: Literal["long", "short", "neutral"]
    confidence: float = Field(ge=0, le=1)
    trade_type: Literal["spot", "futures", "none"] = "none"
    duration_hours: float = 0.0
    reasoning_duration: str = ""
    current_price: Optional[float] = None
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: List[float] = []
    invalidation: str = ""
    support: List[float] = []
    resistance: List[float] = []
    position_size_pct: float = 0.0
    leverage: float = 1.0
    risk_reward: float = 0.0
    reasons: List[str] = []
    risks: List[str] = []
    news_summary: List[str] = []
    sources: List[str] = []
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agents_summary: dict = {}


class ActionPlan(BaseModel):
    """Simple, actionable instructions in plain language."""
    action: Literal[
        "BUY_NOW",          # Buy immediately at market
        "WAIT_FOR_PRICE",   # Don't buy yet — wait for specific price
        "HOLD",             # Already bought — hold position
        "SELL_NOW",         # Sell immediately
        "SELL_AT_PRICE",    # Sell when price hits X
        "SELL_BY_TIME",     # Sell by specific day
        "AVOID",            # Don't touch this asset
        "SET_ALERT",        # Watch price, alert at X
    ] = "AVOID"

    headline: str = ""              # e.g. "Wait — Don't buy above $100"
    plain_explanation: str = ""     # 2-3 lines in simple Urdu/English

    # If WAIT_FOR_PRICE
    buy_trigger_price: Optional[float] = None
    buy_trigger_condition: str = ""  # "if price drops to $X and holds 4h"
    avoid_above_price: Optional[float] = None  # "don't buy above this"

    # If HOLD
    hold_until_price: Optional[float] = None  # Keep holding until this
    sell_if_drops_below: Optional[float] = None  # Exit if drops below

    # Time-based
    wait_days_min: int = 0
    wait_days_max: int = 0
    sell_by_day: int = 0
    time_explanation: str = ""

    # Reasoning
    why_this_action: List[str] = []
    what_would_change_mind: str = ""


class SpotSignal(BaseModel):
    symbol: str
    timeframe: str
    current_price: Optional[float] = None
    recommendation: Literal["buy_now", "buy_dip", "wait", "avoid"] = "wait"
    confidence: float = Field(default=0.0, ge=0, le=1)
    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    stop_loss: Optional[float] = None
    invalidation: str = ""
    target_1d: Optional[float] = None
    target_5d: Optional[float] = None
    target_10d: Optional[float] = None
    target_30d: Optional[float] = None
    prob_1d: float = 0.0
    prob_5d: float = 0.0
    prob_10d: float = 0.0
    prob_30d: float = 0.0
    fundamental_score: int = 0
    institutional_signal: Literal["bullish", "neutral", "bearish"] = "neutral"
    institutional_evidence: List[str] = []
    onchain_evidence: List[str] = []
    catalysts: List[dict] = []
    thesis: str = ""
    reasons: List[str] = []
    risks: List[str] = []
    news_summary: List[str] = []
    bull_thesis: str = ""
    bull_confidence: float = 0.0
    bear_thesis: str = ""
    bear_confidence: float = 0.0
    verdict: str = ""
    action_plan: Optional[ActionPlan] = None
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agents_summary: dict = {}
