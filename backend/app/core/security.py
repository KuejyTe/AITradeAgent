from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class SecureStorage:
    """Encryption helper built on top of Fernet symmetric encryption."""

    def __init__(self, encryption_key: Optional[str] = None) -> None:
        key = encryption_key or settings.encryption_key
        if not key:
            raise ValueError(
                "Encryption key is required. Set ENCRYPTION_KEY in your environment or configuration."
            )

        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key

        try:
            self._cipher = Fernet(key_bytes)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid encryption key supplied to SecureStorage") from exc

    def encrypt(self, data: str) -> str:
        """Encrypt a string value."""
        if data is None:
            raise ValueError("Cannot encrypt None values")
        if data == "":
            return ""
        token = self._cipher.encrypt(data.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a token produced by :meth:`encrypt`."""
        if encrypted_data is None:
            raise ValueError("Cannot decrypt None values")
        if encrypted_data == "":
            return ""
        try:
            value = self._cipher.decrypt(encrypted_data.encode("utf-8"))
        except InvalidToken as exc:
            raise ValueError("Encrypted payload is invalid or has been tampered with") from exc
        return value.decode("utf-8")

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet compatible base64 key."""
        return Fernet.generate_key().decode("utf-8")


class APIKeyManager:
    """Manage encrypted storage of exchange API credentials."""

    def __init__(
        self,
        storage: SecureStorage,
        store_path: Optional[Path] = None,
        audit_logger: Optional["ConfigAuditLogger"] = None,
    ) -> None:
        self.storage = storage
        self.store_path = store_path or settings.api_keys_store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._cached_keys: Optional[Dict[str, str]] = None
        self._metadata: Dict[str, Any] = {}
        self.audit_logger = audit_logger

    def _read_store(self) -> Optional[Dict[str, Any]]:
        if not self.store_path.exists():
            return None
        with self.store_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_store(self, payload: Dict[str, Any]) -> None:
        with self.store_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def save_api_keys(
        self,
        api_key: str,
        secret_key: str,
        passphrase: str,
        actor: str = "system",
    ) -> Dict[str, Any]:
        """Encrypt and persist API credentials."""
        encrypted = {
            "api_key": self.storage.encrypt(api_key),
            "secret_key": self.storage.encrypt(secret_key),
            "passphrase": self.storage.encrypt(passphrase),
        }

        metadata = {"updated_at": datetime.utcnow().isoformat()}
        self._write_store({**encrypted, **metadata})

        # cache decrypted copy for quick retrieval during the request lifecycle
        self._cached_keys = {
            "api_key": api_key,
            "secret_key": secret_key,
            "passphrase": passphrase,
        }
        self._metadata = metadata

        if self.audit_logger:
            self.audit_logger.log(
                action="save_api_keys",
                details={"updated_at": metadata["updated_at"]},
                actor=actor,
            )

        return metadata

    def get_api_keys(self) -> Dict[str, Any]:
        """Return decrypted API credentials for internal use."""
        if self._cached_keys is None:
            stored = self._read_store()
            if not stored:
                return {}
            self._cached_keys = {
                "api_key": self.storage.decrypt(stored["api_key"]),
                "secret_key": self.storage.decrypt(stored["secret_key"]),
                "passphrase": self.storage.decrypt(stored["passphrase"]),
            }
            self._metadata = {"updated_at": stored.get("updated_at")}

        return {**self._cached_keys, **self._metadata}

    def get_status(self) -> Dict[str, Any]:
        """Return a redacted summary for UI consumption."""
        stored = self._read_store()
        if not stored:
            return {"configured": False}

        updated_at = stored.get("updated_at")
        preview = None
        try:
            preview = self.storage.decrypt(stored["api_key"])
        except Exception:  # pragma: no cover - defensive
            preview = ""

        masked = f"{preview[:4]}***{preview[-2:]}" if preview else None
        return {
            "configured": True,
            "api_key_preview": masked,
            "updated_at": updated_at,
        }

    def clear_cache(self) -> None:
        self._cached_keys = None
        self._metadata = {}


# Local import to avoid circular dependency in type checking
from app.core.config_service import ConfigAuditLogger  # noqa: E402  # isort:skip
