from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, GUID, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.trading import Order


class StrategyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class StrategySignalType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Strategy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "strategies"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[StrategyStatus] = mapped_column(
        Enum(StrategyStatus, name="strategy_status", native_enum=False),
        nullable=False,
        default=StrategyStatus.ACTIVE,
    )

    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="strategy", cascade="all, delete-orphan"
    )
    signals: Mapped[List["StrategySignal"]] = relationship(
        "StrategySignal", back_populates="strategy", cascade="all, delete-orphan"
    )


class StrategySignal(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "strategy_signals"
    __table_args__ = (
        Index("ix_strategy_signals_strategy_timestamp", "strategy_id", "timestamp"),
        Index("ix_strategy_signals_instrument_id", "instrument_id"),
    )

    strategy_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False)
    signal_type: Mapped[StrategySignalType] = mapped_column(
        Enum(StrategySignalType, name="strategy_signal_type", native_enum=False), nullable=False
    )
    strength: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="signals")
