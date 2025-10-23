from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from .trade import Base


class Ticker(Base):
    """实时行情数据模型"""
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True, nullable=False)
    last = Column(Float)  # 最新成交价
    last_sz = Column(Float)  # 最新成交数量
    ask_px = Column(Float)  # 卖一价
    ask_sz = Column(Float)  # 卖一数量
    bid_px = Column(Float)  # 买一价
    bid_sz = Column(Float)  # 买一数量
    open_24h = Column(Float)  # 24小时开盘价
    high_24h = Column(Float)  # 24小时最高价
    low_24h = Column(Float)  # 24小时最低价
    vol_ccy_24h = Column(Float)  # 24小时成交量（币）
    vol_24h = Column(Float)  # 24小时成交量（张）
    ts = Column(BigInteger)  # 数据产生时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_ticker_instrument_ts', 'instrument_id', 'ts'),
    )


class Candle(Base):
    """K线数据模型"""
    __tablename__ = "candles"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True, nullable=False)
    bar = Column(String, index=True, nullable=False)  # K线周期 (1m, 5m, 15m, 1H, 1D等)
    ts = Column(BigInteger, index=True, nullable=False)  # K线开始时间戳
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    vol = Column(Float)  # 交易量（张）
    vol_ccy = Column(Float)  # 交易量（币）
    vol_ccy_quote = Column(Float)  # 交易量（计价货币）
    confirm = Column(Boolean, default=False)  # 是否确认（0未确认，1已确认）
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_candle_instrument_bar_ts', 'instrument_id', 'bar', 'ts', unique=True),
    )


class OrderBook(Base):
    """订单簿数据模型"""
    __tablename__ = "order_books"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True, nullable=False)
    asks = Column(String)  # JSON格式存储卖单
    bids = Column(String)  # JSON格式存储买单
    ts = Column(BigInteger)  # 数据产生时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_orderbook_instrument_ts', 'instrument_id', 'ts'),
    )


class DataQualityLog(Base):
    """数据质量监控日志"""
    __tablename__ = "data_quality_logs"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True, nullable=False)
    check_type = Column(String, nullable=False)  # completeness, anomaly等
    status = Column(String, nullable=False)  # pass, warning, error
    message = Column(String)
    details = Column(String)  # JSON格式存储详细信息
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
