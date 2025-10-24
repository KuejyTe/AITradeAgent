from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.config_service import (
    ConfigAuditLogger,
    ConfigBackup,
    ConfigReloader,
    SystemConfigManager,
)
from app.core.security import APIKeyManager, SecureStorage
from app.core.strategy_config import StrategyConfigManager
from app.core.validators import ConfigValidator


router = APIRouter(prefix="/config", tags=["Configuration"])

validator = ConfigValidator()
audit_logger = ConfigAuditLogger()
system_config_manager = SystemConfigManager(settings, audit_logger=audit_logger)
config_backup = ConfigBackup(system_config_manager)
config_reloader = ConfigReloader(settings, system_config_manager)
strategy_config_manager = StrategyConfigManager()

try:
    secure_storage = SecureStorage()
    api_key_manager: APIKeyManager | None = APIKeyManager(
        secure_storage,
        audit_logger=audit_logger,
    )
except ValueError:
    secure_storage = None
    api_key_manager = None


class APIKeysInput(BaseModel):
    api_key: str = Field(..., min_length=10)
    secret_key: str = Field(..., min_length=10)
    passphrase: str = Field(..., min_length=4)


class TelegramSettings(BaseModel):
    bot_token: str | None = None
    chat_id: str | None = None


class NotificationSettings(BaseModel):
    price_alerts: bool | None = None
    order_updates: bool | None = None
    email: str | None = None
    telegram: TelegramSettings | None = None
    wechat_webhook: str | None = None

    def model_dump_filtered(self) -> Dict[str, Any]:
        payload = self.model_dump(exclude_unset=True)
        if "telegram" in payload and payload["telegram"] is None:
            payload.pop("telegram")
        return payload


class SystemConfigUpdate(BaseModel):
    app_name: str | None = None
    environment: str | None = Field(None, description="Environment identifier")
    debug: bool | None = None
    default_trade_amount: float | None = Field(None, ge=0)
    max_position_size: float | None = Field(None, ge=0)
    risk_percentage: float | None = Field(None, ge=0, le=1)
    slippage_tolerance: float | None = Field(None, ge=0)
    log_level: str | None = None
    notifications: NotificationSettings | None = None

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = self.model_dump(exclude_unset=True)
        notification_settings = payload.get("notifications")
        if isinstance(notification_settings, NotificationSettings):
            payload["notifications"] = notification_settings.model_dump_filtered()
        return payload


@router.get("/system")
async def get_system_config() -> Dict[str, Any]:
    """Retrieve the current system configuration with sensitive values redacted."""
    return system_config_manager.get_config()


@router.put("/system")
async def update_system_config(config: SystemConfigUpdate, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    payload = config.to_payload()

    if {"default_trade_amount", "max_position_size", "risk_percentage", "slippage_tolerance"}.intersection(payload):
        trading_snapshot = {
            "default_trade_amount": payload.get("default_trade_amount", settings.default_trade_amount),
            "max_position_size": payload.get("max_position_size", settings.max_position_size),
            "risk_percentage": payload.get("risk_percentage", settings.risk_percentage),
            "slippage_tolerance": payload.get("slippage_tolerance", settings.slippage_tolerance),
        }
        if not validator.validate_trading_params(trading_snapshot):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid trading configuration")

    try:
        result = system_config_manager.update_config(payload, actor="api")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # Persist a backup asynchronously after successful updates
    background_tasks.add_task(config_backup.backup_config)
    return result


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def save_api_keys(keys: APIKeysInput) -> Dict[str, Any]:
    if api_key_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encryption key is not configured. Set ENCRYPTION_KEY before saving API credentials.",
        )

    if not validator.validate_api_keys(keys.api_key, keys.secret_key, keys.passphrase):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="API credentials failed validation")

    metadata = api_key_manager.save_api_keys(keys.api_key, keys.secret_key, keys.passphrase, actor="api")
    return {"message": "API credentials stored securely", **metadata}


@router.get("/api-keys/status")
async def get_api_keys_status() -> Dict[str, Any]:
    if api_key_manager is None:
        return {
            "configured": False,
            "reason": "ENCRYPTION_KEY is not configured",
        }
    return api_key_manager.get_status()


@router.post("/api-keys/test")
async def test_api_connection() -> Dict[str, Any]:
    if api_key_manager is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Encryption key missing")

    # In a real implementation this would reach out to the exchange.
    return {
        "status": "success",
        "message": "API connectivity verified (mock)",
    }


@router.get("/strategies/{strategy_id}")
async def get_strategy_config(strategy_id: str) -> Dict[str, Any]:
    try:
        return strategy_config_manager.load_strategy_config(strategy_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/strategies/{strategy_id}")
async def update_strategy_config(strategy_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        strategy_config_manager.save_strategy_config(strategy_id, config)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    audit_logger.log(
        action="update_strategy_config",
        details={"strategy_id": strategy_id},
        actor="api",
    )

    return {
        "message": "Strategy configuration updated",
        "strategy_id": strategy_id,
    }


@router.post("/reload")
async def reload_configuration() -> Dict[str, Any]:
    config_reloader.reload_config()
    audit_logger.log("reload_config", {"source": "api"})
    return {"message": "Configuration reloaded"}


@router.get("/backups")
async def list_backups() -> Dict[str, Any]:
    return {"backups": config_backup.list_backups()}
