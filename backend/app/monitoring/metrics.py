"""
性能指标收集
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import time


# 定义Prometheus指标
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

active_orders = Gauge(
    'active_orders_total',
    'Number of active orders'
)

strategy_signals = Counter(
    'strategy_signals_total',
    'Strategy signals generated',
    ['strategy', 'signal_type']
)

trades_executed = Counter(
    'trades_executed_total',
    'Trades executed',
    ['instrument', 'side']
)

websocket_connections = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

account_balance = Gauge(
    'account_balance_usd',
    'Account balance in USD'
)

position_value = Gauge(
    'position_value_usd',
    'Total position value in USD',
    ['instrument']
)


def track_api_metrics(func):
    """API指标追踪装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 记录成功请求
            api_requests_total.labels(
                method='unknown',
                endpoint=func.__name__,
                status='success'
            ).inc()
            
            api_request_duration.labels(
                method='unknown',
                endpoint=func.__name__
            ).observe(duration)
            
            return result
            
        except Exception as e:
            # 记录失败请求
            api_requests_total.labels(
                method='unknown',
                endpoint=func.__name__,
                status='error'
            ).inc()
            
            raise
    
    return wrapper


def track_performance(metric_name: str):"""性能追踪装饰器"""
def decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start
            # 这里可以记录到数据库或其他存储
            print(f"{metric_name}: {duration:.3f}s")
    return wrapper
return decorator
