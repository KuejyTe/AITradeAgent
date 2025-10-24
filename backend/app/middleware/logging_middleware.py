"""
请求日志中间件
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.logging import api_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并记录日志"""
        # 记录请求开始
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # 记录请求信息
        api_logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        # 执行请求
        try:
            response = await call_next(request)
duration = time.time() - start_time

        # 记录响应
        api_logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        # 记录错误
        api_logger.error(
            "Request failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=round(duration * 1000, 2)
)

        raise
