from __future__ import annotations

from app.db.base import Base
from app.db.session import get_engine

# Import models to ensure metadata registration
import app.models.account  # noqa: F401
import app.models.market  # noqa: F401
import app.models.strategy  # noqa: F401
import app.models.trading  # noqa: F401


def init_db() -> None:
    """Initialize database schema."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
