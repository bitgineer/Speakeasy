"""Provider credential storage backed by ``~/.speakeasy/secrets.json``.

Keys stay outside ``AppSettings`` so no settings response, wire schema, or log
line can carry one. Only this module reads key material.
"""

import json
import logging
import os
import tempfile
from pathlib import Path

from .settings import get_data_dir

logger = logging.getLogger(__name__)


def _secrets_path(path: Path | None) -> Path:
    return path if path is not None else get_data_dir() / "secrets.json"


def _read_keys(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning(f"Secrets file at {path} is unreadable, treating it as empty")
        return {}
    if not isinstance(data, dict):
        logger.warning(f"Secrets file at {path} is not a mapping, treating it as empty")
        return {}
    return {
        provider_id: key
        for provider_id, key in data.items()
        if isinstance(provider_id, str) and isinstance(key, str)
    }


def _write_keys(path: Path, keys: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(keys, stream, indent=2)
        try:
            os.chmod(temp_name, 0o600)
        except OSError:
            # Windows only supports the read-only bit; the write still stands.
            pass
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def get_key(provider_id: str, path: Path | None = None) -> str | None:
    """Return the stored key for a provider, or None when absent."""
    return _read_keys(_secrets_path(path)).get(provider_id)


def set_key(provider_id: str, key: str, path: Path | None = None) -> None:
    """Store a key for a provider. An empty key deletes the entry."""
    secrets_path = _secrets_path(path)
    keys = _read_keys(secrets_path)
    if key:
        keys[provider_id] = key
        logger.info(f"Stored key for provider {provider_id}")
    else:
        keys.pop(provider_id, None)
        logger.info(f"Cleared key for provider {provider_id}")
    _write_keys(secrets_path, keys)
