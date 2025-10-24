"""
指标导出API
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


router = APIRouter(prefix="/metrics", tags=["指标"])


@router.get("")
async def prometheus_metrics():
    """Prometheus格式的指标导出"""
    metrics = generate_latest()
    return Response(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST
    )
