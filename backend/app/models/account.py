from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base, UUIDPrimaryKeyMixin

ZERO = Decimal("0")


class PositionSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class AccountBalance(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "account_balances"
    __table_args__ = (
        Index("ix_account_balances_currency_timestamp", "currency", "timestamp"),
        Index("ix_account_balances_currency", "currency"),
    )

    currency: Mapped[str] = mapped_column(String(20), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    available: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    frozen: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Position(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_instrument_side_timestamp", "instrument_id", "side", "timestamp"),
        Index("ix_positions_instrument_id", "instrument_id"),
    )

    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[PositionSide] = mapped_column(
        Enum(PositionSide, name="position_side", native_enum=False), nullable=False
    )
    size: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    current_price: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    margin: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False, default=ZERO)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
