from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.trading import Order, OrderStatus, Trade, TradeSide


def get_historical_orders(
    db: Session,
    *,
    instrument_id: str | None = None,
    strategy_id: UUID | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    status: OrderStatus | None = None,
    limit: int | None = None,
) -> list[Order]:
    stmt = select(Order).order_by(Order.created_at.desc())

    if instrument_id is not None:
        stmt = stmt.where(Order.instrument_id == instrument_id)
    if strategy_id is not None:
        stmt = stmt.where(Order.strategy_id == strategy_id)
    if start_time is not None:
        stmt = stmt.where(Order.created_at >= start_time)
    if end_time is not None:
        stmt = stmt.where(Order.created_at <= end_time)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    if limit is not None:
        stmt = stmt.limit(limit)

    return list(db.scalars(stmt))


def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def get_trading_performance(
    db: Session,
    *,
    strategy_id: UUID | None = None,
    instrument_id: str | None = None,
) -> Dict[str, Any]:
    stmt = (
        select(
            func.count(Trade.id).label("trade_count"),
            func.coalesce(func.sum(Trade.size), 0).label("total_volume"),
            func.coalesce(func.sum(Trade.price * Trade.size), 0).label("total_notional"),
            func.coalesce(func.sum(Trade.fee), 0).label("total_fees"),
            func.coalesce(
                func.sum(
                    case((Trade.side == TradeSide.BUY.value, Trade.size), else_=0)
                ),
                0,
            ).label("buy_volume"),
            func.coalesce(
                func.sum(
                    case((Trade.side == TradeSide.SELL.value, Trade.size), else_=0)
                ),
                0,
            ).label("sell_volume"),
            func.min(Trade.timestamp).label("first_trade_at"),
            func.max(Trade.timestamp).label("last_trade_at"),
        )
        .select_from(Trade)
        .join(Order, Trade.order_id == Order.id)
    )

    if strategy_id is not None:
        stmt = stmt.where(Order.strategy_id == strategy_id)
    if instrument_id is not None:
        stmt = stmt.where(Trade.instrument_id == instrument_id)

    row = db.execute(stmt).one()

    total_volume = _as_decimal(row.total_volume)
    total_notional = _as_decimal(row.total_notional)
    buy_volume = _as_decimal(row.buy_volume)
    sell_volume = _as_decimal(row.sell_volume)
    total_fees = _as_decimal(row.total_fees)

    average_price: Optional[Decimal]
    if total_volume == 0:
        average_price = None
    else:
        average_price = total_notional / total_volume

    return {
        "trade_count": int(row.trade_count or 0),
        "total_volume": total_volume,
        "total_notional": total_notional,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "net_volume": buy_volume - sell_volume,
        "total_fees": total_fees,
        "average_price": average_price,
        "first_trade_at": row.first_trade_at,
        "last_trade_at": row.last_trade_at,
    }
