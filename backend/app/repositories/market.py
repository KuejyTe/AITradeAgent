from __future__ import annotations

from datetime import datetime
from typing import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market import Candle


def bulk_insert_candles(
    db: Session, candles: Sequence[Candle | Mapping[str, object]]
) -> list[Candle]:
    """Persist multiple candle records in a single transaction."""
    if not candles:
        return []

    inserted: list[Candle] = []
    for entry in candles:
        candle = entry if isinstance(entry, Candle) else Candle(**entry)
        db.add(candle)
        inserted.append(candle)

    db.flush()
    return inserted


def get_candles(
    db: Session,
    *,
    instrument_id: str,
    bar: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int | None = None,
) -> list[Candle]:
    stmt = (
        select(Candle)
        .where(Candle.instrument_id == instrument_id, Candle.bar == bar)
        .order_by(Candle.timestamp.asc())
    )

    if start_time is not None:
        stmt = stmt.where(Candle.timestamp >= start_time)
    if end_time is not None:
        stmt = stmt.where(Candle.timestamp <= end_time)
    if limit is not None:
        stmt = stmt.limit(limit)

    return list(db.scalars(stmt))
