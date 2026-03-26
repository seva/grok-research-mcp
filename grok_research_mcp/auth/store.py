import json
import os
import time
from pathlib import Path

import win32crypt


class AuthRequired(Exception):
    pass


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


def is_expired(data: dict) -> bool:
    cookies = {c["name"]: c for c in data.get("cookies", [])}
    now = time.time()
    for name in ("sso", "sso-rw"):
        cookie = cookies.get(name)
        if not cookie or cookie.get("expires", 0) < now:
            return True
    return False
