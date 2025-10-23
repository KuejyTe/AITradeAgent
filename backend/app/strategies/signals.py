from enum import Enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class Signal(BaseModel):
    model_config = ConfigDict(
        use_enum_values=False,
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )
    
    type: SignalType
    instrument_id: str
    price: Decimal
    size: Decimal
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level between 0 and 1")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
