import json
import keyring

from grok_research_mcp.auth.store_base import is_expired, AuthRequired

_SERVICE = "grok-research-mcp"
_USERNAME = "auth"


def save(data: dict) -> None:
    keyring.set_password(_SERVICE, _USERNAME, json.dumps(data))


def load() -> dict:
    try:
        value = keyring.get_password(_SERVICE, _USERNAME)
        if value is None:
            raise AuthRequired("No auth found in Keychain. Run: python -m grok_research_mcp auth")
        return json.loads(value)
    except AuthRequired:
        raise
    except Exception as e:
        raise AuthRequired(f"Auth unreadable: {e}. Run: python -m grok_research_mcp auth")
