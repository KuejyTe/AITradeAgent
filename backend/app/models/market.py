from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class Candle(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id", "timestamp", "bar", name="uq_candles_instrument_timestamp_bar"
        ),
        Index("ix_candles_instrument_bar_timestamp", "instrument_id", "bar", "timestamp"),
        Index("ix_candles_instrument_id", "instrument_id"),
    )

    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    bar: Mapped[str] = mapped_column(String(16), nullable=False)


class Ticker(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tickers"
    __table_args__ = (
        Index("ix_tickers_instrument_timestamp", "instrument_id", "timestamp"),
        Index("ix_tickers_instrument_id", "instrument_id"),
    )

    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False)
    last_price: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    bid_price: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    ask_price: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    volume_24h: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
