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

    # Trade type and duration
    trade_type: Literal["spot", "futures", "none"] = "none"
    duration_hours: float = 0.0
    reasoning_duration: str = ""

    # Real price levels
    current_price: Optional[float] = None
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: List[float] = []
    invalidation: str = ""

    # Support / Resistance from real data
    support: List[float] = []
    resistance: List[float] = []

    # Risk
    position_size_pct: float = 0.0
    leverage: float = 1.0
    risk_reward: float = 0.0

    # Narrative
    reasons: List[str] = []
    risks: List[str] = []
    news_summary: List[str] = []
    sources: List[str] = []

    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agents_summary: dict = {}
