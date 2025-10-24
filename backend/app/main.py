from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.websocket import websocket_endpoint
from app.core.config import settings
from app.core.logging import app_logger, init_sentry, setup_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware

setup_logging()
init_sentry()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered trading agent API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.websocket("/ws")(websocket_endpoint)


@app.on_event("startup")
async def on_startup() -> None:
    app_logger.info(
        "Application startup",
        environment=settings.environment,
        version=settings.VERSION,
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs_url": "/docs",
    }


if __name__ == "__main__":  # pragma: no cover - development helper
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
