from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, Text, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from decimal import Decimal
import enum

Base = declarative_base()


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    POST_ONLY = "post_only"
    FOK = "fok"
    IOC = "ioc"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    LIVE = "live"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"
    NET = "net"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_order_id = Column(String, unique=True, index=True, nullable=True)
    exchange_order_id = Column(String, unique=True, index=True, nullable=True)
    instrument_id = Column(String, index=True, nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    price = Column(Numeric(20, 8), nullable=True)
    size = Column(Numeric(20, 8), nullable=False)
    filled_size = Column(Numeric(20, 8), default=Decimal("0"))
    average_price = Column(Numeric(20, 8), nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, index=True)
    trade_mode = Column(String, nullable=True)  # cash, cross, isolated
    position_side = Column(SQLEnum(PositionSide), nullable=True)
    reduce_only = Column(Boolean, default=False)
    
    # Metadata
    strategy_id = Column(String, nullable=True, index=True)
    signal_id = Column(String, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Error information
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String, unique=True, index=True, nullable=False)
    order_id = Column(Integer, index=True, nullable=False)  # Reference to Order.id
    exchange_order_id = Column(String, nullable=True)
    instrument_id = Column(String, index=True, nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    size = Column(Numeric(20, 8), nullable=False)
    fee = Column(Numeric(20, 8), default=Decimal("0"))
    fee_currency = Column(String, nullable=True)
    
    # Additional info
    liquidity = Column(String, nullable=True)  # maker, taker
    trade_mode = Column(String, nullable=True)
    position_side = Column(SQLEnum(PositionSide), nullable=True)
    
    # Metadata
    strategy_id = Column(String, nullable=True, index=True)
    metadata = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    executed_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, unique=True, index=True, nullable=False)
    side = Column(SQLEnum(PositionSide), nullable=False)
    size = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    current_price = Column(Numeric(20, 8), nullable=False)
    average_price = Column(Numeric(20, 8), nullable=False)
    
    # PnL
    unrealized_pnl = Column(Numeric(20, 8), default=Decimal("0"))
    realized_pnl = Column(Numeric(20, 8), default=Decimal("0"))
    
    # Margin
    margin = Column(Numeric(20, 8), nullable=True)
    leverage = Column(Numeric(10, 2), nullable=True)
    margin_mode = Column(String, nullable=True)  # cross, isolated
    
    # Metadata
    strategy_id = Column(String, nullable=True, index=True)
    metadata = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)


class ExecutionEvent(Base):
    __tablename__ = "execution_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)  # order_created, order_filled, order_cancelled, position_opened, position_closed
    order_id = Column(Integer, nullable=True, index=True)
    trade_id = Column(Integer, nullable=True, index=True)
    position_id = Column(Integer, nullable=True, index=True)
    instrument_id = Column(String, nullable=False, index=True)
    
    # Event data
    event_data = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
