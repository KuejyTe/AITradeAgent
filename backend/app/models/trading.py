from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, GUID, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.strategy import Strategy


ZERO = Decimal("0")


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


class TradeSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_orders_order_id"),
        Index("ix_orders_instrument_created_at", "instrument_id", "created_at"),
        Index("ix_orders_instrument_id", "instrument_id"),
    )

    order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[OrderSide] = mapped_column(
        Enum(OrderSide, name="order_side", native_enum=False), nullable=False
    )
    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="order_type", native_enum=False), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    size: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    filled_size: Mapped[Decimal] = mapped_column(
        Numeric(24, 12), nullable=False, default=ZERO
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", native_enum=False),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    strategy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True
    )

    strategy: Mapped[Optional["Strategy"]] = relationship(
        "Strategy", back_populates="orders"
    )
    trades: Mapped[List["Trade"]] = relationship(
        "Trade", back_populates="order", cascade="all, delete-orphan"
    )


class Trade(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("trade_id", name="uq_trades_trade_id"),
        Index("ix_trades_order_timestamp", "order_id", "timestamp"),
        Index("ix_trades_order_id", "order_id"),
        Index("ix_trades_instrument_id", "instrument_id"),
    )

    trade_id: Mapped[str] = mapped_column(String(128), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[TradeSide] = mapped_column(
        Enum(TradeSide, name="trade_side", native_enum=False), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    size: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship("Order", back_populates="trades")
