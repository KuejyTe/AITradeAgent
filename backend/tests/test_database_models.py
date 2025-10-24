from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.market import Candle
from app.models.strategy import Strategy, StrategyStatus
from app.models.trading import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Trade,
    TradeSide,
)
from app.repositories.market import bulk_insert_candles
from app.repositories.trading import get_historical_orders, get_trading_performance


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(  # type: ignore[var-annotated]
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    with TestingSession() as session:
        yield session


def test_bulk_insert_candles(session: Session) -> None:
    payload = [
        {
            "instrument_id": "BTC-USDT",
            "timestamp": datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc),
            "open": Decimal("30000"),
            "high": Decimal("30100"),
            "low": Decimal("29950"),
            "close": Decimal("30050"),
            "volume": Decimal("12.5"),
            "bar": "1m",
        },
        {
            "instrument_id": "BTC-USDT",
            "timestamp": datetime(2023, 1, 1, 0, 1, tzinfo=timezone.utc),
            "open": Decimal("30050"),
            "high": Decimal("30200"),
            "low": Decimal("30000"),
            "close": Decimal("30150"),
            "volume": Decimal("8.2"),
            "bar": "1m",
        },
    ]

    inserted = bulk_insert_candles(session, payload)

    assert len(inserted) == 2
    candles = session.scalars(select(Candle)).all()
    assert len(candles) == 2
    assert candles[0].instrument_id == "BTC-USDT"


def test_get_historical_orders(session: Session) -> None:
    strategy = Strategy(name="Mean Reversion", type="mean", parameters={})
    session.add(strategy)
    session.flush()

    order_pending = Order(
        order_id="ext-1",
        instrument_id="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=Decimal("30000"),
        size=Decimal("0.1"),
        filled_size=Decimal("0"),
        status=OrderStatus.PENDING,
        strategy_id=strategy.id,
    )
    order_filled = Order(
        order_id="ext-2",
        instrument_id="ETH-USDT",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("2000"),
        size=Decimal("1"),
        filled_size=Decimal("1"),
        status=OrderStatus.FILLED,
        strategy_id=strategy.id,
    )

    session.add_all([order_pending, order_filled])
    session.commit()

    btc_orders = get_historical_orders(session, instrument_id="BTC-USDT")
    assert len(btc_orders) == 1
    assert btc_orders[0].order_id == "ext-1"

    filled_orders = get_historical_orders(session, status=OrderStatus.FILLED)
    assert len(filled_orders) == 1
    assert filled_orders[0].order_id == "ext-2"


def test_get_trading_performance(session: Session) -> None:
    strategy = Strategy(name="Breakout", type="momentum", parameters={}, status=StrategyStatus.ACTIVE)
    session.add(strategy)
    session.flush()

    order = Order(
        order_id="perf-1",
        instrument_id="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=Decimal("30000"),
        size=Decimal("0.1"),
        filled_size=Decimal("0.1"),
        status=OrderStatus.FILLED,
        strategy_id=strategy.id,
    )
    session.add(order)
    session.flush()

    first_trade_time = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
    second_trade_time = datetime(2023, 1, 1, 0, 5, tzinfo=timezone.utc)

    trade_buy = Trade(
        trade_id="trade-1",
        order_id=order.id,
        instrument_id="BTC-USDT",
        side=TradeSide.BUY,
        price=Decimal("30000"),
        size=Decimal("0.1"),
        fee=Decimal("0.5"),
        timestamp=first_trade_time,
    )
    trade_sell = Trade(
        trade_id="trade-2",
        order_id=order.id,
        instrument_id="BTC-USDT",
        side=TradeSide.SELL,
        price=Decimal("31000"),
        size=Decimal("0.05"),
        fee=Decimal("0.25"),
        timestamp=second_trade_time,
    )
    session.add_all([trade_buy, trade_sell])
    session.commit()

    performance = get_trading_performance(
        session, strategy_id=strategy.id, instrument_id="BTC-USDT"
    )

    assert performance["trade_count"] == 2
    assert performance["total_volume"] == Decimal("0.15")
    assert performance["buy_volume"] == Decimal("0.1")
    assert performance["sell_volume"] == Decimal("0.05")
    assert performance["net_volume"] == Decimal("0.05")
    assert performance["total_fees"] == Decimal("0.75")
    assert performance["first_trade_at"] == first_trade_time
    assert performance["last_trade_at"] == second_trade_time

    expected_notional = Decimal("30000") * Decimal("0.1") + Decimal("31000") * Decimal("0.05")
    assert performance["total_notional"] == expected_notional

    average_price = performance["average_price"]
    assert average_price is not None
    assert average_price.quantize(Decimal("0.0001")) == (expected_notional / Decimal("0.15")).quantize(
        Decimal("0.0001")
    )
