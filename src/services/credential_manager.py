"""Credential management with SecretStorage (keyring) integration."""

import base64
import json
import os
from pathlib import Path
from typing import Optional

try:
    import secretstorage
    HAS_SECRETSTORAGE = True
except ImportError:
    HAS_SECRETSTORAGE = False

from src.services.config_manager import CONFIG_DIR


KEYRING_LABEL = "PipeRDC RDP Connections"


class CredentialManager:
    """Manages RDP credentials using the system keyring."""

    def __init__(self):
        self._collection = None
        self._connection = None

    def _get_collection(self):
        """Get the default secret storage collection."""
        if not HAS_SECRETSTORAGE:
            return None
        if self._collection is not None:
            return self._collection
        try:
            self._connection = secretstorage.dbus_init()
            self._collection = secretstorage.get_default_collection(self._connection)
            if not self._collection.is_locked():
                self._collection.unlock()
            return self._collection
        except Exception:
            return None

    def store_password(self, conn_id: str, password: str) -> bool:
        """Store password for a connection in the system keyring."""
        collection = self._get_collection()
        if collection is None:
            return self._store_password_fallback(conn_id, password)

        try:
            # Delete existing items with this label
            for item in collection.get_all_items():
                if item.get_label() == f"{KEYRING_LABEL} - {conn_id}":
                    item.delete()

            collection.create_item(
                f"{KEYRING_LABEL} - {conn_id}",
                {"application": "piperdc", "connection_id": conn_id},
                password,
                replace=True,
            )
            return True
        except Exception:
            return self._store_password_fallback(conn_id, password)

    def get_password(self, conn_id: str) -> Optional[str]:
        """Retrieve password from the system keyring."""
        collection = self._get_collection()
        if collection is None:
            return self._get_password_fallback(conn_id)

        try:
            for item in collection.get_all_items():
                if item.get_label() == f"{KEYRING_LABEL} - {conn_id}":
                    secret = item.get_secret()
                    if isinstance(secret, bytes):
                        return secret.decode("utf-8")
                    return str(secret)
            return None
        except Exception:
            return self._get_password_fallback(conn_id)

    def delete_password(self, conn_id: str) -> bool:
        """Delete password from the system keyring."""
        collection = self._get_collection()
        if collection is None:
            return self._delete_password_fallback(conn_id)

        try:
            for item in collection.get_all_items():
                if item.get_label() == f"{KEYRING_LABEL} - {conn_id}":
                    item.delete()
                    return True
            return True
        except Exception:
            return self._delete_password_fallback(conn_id)

    # Fallback: store in an obfuscated file if keyring unavailable
    def _get_fallback_path(self) -> Path:
        """Get path to fallback credential store."""
        return CONFIG_DIR / ".creds"

    def _obfuscate(self, data: str) -> str:
        """Simple obfuscation (not encryption - use keyring for real security)."""
        return base64.b64encode(data.encode()).decode()

    def _deobfuscate(self, data: str) -> str:
        """Reverse obfuscation."""
        try:
            return base64.b64decode(data.encode()).decode()
        except Exception:
            return ""

    def _store_password_fallback(self, conn_id: str, password: str) -> bool:
        """Fallback: store password in obfuscated file."""
        try:
            fallback_path = self._get_fallback_path()
            creds = {}
            if fallback_path.exists():
                try:
                    raw = fallback_path.read_text()
                    decoded = self._deobfuscate(raw)
                    creds = json.loads(decoded)
                except Exception:
                    creds = {}

            creds[conn_id] = password
            fallback_path.write_text(self._obfuscate(json.dumps(creds)))
            fallback_path.chmod(0o600)
            return True
        except Exception:
            return False

    def _get_password_fallback(self, conn_id: str) -> Optional[str]:
        """Fallback: retrieve password from obfuscated file."""
        try:
            fallback_path = self._get_fallback_path()
            if not fallback_path.exists():
                return None
            raw = fallback_path.read_text()
            decoded = self._deobfuscate(raw)
            creds = json.loads(decoded)
            return creds.get(conn_id)
        except Exception:
            return None

    def _delete_password_fallback(self, conn_id: str) -> bool:
        """Fallback: delete password from obfuscated file."""
        try:
            fallback_path = self._get_fallback_path()
            if not fallback_path.exists():
                return True
            raw = fallback_path.read_text()
            decoded = self._deobfuscate(raw)
            creds = json.loads(decoded)
            creds.pop(conn_id, None)
            fallback_path.write_text(self._obfuscate(json.dumps(creds)))
            return True
        except Exception:
            return False