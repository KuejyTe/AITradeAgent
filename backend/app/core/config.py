from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, SettingsSourceCallable


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # Application metadata
    PROJECT_NAME: str = Field("AITradeAgent", env="PROJECT_NAME")
    VERSION: str = Field("1.0.0", env="VERSION")
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")
    APP_NAME: str = Field("AITradeAgent", env="APP_NAME")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(False, env="DEBUG")
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        env="BACKEND_CORS_ORIGINS",
    )

    # OKX API credentials
    OKX_API_KEY: str = Field("", env="OKX_API_KEY")
    OKX_SECRET_KEY: str = Field("", env="OKX_SECRET_KEY")
    OKX_PASSPHRASE: str = Field("", env="OKX_PASSPHRASE")
    OKX_API_BASE_URL: str = Field("https://www.okx.com", env="OKX_API_BASE_URL")
    OKX_WS_PUBLIC_URL: str = Field("wss://ws.okx.com:8443/ws/v5/public", env="OKX_WS_PUBLIC_URL")
    OKX_WS_PRIVATE_URL: str = Field("wss://ws.okx.com:8443/ws/v5/private", env="OKX_WS_PRIVATE_URL")

    # Database configuration
    DATABASE_URL: str = Field("sqlite+pysqlite:///./trading.db", env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(20, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(1800, env="DB_POOL_RECYCLE")

    # Optional services
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")

    # Security
    SECRET_KEY: str = Field("change-me", env="SECRET_KEY")
    JWT_EXPIRATION_HOURS: int = Field(24, env="JWT_EXPIRATION_HOURS")
    ENCRYPTION_KEY: Optional[str] = Field(None, env="ENCRYPTION_KEY")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("logs/app.log", env="LOG_FILE")
    LOG_FILE_PATH: Optional[str] = Field(None, env="LOG_FILE_PATH")
    LOG_MAX_SIZE: int = Field(10 * 1024 * 1024, env="LOG_MAX_SIZE")
    LOG_BACKUP_COUNT: int = Field(10, env="LOG_BACKUP_COUNT")
    LOG_ROTATION_WHEN: str = Field("midnight", env="LOG_ROTATION_WHEN")
    LOG_ROTATION_INTERVAL: int = Field(1, env="LOG_ROTATION_INTERVAL")

    # Monitoring
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9090, env="METRICS_PORT")

    # Sentry
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: Optional[str] = Field(None, env="SENTRY_ENVIRONMENT")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(1.0, env="SENTRY_TRACES_SAMPLE_RATE")

    # Alerting
    ALERT_EMAIL: Optional[str] = Field(None, env="ALERT_EMAIL")
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")

    # Trading defaults
    DEFAULT_TRADE_AMOUNT: float = Field(100, env="DEFAULT_TRADE_AMOUNT")
    MAX_POSITION_SIZE: float = Field(10000, env="MAX_POSITION_SIZE")
    RISK_PERCENTAGE: float = Field(0.02, env="RISK_PERCENTAGE")
    SLIPPAGE_TOLERANCE: float = Field(0.001, env="SLIPPAGE_TOLERANCE")

    # Configuration management
    CONFIG_AUDIT_LOG: str = Field("logs/config_audit.log", env="CONFIG_AUDIT_LOG")
    CONFIG_STORAGE_DIR: str = Field("configs/system", env="CONFIG_STORAGE_DIR")
    CONFIG_BACKUP_DIR: str = Field("configs/backups", env="CONFIG_BACKUP_DIR")
    STRATEGY_CONFIG_DIR: str = Field("configs/strategies", env="STRATEGY_CONFIG_DIR")
    API_KEYS_STORE: str = Field("configs/secure/api_keys.json", env="API_KEYS_STORE")

    # Data collector defaults
    DATA_COLLECTOR_CONFIG: Dict[str, Any] = Field(
        default_factory=lambda: {
            "instruments": ["BTC-USDT"],
            "candle_bars": ["1m", "5m", "1H"],
            "cache_enabled": False,
            "enable_order_book": False,
            "retention_days": 90,
        }
    )

    # Runtime alias mapping to allow both snake_case and upper case mutation
    _runtime_aliases: Dict[str, str] = {
        "project_name": "PROJECT_NAME",
        "api_v1_str": "API_V1_STR",
        "app_name": "APP_NAME",
        "environment": "ENVIRONMENT",
        "debug": "DEBUG",
        "database_url": "DATABASE_URL",
        "db_pool_size": "DB_POOL_SIZE",
        "db_max_overflow": "DB_MAX_OVERFLOW",
        "db_pool_timeout": "DB_POOL_TIMEOUT",
        "db_pool_recycle": "DB_POOL_RECYCLE",
        "redis_url": "REDIS_URL",
        "secret_key": "SECRET_KEY",
        "jwt_expiration_hours": "JWT_EXPIRATION_HOURS",
        "encryption_key": "ENCRYPTION_KEY",
        "log_level": "LOG_LEVEL",
        "log_file": "LOG_FILE",
        "log_file_path": "LOG_FILE_PATH",
        "log_max_size": "LOG_MAX_SIZE",
        "log_backup_count": "LOG_BACKUP_COUNT",
        "log_rotation_when": "LOG_ROTATION_WHEN",
        "log_rotation_interval": "LOG_ROTATION_INTERVAL",
        "enable_metrics": "ENABLE_METRICS",
        "metrics_port": "METRICS_PORT",
        "sentry_dsn": "SENTRY_DSN",
        "sentry_environment": "SENTRY_ENVIRONMENT",
        "sentry_traces_sample_rate": "SENTRY_TRACES_SAMPLE_RATE",
        "alert_email": "ALERT_EMAIL",
        "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
        "telegram_chat_id": "TELEGRAM_CHAT_ID",
        "default_trade_amount": "DEFAULT_TRADE_AMOUNT",
        "max_position_size": "MAX_POSITION_SIZE",
        "risk_percentage": "RISK_PERCENTAGE",
        "slippage_tolerance": "SLIPPAGE_TOLERANCE",
    }

    @classmethod
    def settings_customise_sources(
        cls,
        init_settings: SettingsSourceCallable,
        env_settings: SettingsSourceCallable,
        dotenv_settings: SettingsSourceCallable,
        file_secret_settings: SettingsSourceCallable,
    ) -> tuple[SettingsSourceCallable, ...]:
        """Load .env.<environment> before the default .env if present."""

        env = os.getenv("ENVIRONMENT", "development").lower()
        candidate_files: List[Path] = []

        env_specific = PROJECT_ROOT / f".env.{env}"
        if env_specific.exists():
            candidate_files.append(env_specific)

        root_env = PROJECT_ROOT / ".env"
        if root_env.exists():
            candidate_files.append(root_env)

        dotenv_sources = tuple(
            DotEnvSettingsSource(
                cls,
                env_file=path,
                case_sensitive=False,
                env_file_encoding="utf-8",
            )
            for path in candidate_files
        )

        return (init_settings, env_settings, *dotenv_sources, file_secret_settings)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _convert_cors(cls, value: Any) -> List[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                    raise ValueError("BACKEND_CORS_ORIGINS must be a JSON array or comma-separated string") from exc
                if isinstance(parsed, list):
                    return parsed
                raise ValueError("BACKEND_CORS_ORIGINS JSON value must be a list")
            return [item.strip() for item in value.split(",") if item.strip()]
        raise TypeError("Invalid BACKEND_CORS_ORIGINS value")

    @field_validator("DATA_COLLECTOR_CONFIG", mode="before")
    @classmethod
    def _parse_data_collector(cls, value: Any) -> Dict[str, Any]:
        if value is None or value == "":
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ValueError("DATA_COLLECTOR_CONFIG must be valid JSON") from exc
            if not isinstance(parsed, dict):
                raise ValueError("DATA_COLLECTOR_CONFIG must be a JSON object")
            return parsed
        raise TypeError("Unsupported DATA_COLLECTOR_CONFIG type")

    def model_post_init(self, __context: Any) -> None:  # pragma: no cover - simple filesystem setup
        self._ensure_paths()

    def _ensure_paths(self) -> None:
        log_file_path = self.resolve_path(self.log_file)
        for path in (
            log_file_path.parent,
            self.resolve_path(self.CONFIG_STORAGE_DIR),
            self.resolve_path(self.CONFIG_BACKUP_DIR),
            self.resolve_path(self.API_KEYS_STORE).parent,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate

    def data_collector_config(self) -> Dict[str, Any]:
        return deepcopy(self.DATA_COLLECTOR_CONFIG)

    def set_runtime_value(self, key: str, value: Any) -> None:
        field_name = self._runtime_aliases.get(key, key)
        if field_name not in self.model_fields:
            object.__setattr__(self, field_name, value)
            return
        object.__setattr__(self, field_name, value)

    def apply_from(self, other: "Settings") -> None:
        for field_name in self.model_fields:
            object.__setattr__(self, field_name, getattr(other, field_name))

    # Convenience accessors -------------------------------------------------

    @property
    def project_name(self) -> str:
        return self.PROJECT_NAME

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def debug(self) -> bool:
        return self.DEBUG

    @property
    def backend_cors_origins(self) -> List[str]:
        return self.BACKEND_CORS_ORIGINS

    @property
    def okx_api_key(self) -> str:
        return self.OKX_API_KEY

    @property
    def okx_secret_key(self) -> str:
        return self.OKX_SECRET_KEY

    @property
    def okx_passphrase(self) -> str:
        return self.OKX_PASSPHRASE

    @property
    def okx_api_base_url(self) -> str:
        return self.OKX_API_BASE_URL

    @property
    def okx_ws_public_url(self) -> str:
        return self.OKX_WS_PUBLIC_URL

    @property
    def okx_ws_private_url(self) -> str:
        return self.OKX_WS_PRIVATE_URL

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def secret_key(self) -> str:
        return self.SECRET_KEY

    @property
    def jwt_expiration_hours(self) -> int:
        return self.JWT_EXPIRATION_HOURS

    @property
    def encryption_key(self) -> Optional[str]:
        return self.ENCRYPTION_KEY

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def log_file(self) -> str:
        return self.LOG_FILE_PATH or self.LOG_FILE

    @property
    def log_max_size(self) -> int:
        return self.LOG_MAX_SIZE

    @property
    def log_backup_count(self) -> int:
        return self.LOG_BACKUP_COUNT

    @property
    def log_rotation_when(self) -> str:
        return self.LOG_ROTATION_WHEN

    @property
    def log_rotation_interval(self) -> int:
        return self.LOG_ROTATION_INTERVAL

    @property
    def enable_metrics(self) -> bool:
        return self.ENABLE_METRICS

    @property
    def metrics_port(self) -> int:
        return self.METRICS_PORT

    @property
    def sentry_dsn(self) -> Optional[str]:
        return self.SENTRY_DSN

    @property
    def sentry_environment(self) -> Optional[str]:
        return self.SENTRY_ENVIRONMENT or self.ENVIRONMENT

    @property
    def sentry_traces_sample_rate(self) -> float:
        return self.SENTRY_TRACES_SAMPLE_RATE

    @property
    def alert_email(self) -> Optional[str]:
        return self.ALERT_EMAIL

    @property
    def telegram_bot_token(self) -> Optional[str]:
        return self.TELEGRAM_BOT_TOKEN

    @property
    def telegram_chat_id(self) -> Optional[str]:
        return self.TELEGRAM_CHAT_ID

    @property
    def default_trade_amount(self) -> float:
        return self.DEFAULT_TRADE_AMOUNT

    @property
    def max_position_size(self) -> float:
        return self.MAX_POSITION_SIZE

    @property
    def risk_percentage(self) -> float:
        return self.RISK_PERCENTAGE

    @property
    def slippage_tolerance(self) -> float:
        return self.SLIPPAGE_TOLERANCE

    @property
    def config_storage_dir(self) -> Path:
        return self.resolve_path(self.CONFIG_STORAGE_DIR)

    @property
    def config_backup_dir(self) -> Path:
        return self.resolve_path(self.CONFIG_BACKUP_DIR)

    @property
    def strategy_config_dir(self) -> Path:
        return self.resolve_path(self.STRATEGY_CONFIG_DIR)

    @property
    def api_keys_store_path(self) -> Path:
        return self.resolve_path(self.API_KEYS_STORE)

    @property
    def config_audit_log_path(self) -> Path:
        return self.resolve_path(self.CONFIG_AUDIT_LOG)


settings = Settings()
