import sys
import subprocess
from io import StringIO
from unittest.mock import patch
import pytest

from grok_research_mcp.__main__ import main


def test_no_args_usage_includes_query():
    with patch("sys.argv", ["grok_research_mcp"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1


def test_query_routes_to_web_search_by_default():
    async def _mock_web(q, **kwargs):
        return f"web:{q}"

    with patch("sys.argv", ["grok_research_mcp", "query", "test", "query"]):
        with patch("grok_research_mcp.tools.research.grok_web_search", _mock_web):
            with patch("sys.stdout", new_callable=StringIO) as mock_out:
                main()

    assert "web:test query" in mock_out.getvalue()


def test_query_mode_x_routes_to_x_search():
    async def _mock_x(q, **kwargs):
        return f"x:{q}"

    with patch("sys.argv", ["grok_research_mcp", "query", "--mode", "x", "xai news"]):
        with patch("grok_research_mcp.tools.research.grok_x_search", _mock_x):
            with patch("sys.stdout", new_callable=StringIO) as mock_out:
                main()

    assert "x:xai news" in mock_out.getvalue()


def test_query_error_result_goes_to_stderr_and_exits_1():
    async def _mock_error(q, **kwargs):
        return "Error: Auth required. Run: python -m grok_research_mcp auth"

    with patch("sys.argv", ["grok_research_mcp", "query", "test"]):
        with patch("grok_research_mcp.tools.research.grok_web_search", _mock_error):
            with patch("sys.stderr", new_callable=StringIO) as mock_err:
                with pytest.raises(SystemExit) as exc:
                    main()

    assert exc.value.code == 1
    assert "Error:" in mock_err.getvalue()


def test_query_reasoning_flag_passed_through():
    captured = {}

    async def _mock_web(q, **kwargs):
        captured.update(kwargs)
        return "result"

    with patch("sys.argv", ["grok_research_mcp", "query", "--reasoning", "test"]):
        with patch("grok_research_mcp.tools.research.grok_web_search", _mock_web):
            with patch("sys.stdout", new_callable=StringIO):
                main()

    assert captured.get("is_reasoning") is True


def test_query_unicode_output_does_not_crash():
    async def _mock_web(q, **kwargs):
        return "result with emoji 😊 and unicode — café"

    with patch("sys.argv", ["grok_research_mcp", "query", "test"]):
        with patch("grok_research_mcp.tools.research.grok_web_search", _mock_web):
            with patch("sys.stdout", new_callable=StringIO) as mock_out:
                main()

    assert "😊" in mock_out.getvalue()


def test_query_auth_missing_exits_1_via_subprocess(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "grok_research_mcp", "query", "test"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "GROK_MCP_DIR": str(tmp_path)},
    )
    assert result.returncode == 1
    assert result.stderr
