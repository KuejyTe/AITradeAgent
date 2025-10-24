from __future__ import annotations

import json
import shutil
import threading
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.core.config import Settings, settings
from app.core.validators import ConfigValidator


DEFAULT_NOTIFICATION_SETTINGS: Dict[str, Any] = {
    "price_alerts": False,
    "order_updates": True,
    "email": None,
    "telegram": {
        "bot_token": None,
        "chat_id": None,
    },
    "wechat_webhook": None,
}


class ConfigAuditLogger:
    """Persist configuration change events to an append-only audit log."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self.log_path = log_path or settings.config_audit_log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, action: str, details: Dict[str, Any], actor: str = "system") -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "details": details,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False))
            handle.write("\n")


class SystemConfigManager:
    """Manage persisted system configuration and keep the runtime settings in sync."""

    _TRADING_FIELDS = {
        "default_trade_amount",
        "max_position_size",
        "risk_percentage",
        "slippage_tolerance",
    }

    def __init__(
        self,
        app_settings: Settings,
        config_file: Optional[Path] = None,
        audit_logger: Optional[ConfigAuditLogger] = None,
    ) -> None:
        self.settings = app_settings
        self.config_file = config_file or (self.settings.config_storage_dir / "system_config.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.audit_logger = audit_logger or ConfigAuditLogger()
        self.validator = ConfigValidator()
        self._config: Dict[str, Any] = {}
        self._load_overrides()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_overrides(self) -> None:
        if self.config_file.exists():
            with self.config_file.open("r", encoding="utf-8") as handle:
                try:
                    self._config = json.load(handle)
                except json.JSONDecodeError:
                    self._config = {}
        else:
            self._config = {}

        if self._config:
            self._apply_to_runtime(self._config)

    def _apply_to_runtime(self, updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            if key == "notifications":
                continue
            self.settings.set_runtime_value(key, value)

    def _write(self) -> None:
        payload = deepcopy(self._config)
        with self.config_file.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_config(self) -> Dict[str, Any]:
        """Return a sanitized snapshot of current configuration for API responses."""
        notifications = deepcopy(DEFAULT_NOTIFICATION_SETTINGS)
        notifications.update(self._config.get("notifications", {}))

        return {
            "app_name": self.settings.app_name,
            "environment": self.settings.environment,
            "debug": self.settings.debug,
            "default_trade_amount": self.settings.default_trade_amount,
            "max_position_size": self.settings.max_position_size,
            "risk_percentage": self.settings.risk_percentage,
            "slippage_tolerance": getattr(self.settings, "slippage_tolerance", 0.0),
            "log_level": self.settings.log_level,
            "okx_api_configured": bool(self.settings.okx_api_key),
            "database_configured": bool(self.settings.database_url),
            "notifications": notifications,
            "last_updated": self._config.get("last_updated"),
        }

    def update_config(self, data: Dict[str, Any], actor: str = "system") -> Dict[str, Any]:
        filtered = {key: value for key, value in data.items() if value is not None}

        trading_updates = {
            key: filtered[key]
            for key in self._TRADING_FIELDS
            if key in filtered
        }

        if trading_updates:
            snapshot = {
                "default_trade_amount": filtered.get("default_trade_amount", self.settings.default_trade_amount),
                "max_position_size": filtered.get("max_position_size", self.settings.max_position_size),
                "risk_percentage": filtered.get("risk_percentage", self.settings.risk_percentage),
                "slippage_tolerance": filtered.get("slippage_tolerance", getattr(self.settings, "slippage_tolerance", 0.0)),
            }
            if not self.validator.validate_trading_params(snapshot):
                raise ValueError("Invalid trading configuration parameters supplied")

        notifications = filtered.get("notifications")
        if notifications:
            merged_notifications = deepcopy(DEFAULT_NOTIFICATION_SETTINGS)
            merged_notifications.update(self._config.get("notifications", {}))
            merged_notifications.update(notifications)
            filtered["notifications"] = merged_notifications

        filtered["last_updated"] = datetime.utcnow().isoformat()

        self._config.update(filtered)
        self._apply_to_runtime(filtered)
        self._write()

        if self.audit_logger:
            audit_payload = {key: value for key, value in filtered.items() if key != "notifications"}
            self.audit_logger.log("update_system_config", audit_payload, actor=actor)

        return self.get_config()

    def reload(self) -> None:
        """Reload configuration from disk and apply to runtime settings."""
        self._load_overrides()


class ConfigBackup:
    """Create and restore backups of configuration artefacts."""

    def __init__(
        self,
        system_manager: SystemConfigManager,
        backup_dir: Optional[Path] = None,
        tracked_files: Optional[Iterable[Path]] = None,
    ) -> None:
        self.system_manager = system_manager
        self.backup_dir = backup_dir or settings.config_backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        default_files = [
            self.system_manager.config_file,
            settings.api_keys_store_path,
        ]
        if tracked_files:
            default_files.extend(tracked_files)
        # Ensure uniqueness while preserving order
        seen: set[Path] = set()
        self.tracked_files: List[Path] = []
        for file_path in default_files:
            if file_path in seen:
                continue
            seen.add(file_path)
            self.tracked_files.append(file_path)

    def backup_config(self) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        target_dir = self.backup_dir / timestamp
        target_dir.mkdir(parents=True, exist_ok=False)

        copied: List[str] = []
        for file_path in self.tracked_files:
            if file_path.exists():
                shutil.copy2(file_path, target_dir / file_path.name)
                copied.append(file_path.name)

        manifest = {
            "created_at": datetime.utcnow().isoformat(),
            "files": copied,
        }
        with (target_dir / "manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)

        if self.system_manager.audit_logger:
            self.system_manager.audit_logger.log("backup_config", manifest)

        return timestamp

    def restore_config(self, backup_id: str) -> None:
        source_dir = self.backup_dir / backup_id
        if not source_dir.exists() or not source_dir.is_dir():
            raise FileNotFoundError(f"Backup '{backup_id}' not found")

        for file_path in source_dir.iterdir():
            if file_path.name == "manifest.json":
                continue
            destination = next(
                (tracked for tracked in self.tracked_files if tracked.name == file_path.name),
                None,
            )
            if destination:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, destination)

        self.system_manager.reload()

        if self.system_manager.audit_logger:
            self.system_manager.audit_logger.log("restore_config", {"backup_id": backup_id})

    def list_backups(self) -> List[Dict[str, Any]]:
        backups: List[Dict[str, Any]] = []
        if not self.backup_dir.exists():
            return backups

        for entry in sorted(self.backup_dir.iterdir(), reverse=True):
            if not entry.is_dir():
                continue
            manifest_path = entry / "manifest.json"
            manifest: Dict[str, Any] = {}
            if manifest_path.exists():
                with manifest_path.open("r", encoding="utf-8") as handle:
                    try:
                        manifest = json.load(handle)
                    except json.JSONDecodeError:
                        manifest = {}
            backups.append({"backup_id": entry.name, **manifest})
        return backups


class ConfigReloader:
    """Reload application settings on demand or when files change."""

    def __init__(self, app_settings: Settings, system_manager: SystemConfigManager) -> None:
        self.settings = app_settings
        self.system_manager = system_manager

    def reload_config(self) -> Settings:
        fresh = Settings()
        self.settings.apply_from(fresh)
        self.system_manager.reload()
        return self.settings

    def watch_config_changes(
        self,
        interval_seconds: float = 5.0,
        stop_event: Optional[threading.Event] = None,
    ) -> threading.Thread:
        """Start a background watcher that reloads when the system config file changes."""

        config_path = self.system_manager.config_file

        def _worker() -> None:
            try:
                last_mtime = config_path.stat().st_mtime if config_path.exists() else None
            except FileNotFoundError:
                last_mtime = None

            while stop_event is None or not stop_event.is_set():
                try:
                    current_mtime = config_path.stat().st_mtime if config_path.exists() else None
                except FileNotFoundError:
                    current_mtime = None

                if current_mtime and current_mtime != last_mtime:
                    self.reload_config()
                    last_mtime = current_mtime

                time.sleep(interval_seconds)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread
