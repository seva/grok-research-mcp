import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from grok_research_mcp.client.endpoints import send_message, parse_citations


# --- fixtures ---

def _ndjson(*lines):
    """Build a mock streaming response from NDJSON lines."""
    encoded = [json.dumps(l).encode() for l in lines]

    async def _aiter():
        for line in encoded:
            yield line

    mock = MagicMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    mock.aiter_lines = _aiter
    return mock


STREAM_LINES = [
    {"result": {"response": {"token": "Hello "}}},
    {"result": {"response": {"token": "world"}}},
    {"result": {"conversation": {"conversationId": "conv-abc"}}},
    {"result": {"response": {"modelResponse": {"message": "Hello world", "responseId": "resp-xyz"}}}},
]


# --- send_message ---

@pytest.mark.asyncio
async def test_send_message_new_conversation_hits_new_endpoint(mock_session):
    async for _t, _c, _m in send_message(mock_session, None, "hi", "web"):
        pass
    mock_session.stream.assert_called_once()
    url = mock_session.stream.call_args[0][1]
    assert url == "https://grok.com/rest/app-chat/conversations/new"


@pytest.mark.asyncio
async def test_send_message_existing_conversation_hits_responses_endpoint(mock_session):
    async for _t, _c, _m in send_message(mock_session, "conv-abc", "hi", "web"):
        pass
    url = mock_session.stream.call_args[0][1]
    assert "conv-abc/responses" in url


@pytest.mark.asyncio
async def test_send_message_web_mode_sets_tool_overrides(mock_session):
    async for _t, _c, _m in send_message(mock_session, None, "hi", "web"):
        pass
    payload = mock_session.stream.call_args[1]["json"]
    assert payload["toolOverrides"]["webSearch"] is True
    assert payload["toolOverrides"]["xSearch"] is False


@pytest.mark.asyncio
async def test_send_message_x_mode_sets_tool_overrides(mock_session):
    async for _t, _c, _m in send_message(mock_session, None, "hi", "x"):
        pass
    payload = mock_session.stream.call_args[1]["json"]
    assert payload["toolOverrides"]["webSearch"] is False
    assert payload["toolOverrides"]["xSearch"] is True


@pytest.mark.asyncio
async def test_send_message_none_mode_disables_search(mock_session):
    async for _t, _c, _m in send_message(mock_session, None, "hi", "none"):
        pass
    payload = mock_session.stream.call_args[1]["json"]
    assert payload["disableSearch"] is True


@pytest.mark.asyncio
async def test_send_message_yields_tokens(mock_session):
    tokens = [t async for t, _, _m in send_message(mock_session, None, "hi", "web") if t]
    assert tokens == ["Hello ", "world"]


@pytest.mark.asyncio
async def test_send_message_yields_conv_id(mock_session):
    conv_ids = [cid async for _, cid, _m in send_message(mock_session, None, "hi", "web") if cid]
    assert conv_ids == ["conv-abc"]


@pytest.mark.asyncio
async def test_send_message_skips_malformed_json_lines():
    """Invalid NDJSON lines are silently dropped; valid tokens still yielded."""
    malformed_lines = [
        {"result": {"response": {"token": "Hello "}}},
        "not valid json{{{{",
        {"result": {"response": {"token": "world"}}},
    ]

    async def _aiter_lines():
        for line in malformed_lines:
            if isinstance(line, dict):
                yield json.dumps(line)
            else:
                yield line

    response = MagicMock()
    response.aiter_lines = _aiter_lines
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    response.raise_for_status = MagicMock()

    session = MagicMock()
    session.stream = MagicMock(return_value=response)

    tokens = [t async for t, _, _m in send_message(session, None, "hi", "web") if t]
    assert tokens == ["Hello ", "world"]


@pytest.mark.asyncio
async def test_send_message_includes_parent_response_id(mock_session):
    async for _t, _c, _m in send_message(mock_session, "conv-abc", "hi", "web", response_id="resp-xyz"):
        pass
    payload = mock_session.stream.call_args[1]["json"]
    assert payload["parentResponseId"] == "resp-xyz"


@pytest.mark.asyncio
async def test_send_message_no_parent_response_id_when_none(mock_session):
    async for _t, _c, _m in send_message(mock_session, None, "hi", "web"):
        pass
    payload = mock_session.stream.call_args[1]["json"]
    assert "parentResponseId" not in payload


# --- parse_citations ---

def test_parse_citations_extracts_web_search_results():
    model_response = {
        "webSearchResults": [
            {"title": "Example", "url": "https://example.com", "preview": "..."},
            {"title": "Other", "url": "https://other.org", "preview": "..."},
        ]
    }
    result = parse_citations(model_response)
    assert {"title": "Example", "url": "https://example.com"} in result
    assert {"title": "Other", "url": "https://other.org"} in result


def test_parse_citations_empty():
    assert parse_citations({}) == []


# --- conftest fixture ---

@pytest.fixture
def mock_session():
    async def _aiter_lines():
        for line in STREAM_LINES:
            yield json.dumps(line).encode()

    response = MagicMock()
    response.aiter_lines = _aiter_lines
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    response.raise_for_status = MagicMock()

    session = MagicMock()
    session.post = MagicMock(return_value=response)
    session.stream = MagicMock(return_value=response)
    return session
