import json
import os
from pathlib import Path

import keyring

from grok_research_mcp.auth.store_base import is_expired, AuthRequired

_SERVICE = "grok-research-mcp"
_USERNAME = "auth"


def _test_path() -> Path | None:
    """Return a file path when GROK_MCP_DIR is set (test isolation). None in production."""
    d = os.environ.get("GROK_MCP_DIR")
    return Path(d) / "auth.json" if d else None


def save(data: dict) -> None:
    path = _test_path()
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    else:
        keyring.set_password(_SERVICE, _USERNAME, json.dumps(data))


def load() -> dict:
    path = _test_path()
    if path is not None:
        if not path.exists():
            raise AuthRequired("No auth file found. Run: python -m grok_research_mcp auth")
        try:
            return json.loads(path.read_text())
        except Exception as e:
            raise AuthRequired(f"Auth file corrupt or unreadable: {e}. Run: python -m grok_research_mcp auth")
    try:
        value = keyring.get_password(_SERVICE, _USERNAME)
        if value is None:
            raise AuthRequired("No auth found in Keychain. Run: python -m grok_research_mcp auth")
        return json.loads(value)
    except AuthRequired:
        raise
    except Exception as e:
        raise AuthRequired(f"Auth unreadable: {e}. Run: python -m grok_research_mcp auth")
