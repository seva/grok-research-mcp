from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx


class AuthExpired(Exception):
    pass


class AccessDenied(Exception):
    pass


async def _auth_event_hook(response: httpx.Response) -> None:
    if response.status_code == 401:
        raise AuthExpired("Session expired (HTTP 401). Run: python -m grok_research_mcp auth")
    if response.status_code == 403:
        raise AccessDenied("Access denied (HTTP 403) — may be rate-limited or geo-blocked")


@asynccontextmanager
async def build_session(auth: dict) -> AsyncIterator[httpx.AsyncClient]:
    cookies = {c["name"]: c["value"] for c in auth.get("cookies", [])}
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://grok.com",
        "Referer": "https://grok.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
    }
    if auth.get("statsig_id"):
        headers["x-statsig-id"] = auth["statsig_id"]

    async with httpx.AsyncClient(
        cookies=cookies,
        headers=headers,
        timeout=httpx.Timeout(120.0, connect=10.0),
        event_hooks={"response": [_auth_event_hook]},
    ) as client:
        yield client
