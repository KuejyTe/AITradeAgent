"""
指标导出API
"""

from fastapi import APIRouter, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import settings

router = APIRouter(prefix="/metrics", tags=["指标"])


@router.get("")
async def prometheus_metrics() -> Response:
    """Prometheus格式的指标导出"""
    if not settings.enable_metrics:
        raise HTTPException(status_code=503, detail="Metrics collection disabled")

    metrics = generate_latest()
    return Response(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST,
    )
