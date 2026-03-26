import sys
import subprocess
import time
from unittest.mock import patch

import anyio
import pytest
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp.client.session import ClientSession
from mcp.shared.message import SessionMessage
from mcp.types import TextContent

from grok_research_mcp.auth.store import save
from grok_research_mcp.server import mcp


# ---------------------------------------------------------------------------
# Test 1 — startup guards
# ---------------------------------------------------------------------------

def test_run_exits_when_auth_missing(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "grok_research_mcp", "serve"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "GROK_MCP_DIR": str(tmp_path)},
    )
    assert result.returncode == 1
    assert "Auth required" in result.stderr


def test_run_exits_when_auth_expired(tmp_path):
    expired_auth = {
        "cookies": [
            {"name": "sso",    "value": "x", "expires": time.time() - 1,
             "domain": ".grok.com", "path": "/"},
            {"name": "sso-rw", "value": "y", "expires": time.time() - 1,
             "domain": ".grok.com", "path": "/"},
        ],
        "statsig_id": "fake",
    }
    import os
    old = os.environ.get("GROK_MCP_DIR")
    os.environ["GROK_MCP_DIR"] = str(tmp_path)
    try:
        save(expired_auth)
    finally:
        if old is None:
            del os.environ["GROK_MCP_DIR"]
        else:
            os.environ["GROK_MCP_DIR"] = old

    result = subprocess.run(
        [sys.executable, "-m", "grok_research_mcp", "serve"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "GROK_MCP_DIR": str(tmp_path)},
    )
    assert result.returncode == 1
    assert "Auth expired" in result.stderr


# ---------------------------------------------------------------------------
# Test 2 — tool registration (no transport)
# ---------------------------------------------------------------------------

def test_tool_registration():
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}

    assert "grok_web_search_tool" in tools
    assert "grok_x_search_tool" in tools

    for name in ("grok_web_search_tool", "grok_x_search_tool"):
        schema = tools[name].parameters
        props = schema.get("properties", {})
        assert "query" in props, f"{name}: missing 'query' parameter"
        assert props["query"].get("type") == "string", f"{name}: 'query' must be type string"


# ---------------------------------------------------------------------------
# Test 3 — JSON-RPC round-trip (in-process memory streams)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_tool_round_trip():
    client_to_server_send, client_to_server_recv = anyio.create_memory_object_stream[
        SessionMessage | Exception
    ](16)
    server_to_client_send, server_to_client_recv = anyio.create_memory_object_stream[
        SessionMessage
    ](16)

    async def _run_server():
        await mcp._mcp_server.run(
            client_to_server_recv,
            server_to_client_send,
            mcp._mcp_server.create_initialization_options(),
            raise_exceptions=True,
        )

    with patch("grok_research_mcp.server.grok_web_search", return_value="Mocked result."):
        async with anyio.create_task_group() as tg:
            tg.start_soon(_run_server)

            async with ClientSession(
                server_to_client_recv,
                client_to_server_send,
            ) as client:
                await client.initialize()

                result = await client.call_tool(
                    "grok_web_search_tool", {"query": "test query"}
                )

                tg.cancel_scope.cancel()

    assert not result.isError
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == "Mocked result."
