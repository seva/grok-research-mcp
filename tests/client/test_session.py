import pytest
import httpx
import respx

from grok_research_mcp.client.session import build_session, AuthExpired, AccessDenied

AUTH = {
    "cookies": [
        {"name": "sso", "value": "sso-val", "expires": 9999999999.0, "domain": ".grok.com", "path": "/"},
        {"name": "sso-rw", "value": "sso-rw-val", "expires": 9999999999.0, "domain": ".grok.com", "path": "/"},
    ],
    "statsig_id": "test-statsig-id",
}


@respx.mock
@pytest.mark.asyncio
async def test_build_session_injects_cookies():
    respx.get("https://grok.com/test").mock(return_value=httpx.Response(200))
    async with build_session(AUTH) as client:
        resp = await client.get("https://grok.com/test")
    assert resp.status_code == 200
    request = respx.calls.last.request
    assert "sso=sso-val" in request.headers["cookie"]
    assert "sso-rw=sso-rw-val" in request.headers["cookie"]


@respx.mock
@pytest.mark.asyncio
async def test_build_session_injects_statsig_header():
    respx.get("https://grok.com/test").mock(return_value=httpx.Response(200))
    async with build_session(AUTH) as client:
        resp = await client.get("https://grok.com/test")
    request = respx.calls.last.request
    assert request.headers.get("x-statsig-id") == "test-statsig-id"


@respx.mock
@pytest.mark.asyncio
async def test_build_session_raises_auth_expired_on_401():
    respx.get("https://grok.com/test").mock(return_value=httpx.Response(401))
    with pytest.raises(AuthExpired):
        async with build_session(AUTH) as client:
            await client.get("https://grok.com/test")


@respx.mock
@pytest.mark.asyncio
async def test_build_session_raises_access_denied_on_403():
    respx.get("https://grok.com/test").mock(return_value=httpx.Response(403))
    with pytest.raises(AccessDenied):
        async with build_session(AUTH) as client:
            await client.get("https://grok.com/test")


# --- #19: enriched Chrome fingerprint headers ---

@respx.mock
@pytest.mark.asyncio
async def test_build_session_includes_accept_language():
    respx.get("https://grok.com/test").mock(return_value=httpx.Response(200))
    async with build_session(AUTH) as client:
        await client.get("https://grok.com/test")
    request = respx.calls.last.request
    assert "accept-language" in request.headers


@respx.mock
@pytest.mark.asyncio
async def test_build_session_includes_sec_ch_ua_headers():
    respx.get("https://grok.com/test").mock(return_value=httpx.Response(200))
    async with build_session(AUTH) as client:
        await client.get("https://grok.com/test")
    request = respx.calls.last.request
    assert "sec-ch-ua" in request.headers
    assert "sec-ch-ua-mobile" in request.headers
    assert "sec-ch-ua-platform" in request.headers


@respx.mock
@pytest.mark.asyncio
async def test_build_session_includes_dnt_header():
    respx.get("https://grok.com/test").mock(return_value=httpx.Response(200))
    async with build_session(AUTH) as client:
        await client.get("https://grok.com/test")
    request = respx.calls.last.request
    assert "dnt" in request.headers
