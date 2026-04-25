import json
import os
from pathlib import Path

import win32crypt

from grok_research_mcp.auth.store_base import AuthRequired, is_expired

__all__ = ["save", "load", "is_expired", "AuthRequired"]


def _auth_path() -> Path:
    return Path(os.environ.get("GROK_MCP_DIR", Path.home() / ".grok-mcp")) / "auth.dpapi"


def save(data: dict) -> None:
    path = _auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(data).encode()
    encrypted = win32crypt.CryptProtectData(blob, None, None, None, None, 0)
    path.write_bytes(encrypted)


def load() -> dict:
    path = _auth_path()
    if not path.exists():
        raise AuthRequired("No auth file found. Run: python -m grok_research_mcp auth")
    try:
        encrypted = path.read_bytes()
        _, blob = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        return json.loads(blob.decode())
    except Exception as e:
        raise AuthRequired(f"Auth file corrupt or unreadable: {e}. Run: python -m grok_research_mcp auth")
