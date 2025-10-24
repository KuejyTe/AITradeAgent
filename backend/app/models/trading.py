"""
交易相关数据模型
"""

from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from .base import Base


class OrderSide(str, enum.Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, enum.Enum):
    """订单状态"""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(String(100), unique=True, nullable=False, index=True, comment="交易所订单ID")
    instrument_id = Column(String(50), nullable=False, index=True, comment="交易对")
    side = Column(SQLEnum(OrderSide), nullable=False, comment="买卖方向")
    order_type = Column(SQLEnum(OrderType), nullable=False, comment="订单类型")
    price = Column(Numeric(20, 8), comment="价格")
    size = Column(Numeric(20, 8), nullable=False, comment="数量")
    filled_size = Column(Numeric(20, 8), default=0, comment="已成交数量")
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING, comment="订单状态")
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=True, comment="关联策略ID")
    client_order_id = Column(String(100), comment="客户端订单ID")
    fee = Column(Numeric(20, 8), default=0, comment="手续费")
    fee_currency = Column(String(20), comment="手续费币种")
    error_message = Column(String(500), comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 关系
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")
    strategy = relationship("Strategy", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, instrument_id={self.instrument_id}, side={self.side}, status={self.status})>"


class Trade(Base):
    """成交记录模型"""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(String(100), unique=True, nullable=False, index=True, comment="交易所成交ID")
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, comment="关联订单ID")
    instrument_id = Column(String(50), nullable=False, index=True, comment="交易对")
    side = Column(SQLEnum(OrderSide), nullable=False, comment="买卖方向")
    price = Column(Numeric(20, 8), nullable=False, comment="成交价格")
    size = Column(Numeric(20, 8), nullable=False, comment="成交数量")
    fee = Column(Numeric(20, 8), default=0, comment="手续费")
    fee_currency = Column(String(20), comment="手续费币种")
    role = Column(String(20), comment="maker/taker")
    timestamp = Column(DateTime, nullable=False, index=True, comment="成交时间")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="记录创建时间")

    # 关系
    order = relationship("Order", back_populates="trades")

    def __repr__(self):
        return f"<Trade(id={self.id}, instrument_id={self.instrument_id}, price={self.price}, size={self.size})>"