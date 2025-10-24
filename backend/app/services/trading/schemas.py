from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.trading import OrderSide, OrderType, OrderStatus, PositionSide


class OrderParams(BaseModel):
    """Parameters for creating an order"""
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    instrument_id: str
    side: OrderSide
    order_type: OrderType
    size: Decimal
    price: Optional[Decimal] = None
    trade_mode: str = "cash"  # cash, cross, isolated
    position_side: Optional[PositionSide] = None
    reduce_only: bool = False
    client_order_id: Optional[str] = None
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrderResponse(BaseModel):
    """Order response"""
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    id: int
    client_order_id: Optional[str] = None
    exchange_order_id: Optional[str] = None
    instrument_id: str
    side: OrderSide
    order_type: OrderType
    price: Optional[Decimal] = None
    size: Decimal
    filled_size: Decimal
    average_price: Optional[Decimal] = None
    status: OrderStatus
    trade_mode: Optional[str] = None
    position_side: Optional[PositionSide] = None
    reduce_only: bool
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class TradeResponse(BaseModel):
    """Trade response"""
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    id: int
    trade_id: str
    order_id: int
    exchange_order_id: Optional[str] = None
    instrument_id: str
    side: OrderSide
    price: Decimal
    size: Decimal
    fee: Decimal
    fee_currency: Optional[str] = None
    liquidity: Optional[str] = None
    trade_mode: Optional[str] = None
    position_side: Optional[PositionSide] = None
    strategy_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    executed_at: datetime
    created_at: datetime


class PositionResponse(BaseModel):
    """Position response"""
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    id: int
    instrument_id: str
    side: PositionSide
    size: Decimal
    entry_price: Decimal
    current_price: Decimal
    average_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    margin: Optional[Decimal] = None
    leverage: Optional[Decimal] = None
    margin_mode: Optional[str] = None
    strategy_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    opened_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None


class PerformanceMetrics(BaseModel):
    """Trading performance metrics"""
    model_config = ConfigDict(json_encoders={Decimal: str, datetime: lambda v: v.isoformat()})
    
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: Decimal
    total_return_pct: float
    average_win: Decimal
    average_loss: Decimal
    profit_factor: float
    max_drawdown: Decimal
    max_drawdown_pct: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    start_date: datetime
    end_date: datetime


class RiskCheckResult(BaseModel):
    """Risk check result"""
    passed: bool
    reason: Optional[str] = None
    adjusted_size: Optional[Decimal] = None
    warnings: list[str] = Field(default_factory=list)
