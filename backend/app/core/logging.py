"""Logging configuration and structured logging utilities for the backend service."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings

try:  # pragma: no cover - optional dependency
    import sentry_sdk
except ImportError:  # pragma: no cover - sentry is optional in some deployments
    sentry_sdk = None  # type: ignore[assignment]


LOG_FORMAT = {
    "timestamp": "%(asctime)s",
    "level": "%(levelname)s",
    "module": "%(name)s",
    "function": "%(funcName)s",
    "line": "%(lineno)d",
    "message": "%(message)s",
}

_LOG_DIR = settings.resolve_path(settings.log_file).parent
_LOG_FILES: Dict[str, Path] = {
    "app": _LOG_DIR / "app.log",
    "api": _LOG_DIR / "api.log",
    "trading": _LOG_DIR / "trading.log",
    "strategy": _LOG_DIR / "strategy.log",
    "error": _LOG_DIR / "error.log",
}
_SENTRY_INITIALISED = False
_LOGGING_CONFIGURED = False


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _resolve_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    numeric = getattr(logging, level.upper(), None)
    if isinstance(numeric, int):
        return numeric
    return logging.INFO


class StructuredFormatter(logging.Formatter):
    """Format log records as structured JSON payloads."""

    FORMAT_MAP = LOG_FORMAT

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        context = getattr(record, "context", None)
        if context:
            payload["context"] = context

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack_info"] = record.stack_info

        return json.dumps(payload, ensure_ascii=False)


def _create_size_based_handler(path: Path, level: int) -> logging.Handler:
    _ensure_directory(path)
    handler = RotatingFileHandler(
        path,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(StructuredFormatter())
    return handler


def _create_time_based_handler(path: Path, level: int) -> logging.Handler:
    _ensure_directory(path)
    handler = TimedRotatingFileHandler(
        path,
        when=settings.log_rotation_when,
        interval=settings.log_rotation_interval,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
        utc=True,
    )
    handler.setLevel(level)
    handler.setFormatter(StructuredFormatter())
    return handler


def _configure_structured_logger(name: str, path: Path, level: int, *, time_based: bool) -> None:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(level)
    handler = _create_time_based_handler(path, level) if time_based else _create_size_based_handler(path, level)
    logger.addHandler(handler)
    logger.propagate = False


def setup_logging(force: bool = False) -> None:
    """Initialise the logging subsystem with structured handlers."""
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED and not force:
        return

    logging.captureWarnings(True)

    root_logger = logging.getLogger()
    root_logger.setLevel(_resolve_level(settings.log_level))
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(root_logger.level)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    root_logger.addHandler(console_handler)

    for name, path in _LOG_FILES.items():
        level = logging.ERROR if name == "error" else logging.INFO
        _configure_structured_logger(name, path, level, time_based=(name != "error"))

    audit_path = settings.resolve_path(settings.CONFIG_AUDIT_LOG)
    _configure_structured_logger("audit", audit_path, logging.INFO, time_based=False)

    _LOGGING_CONFIGURED = True


class StructuredLogger:
    """Structured logger wrapper that enriches records with context information."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str | int, message: str, **context: Any) -> None:
        numeric_level = _resolve_level(level)
        extra = {"context": context} if context else {}
        self.logger.log(numeric_level, message, extra=extra)

    def debug(self, message: str, **context: Any) -> None:
        self.log(logging.DEBUG, message, **context)

    def info(self, message: str, **context: Any) -> None:
        self.log(logging.INFO, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self.log(logging.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> None:
        self.log(logging.ERROR, message, **context)

    def critical(self, message: str, **context: Any) -> None:
        self.log(logging.CRITICAL, message, **context)


class AuditLogger:
    """Audit logging helper for recording sensitive operations."""

    def __init__(self, logger: Optional[StructuredLogger] = None):
        self._logger = logger or StructuredLogger("audit")

    def log_operation(
        self,
        user_id: str,
        operation: str,
        resource: str,
        details: Dict[str, Any],
        *,
        ip_address: Optional[str] = None,
        status: str | None = None,
    ) -> None:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "operation": operation,
            "resource": resource,
            "details": details,
            "ip_address": ip_address or "unknown",
            "status": status or "success",
        }
        self._logger.info("audit.operation", **payload)


def cleanup_old_logs(days: int = 30, *, directory: Optional[Path] = None) -> None:
    """Remove log files older than the specified retention period."""
    log_directory = directory or _LOG_DIR
    if not log_directory.exists():
        return

    cutoff = datetime.utcnow() - timedelta(days=days)
    for log_file in log_directory.glob("*.log*"):
        try:
            modified = datetime.utcfromtimestamp(log_file.stat().st_mtime)
            if modified < cutoff:
                log_file.unlink(missing_ok=True)
        except OSError as exc:  # pragma: no cover - filesystem issues
            logging.getLogger("app").warning("Failed to remove old log file", file=str(log_file), error=str(exc))


def init_sentry(force: bool = False) -> None:
    """Initialise Sentry error tracking if configuration is provided."""
    global _SENTRY_INITIALISED

    if _SENTRY_INITIALISED and not force:
        return

    if not settings.sentry_dsn or sentry_sdk is None:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
    _SENTRY_INITIALISED = True


def capture_exception_with_context(exception: Exception, context: Dict[str, Any]) -> None:
    """Capture exceptions with additional context information in Sentry."""
    if sentry_sdk is None or not settings.sentry_dsn:
        return

    if not _SENTRY_INITIALISED:
        init_sentry()

    with sentry_sdk.push_scope() as scope:  # type: ignore[attr-defined]
        for key, value in context.items():
            if isinstance(value, dict):
                scope.set_context(key, value)
            else:
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(exception)


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)


setup_logging()

app_logger = StructuredLogger("app")
api_logger = StructuredLogger("api")
trading_logger = StructuredLogger("trading")
strategy_logger = StructuredLogger("strategy")
error_logger = StructuredLogger("error")
audit_logger = StructuredLogger("audit")
audit_log = AuditLogger(audit_logger)


__all__ = [
    "StructuredLogger",
    "AuditLogger",
    "setup_logging",
    "init_sentry",
    "capture_exception_with_context",
    "cleanup_old_logs",
    "get_logger",
    "app_logger",
    "api_logger",
    "trading_logger",
    "strategy_logger",
    "error_logger",
    "audit_logger",
    "audit_log",
]
