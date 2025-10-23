from fastapi import APIRouter
from app.api.strategies import router as strategies_router
from app.api.market_data import router as market_data_router

router = APIRouter()

# Include sub-routers
router.include_router(strategies_router)
router.include_router(market_data_router)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AITradeAgent API is running"}


@router.get("/")
async def root():
    return {
        "message": "Welcome to AITradeAgent API",
        "version": "1.0.0",
        "docs": "/docs"
    }
