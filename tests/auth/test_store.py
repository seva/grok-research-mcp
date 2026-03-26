import time
from pathlib import Path
import pytest

from grok_research_mcp.auth.store import save, load, is_expired, AuthRequired


SAMPLE = {
    "cookies": [
        {"name": "sso", "value": "abc123", "expires": time.time() + 3600, "domain": ".grok.com"},
        {"name": "sso-rw", "value": "def456", "expires": time.time() + 3600, "domain": ".grok.com"},
    ]
}


def test_save_writes_to_expected_path(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    save(SAMPLE)
    assert (tmp_path / "auth.dpapi").exists()


def test_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    save(SAMPLE)
    result = load()
    assert result["cookies"][0]["name"] == "sso"
    assert result["cookies"][0]["value"] == "abc123"


def test_load_raises_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    with pytest.raises(AuthRequired):
        load()


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


def test_load_raises_on_corrupt_blob(tmp_path, monkeypatch):
    monkeypatch.setenv("GROK_MCP_DIR", str(tmp_path))
    (tmp_path / "auth.dpapi").write_bytes(b"not-a-valid-dpapi-blob")
    with pytest.raises(AuthRequired):
        load()
