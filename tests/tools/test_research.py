import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

import grok_research_mcp.tools.research as research_module
from grok_research_mcp.tools.research import grok_web_search, grok_x_search, _format_result
from grok_research_mcp.client.session import AccessDenied


SAMPLE_TOKENS = ["Paris is the ", "capital of France."]
SAMPLE_CITATIONS = [
    {"title": "France - Wikipedia", "url": "https://en.wikipedia.org/wiki/France"},
    {"title": "Paris Official Site", "url": "https://www.paris.fr"},
]
CANONICAL_MESSAGE = "Paris is the capital of France."


def test_format_result_with_citations():
    result = _format_result("Paris is the capital of France.", SAMPLE_CITATIONS)
    assert "Paris is the capital of France." in result
    assert "Sources:" in result
    assert "- [France - Wikipedia](https://en.wikipedia.org/wiki/France)" in result
    assert "- [Paris Official Site](https://www.paris.fr)" in result


def test_format_result_no_citations():
    result = _format_result("Simple answer.", [])
    assert "Simple answer." in result
    assert "Sources:" not in result


@pytest.fixture
def mock_send():
    """Mock send_message to yield tokens then model_response."""
    async def _gen(*args, **kwargs):
        for token in SAMPLE_TOKENS:
            yield token, None, None
        yield None, "conv-abc", None
        yield None, None, {"webSearchResults": [
            {"title": "France - Wikipedia", "url": "https://en.wikipedia.org/wiki/France", "preview": "..."},
            {"title": "Paris Official Site", "url": "https://www.paris.fr", "preview": "..."},
        ]}

    return _gen


@pytest.fixture
def mock_send_with_canonical():
    """Mock where modelResponse.message differs from streamed tokens."""
    async def _gen(*args, **kwargs):
        yield "wrong streamed ", None, None
        yield "tokens", None, None
        yield None, "conv-abc", None
        yield None, None, {
            "message": CANONICAL_MESSAGE,
            "webSearchResults": [
                {"title": "France - Wikipedia", "url": "https://en.wikipedia.org/wiki/France", "preview": "..."},
            ],
        }

    return _gen


@pytest.fixture
def mock_send_with_render_tags():
    """Mock where modelResponse.message contains grok:render citation tags."""
    async def _gen(*args, **kwargs):
        yield None, "conv-abc", None
        yield None, None, {
            "message": (
                "Paris is the capital of France"
                '<grok:render card_id="85dac1" card_type="citation_card"'
                ' type="render_inline_citation">'
                '<argument name="citation_id">21</argument>'
                "</grok:render>"
                " and a major European city."
                '<grok:render card_id="f3a9c2" card_type="citation_card"'
                ' type="render_inline_citation">'
                '<argument name="citation_id">5</argument>'
                "</grok:render>"
            ),
            "webSearchResults": [],
        }

    return _gen


@pytest.mark.asyncio
async def test_grok_web_search_returns_text_and_sources(mock_send):
    with patch("grok_research_mcp.tools.research.send_message", mock_send):
        with patch("grok_research_mcp.tools.research._get_session") as mock_session_ctx:
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await grok_web_search("capital of France")

    assert "Paris is the capital of France." in result
    assert "Sources:" in result
    assert "France - Wikipedia" in result


@pytest.mark.asyncio
async def test_grok_render_tags_stripped_from_response(mock_send_with_render_tags):
    with patch("grok_research_mcp.tools.research.send_message", mock_send_with_render_tags):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await grok_web_search("capital of France")

    assert "<grok:render" not in result
    assert "Paris is the capital of France" in result
    assert "and a major European city." in result


@pytest.mark.asyncio
async def test_grok_web_search_uses_model_response_message(mock_send_with_canonical):
    with patch("grok_research_mcp.tools.research.send_message", mock_send_with_canonical):
        with patch("grok_research_mcp.tools.research._get_session") as mock_session_ctx:
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await grok_web_search("capital of France")

    assert CANONICAL_MESSAGE in result
    assert "wrong streamed" not in result


@pytest.mark.asyncio
async def test_grok_x_search_uses_x_mode(mock_send):
    calls = []

    async def _capturing_send(session, conv_id, text, mode, **kwargs):
        calls.append(mode)
        async for item in mock_send(session, conv_id, text, mode):
            yield item

    with patch("grok_research_mcp.tools.research.send_message", _capturing_send):
        with patch("grok_research_mcp.tools.research._get_session") as mock_session_ctx:
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
            await grok_x_search("SpaceX")

    assert calls == ["x"]


def _patched_session(mock_session_ctx):
    mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
    mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)


@pytest.mark.asyncio
async def test_run_query_returns_error_on_access_denied():
    async def _raising(*args, **kwargs):
        raise AccessDenied("rate limited")
        yield  # makes this an async generator

    with patch("grok_research_mcp.tools.research.send_message", _raising):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            _patched_session(mock_ctx)
            result = await grok_web_search("test")

    assert "Access denied" in result
    assert "rate limited" in result


@pytest.mark.asyncio
async def test_run_query_returns_error_on_http_status_error():
    mock_response = MagicMock()
    mock_response.status_code = 429

    async def _raising(*args, **kwargs):
        raise httpx.HTTPStatusError("Too Many Requests", request=MagicMock(), response=mock_response)
        yield

    with patch("grok_research_mcp.tools.research.send_message", _raising):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            _patched_session(mock_ctx)
            result = await grok_web_search("test")

    assert "429" in result


@pytest.mark.asyncio
async def test_run_query_returns_error_on_network_error():
    async def _raising(*args, **kwargs):
        raise httpx.NetworkError("connection refused")
        yield

    with patch("grok_research_mcp.tools.research.send_message", _raising):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            _patched_session(mock_ctx)
            result = await grok_web_search("test")

    assert "Network error" in result
    assert "connection refused" in result


# --- #22: is_reasoning parameter ---

@pytest.mark.asyncio
async def test_grok_web_search_passes_is_reasoning_true(mock_send):
    captured = {}

    async def _capturing(session, conv_id, text, mode, **kwargs):
        captured.update(kwargs)
        async for item in mock_send(session, conv_id, text, mode):
            yield item

    with patch("grok_research_mcp.tools.research.send_message", _capturing):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            _patched_session(mock_ctx)
            await grok_web_search("test", is_reasoning=True)

    assert captured.get("is_reasoning") is True


@pytest.mark.asyncio
async def test_grok_web_search_is_reasoning_false_by_default(mock_send):
    captured = {}

    async def _capturing(session, conv_id, text, mode, **kwargs):
        captured.update(kwargs)
        async for item in mock_send(session, conv_id, text, mode):
            yield item

    with patch("grok_research_mcp.tools.research.send_message", _capturing):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            _patched_session(mock_ctx)
            await grok_web_search("test")

    assert captured.get("is_reasoning") is False


# --- #19: per-query jitter delay ---

@pytest.fixture(autouse=True)
def reset_last_query_time():
    research_module._last_query_time = 0.0
    yield
    research_module._last_query_time = 0.0


@pytest.mark.asyncio
async def test_run_query_no_jitter_on_first_call(mock_send):
    with patch("grok_research_mcp.tools.research.send_message", mock_send):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                _patched_session(mock_ctx)
                await grok_web_search("test")

    mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_run_query_applies_jitter_on_consecutive_calls(mock_send):
    import time
    research_module._last_query_time = time.monotonic()  # simulate recent prior call

    with patch("grok_research_mcp.tools.research.send_message", mock_send):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                _patched_session(mock_ctx)
                await grok_web_search("test")

    mock_sleep.assert_called_once()
    sleep_arg = mock_sleep.call_args[0][0]
    assert 0 < sleep_arg <= research_module._JITTER_MAX


# --- #20: HTTP 400 retry with exponential backoff ---

@pytest.mark.asyncio
async def test_run_query_retries_on_400_then_succeeds(mock_send):
    call_count = 0

    async def _fail_then_succeed(session, conv_id, text, mode, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            raise httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_resp)
        async for item in mock_send(session, conv_id, text, mode):
            yield item

    with patch("grok_research_mcp.tools.research.send_message", _fail_then_succeed):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                _patched_session(mock_ctx)
                result = await grok_web_search("test")

    assert call_count == 2
    assert "Paris is the capital of France." in result


@pytest.mark.asyncio
async def test_run_query_returns_down_message_after_exhausted_retries():
    async def _always_400(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        raise httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_resp)
        yield  # make it an async generator

    with patch("grok_research_mcp.tools.research.send_message", _always_400):
        with patch("grok_research_mcp.tools.research._get_session") as mock_ctx:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                _patched_session(mock_ctx)
                result = await grok_web_search("test")

    assert "down" in result.lower()
    assert mock_sleep.call_count == 3  # _RETRY_MAX retries
