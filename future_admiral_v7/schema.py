from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, List, Optional

from pydantic import BaseModel, Field, field_validator


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

    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: List[float] = []
    invalidation: str = ""

    position_size_pct: float = 0.0
    leverage: float = 1.0
    risk_reward: float = 0.0

    reasons: List[str] = []
    risks: List[str] = []
    sources: List[str] = []

    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agents_summary: dict[str, Any] = {}

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))
