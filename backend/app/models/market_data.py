from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Ticker(Base):
    __tablename__ = "tickers"
    __table_args__ = (
        Index("ix_tickers_instrument_ts", "instrument_id", "ts"),
        Index("ix_tickers_instrument_id", "instrument_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    last: Mapped[float] = mapped_column(Float, nullable=True)
    last_sz: Mapped[float] = mapped_column(Float, nullable=True)
    ask_px: Mapped[float] = mapped_column(Float, nullable=True)
    ask_sz: Mapped[float] = mapped_column(Float, nullable=True)
    bid_px: Mapped[float] = mapped_column(Float, nullable=True)
    bid_sz: Mapped[float] = mapped_column(Float, nullable=True)
    open_24h: Mapped[float] = mapped_column(Float, nullable=True)
    high_24h: Mapped[float] = mapped_column(Float, nullable=True)
    low_24h: Mapped[float] = mapped_column(Float, nullable=True)
    vol_ccy_24h: Mapped[float] = mapped_column(Float, nullable=True)
    vol_24h: Mapped[float] = mapped_column(Float, nullable=True)
    ts: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True, comment="毫秒级时间戳")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        Index("ix_candles_instrument_bar_ts", "instrument_id", "bar", "ts", unique=True),
        Index("ix_candles_instrument_id", "instrument_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    bar: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="毫秒级时间戳")
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    vol: Mapped[float] = mapped_column(Float, nullable=True)
    vol_ccy: Mapped[float] = mapped_column(Float, nullable=True)
    vol_ccy_quote: Mapped[float] = mapped_column(Float, nullable=True)
    confirm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OrderBook(Base):
    __tablename__ = "order_books"
    __table_args__ = (
        Index("ix_orderbook_instrument_ts", "instrument_id", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    asks: Mapped[str] = mapped_column(Text, nullable=True)  # JSON 序列化字符串
    bids: Mapped[str] = mapped_column(Text, nullable=True)
    ts: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DataQualityLog(Base):
    __tablename__ = "data_quality_logs"
    __table_args__ = (
        Index("ix_data_quality_instrument_ts", "instrument_id", "created_at"),
        Index("ix_data_quality_type", "check_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
