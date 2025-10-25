from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, GUID, UUIDPrimaryKeyMixin

if TYPE_CHECKING:  # pragma: no cover - typing support only
    from app.models.strategy import Strategy


ZERO = Decimal("0")


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    LIVE = "live"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class Order(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_instrument_status", "instrument_id", "status"),
        Index("ix_orders_exchange_order", "exchange_order_id"),
        Index("ix_orders_client_order", "client_order_id"),
    )

    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    client_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    exchange_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    side: Mapped[OrderSide] = mapped_column(
        Enum(OrderSide, name="order_side", native_enum=False), nullable=False
    )
    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="order_type", native_enum=False), nullable=False
    )
    trade_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")
    position_side: Mapped[Optional[PositionSide]] = mapped_column(
        Enum(PositionSide, name="order_position_side", native_enum=False), nullable=True
    )
    reduce_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(28, 12))
    size: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    filled_size: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    average_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(28, 12))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", native_enum=False),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    signal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    strategy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    filled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    trades: Mapped[list["Trade"]] = relationship(
        "Trade", back_populates="order", cascade="all, delete-orphan"
    )
    strategy: Mapped[Optional["Strategy"]] = relationship("Strategy", back_populates="orders")


class Trade(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_order_id", "order_id"),
        Index("ix_trades_instrument_id", "instrument_id"),
        Index("ix_trades_trade_id", "trade_id", unique=True),
    )

    trade_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    exchange_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    side: Mapped[OrderSide] = mapped_column(
        Enum(OrderSide, name="trade_side", native_enum=False), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    size: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    fee_currency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    liquidity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    trade_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    position_side: Mapped[Optional[PositionSide]] = mapped_column(
        Enum(PositionSide, name="trade_position_side", native_enum=False), nullable=True
    )
    strategy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship("Order", back_populates="trades")


class Position(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_instrument_side", "instrument_id", "side"),
        Index("ix_positions_instrument_open", "instrument_id", "opened_at"),
    )

    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    side: Mapped[PositionSide] = mapped_column(
        Enum(PositionSide, name="position_side", native_enum=False), nullable=False
    )
    size: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    average_price: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    current_price: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    margin: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False, default=ZERO)
    leverage: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    margin_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    trade_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    strategy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    strategy: Mapped[Optional["Strategy"]] = relationship("Strategy")
