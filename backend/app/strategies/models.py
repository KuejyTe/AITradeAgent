from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class Order(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    id: str
    instrument_id: str
    side: OrderSide
    order_type: OrderType
    price: Optional[Decimal] = None
    size: Decimal
    filled_size: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Candle(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class MarketData(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    instrument_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_price: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    candles: List[Candle] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Position(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    instrument_id: str
    size: Decimal
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    side: OrderSide
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Account(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    balance: Decimal
    equity: Decimal
    available_balance: Decimal
    positions: List[Position] = Field(default_factory=list)
    daily_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    margin_ratio: Optional[float] = None
