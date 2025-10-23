from fastapi import APIRouter

router = APIRouter()


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
