from __future__ import annotations

from fastapi import APIRouter

from app.api.config import router as config_router
from app.api.health import router as health_router
from app.api.market_data import router as market_data_router
from app.api.metrics import router as metrics_router
from app.api.strategies import router as strategies_router
from app.api.trading import router as trading_router
from app.core.config import settings

router = APIRouter()

router.include_router(health_router)
router.include_router(metrics_router)
router.include_router(config_router)
router.include_router(strategies_router)
router.include_router(market_data_router)
router.include_router(trading_router)


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
    }
