"""Prometheus metrics and performance tracking utilities."""

from __future__ import annotations

import time
from collections import defaultdict
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable, Dict, List, MutableMapping

from prometheus_client import Counter, Gauge, Histogram

# Prometheus metrics ---------------------------------------------------------

api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint"],
)

active_orders = Gauge(
    "active_orders_total",
    "Number of active orders",
)

strategy_signals = Counter(
    "strategy_signals_total",
    "Strategy signals generated",
    ["strategy", "signal_type"],
)

trades_executed = Counter(
    "trades_executed_total",
    "Trades executed",
    ["instrument", "side"],
)

websocket_connections = Gauge(
    "websocket_connections_active",
    "Active WebSocket connections",
)

performance_metrics: MutableMapping[str, List[float]] = defaultdict(list)


def track_performance(metric_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Measure execution time for async or sync callables."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start
                    bucket = performance_metrics[metric_name]
                    bucket.append(duration)
                    if len(bucket) > 1000:
                        bucket.pop(0)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                bucket = performance_metrics[metric_name]
                bucket.append(duration)
                if len(bucket) > 1000:
                    bucket.pop(0)

        return sync_wrapper

    return decorator


def get_performance_snapshot() -> Dict[str, Dict[str, float]]:
    """Return aggregated performance metrics for monitoring dashboards."""
    snapshot: Dict[str, Dict[str, float]] = {}
    for name, samples in performance_metrics.items():
        if not samples:
            continue
        total = sum(samples)
        snapshot[name] = {
            "count": float(len(samples)),
            "avg": total / len(samples),
            "min": min(samples),
            "max": max(samples),
        }
    return snapshot


__all__ = [
    "api_requests_total",
    "api_request_duration",
    "active_orders",
    "strategy_signals",
    "trades_executed",
    "websocket_connections",
    "performance_metrics",
    "track_performance",
    "get_performance_snapshot",
]
