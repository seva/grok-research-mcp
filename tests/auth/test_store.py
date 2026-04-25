import sys
import time
from unittest.mock import patch, MagicMock
import pytest

from grok_research_mcp.auth.store import save, load, is_expired, AuthRequired


SAMPLE = {
    "cookies": [
        {"name": "sso", "value": "abc123", "expires": time.time() + 3600, "domain": ".grok.com"},
        {"name": "sso-rw", "value": "def456", "expires": time.time() + 3600, "domain": ".grok.com"},
    ]
}

# ---------------------------------------------------------------------------
# Windows DPAPI tests — skipped on non-Windows
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
def test_save_writes_to_expected_path(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    save(SAMPLE)
    assert (tmp_path / "auth.dpapi").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
def test_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    save(SAMPLE)
    result = load()
    assert result["cookies"][0]["name"] == "sso"
    assert result["cookies"][0]["value"] == "abc123"


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
def test_load_raises_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    with pytest.raises(AuthRequired):
        load()


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
def test_load_raises_on_corrupt_blob(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    (tmp_path / "auth.dpapi").write_bytes(b"not-a-valid-dpapi-blob")
    with pytest.raises(AuthRequired):
        load()


# ---------------------------------------------------------------------------
# macOS keyring tests — skipped on non-macOS
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform != "darwin", reason="keyring path only on macOS")
def test_save_calls_keyring_set_password():
    import json
    with patch("grok_research_mcp.auth.store_darwin.keyring") as mock_kr:
        save(SAMPLE)
        mock_kr.set_password.assert_called_once_with(
            "grok-research-mcp", "auth", json.dumps(SAMPLE)
        )


@pytest.mark.skipif(sys.platform != "darwin", reason="keyring path only on macOS")
def test_load_roundtrip_keyring():
    import json
    with patch("grok_research_mcp.auth.store_darwin.keyring") as mock_kr:
        mock_kr.get_password.return_value = json.dumps(SAMPLE)
        result = load()
        assert result["cookies"][0]["name"] == "sso"
        assert result["cookies"][0]["value"] == "abc123"
        mock_kr.get_password.assert_called_once_with("grok-research-mcp", "auth")


@pytest.mark.skipif(sys.platform != "darwin", reason="keyring path only on macOS")
def test_load_raises_when_missing_keyring():
    with patch("grok_research_mcp.auth.store_darwin.keyring") as mock_kr:
        mock_kr.get_password.return_value = None
        with pytest.raises(AuthRequired):
            load()


@pytest.mark.skipif(sys.platform != "darwin", reason="keyring path only on macOS")
def test_load_raises_on_corrupt_value_keyring():
    with patch("grok_research_mcp.auth.store_darwin.keyring") as mock_kr:
        mock_kr.get_password.return_value = "not-valid-json{{{"
        with pytest.raises(AuthRequired):
            load()


# ---------------------------------------------------------------------------
# is_expired — no platform dependency
# ---------------------------------------------------------------------------

def test_is_expired_past():
    data = {
        "cookies": [
            {"name": "sso", "value": "x", "expires": time.time() - 1},
        ]
    }
    assert is_expired(data) is True


def test_is_expired_future():
    data = {
        "cookies": [
            {"name": "sso", "value": "x", "expires": time.time() + 3600},
            {"name": "sso-rw", "value": "y", "expires": time.time() + 3600},
        ]
    }
    assert is_expired(data) is False


def test_is_expired_missing_sso_rw():
    data = {
        "cookies": [
            {"name": "sso", "value": "x", "expires": time.time() + 3600},
        ]
    }
    assert is_expired(data) is True


def test_is_expired_sso_rw_expired():
    data = {
        "cookies": [
            {"name": "sso", "value": "x", "expires": time.time() + 3600},
            {"name": "sso-rw", "value": "y", "expires": time.time() - 1},
        ]
    }
    assert is_expired(data) is True
