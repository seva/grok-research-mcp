import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from grok_research_mcp.auth.browser import _has_required_cookies, capture


def test_cookie_detection_present():
    cookies = [
        {"name": "sso", "value": "a"},
        {"name": "sso-rw", "value": "b"},
        {"name": "other", "value": "c"},
    ]
    assert _has_required_cookies(cookies) is True


def test_cookie_detection_missing_sso_rw():
    cookies = [
        {"name": "sso", "value": "a"},
    ]
    assert _has_required_cookies(cookies) is False


def test_cookie_detection_missing_sso():
    cookies = [
        {"name": "sso-rw", "value": "b"},
    ]
    assert _has_required_cookies(cookies) is False


def test_cookie_detection_empty():
    assert _has_required_cookies([]) is False


@pytest.mark.asyncio
async def test_capture_raises_timeout_and_closes_browser():
    mock_page = AsyncMock()
    mock_page.on = MagicMock()

    mock_context = AsyncMock()
    mock_context.cookies = AsyncMock(return_value=[])  # never satisfies _has_required_cookies
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_p = MagicMock()
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright_cm = AsyncMock()
    mock_playwright_cm.__aenter__ = AsyncMock(return_value=mock_p)
    mock_playwright_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("grok_research_mcp.auth.browser.async_playwright", return_value=mock_playwright_cm):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TimeoutError):
                await capture(timeout=2)  # POLL_INTERVAL=2, so times out after one loop

    mock_browser.close.assert_called_once()
