# grok-research-mcp — Implementation Plan

---

## Phase 0 — Discovery (prerequisite to Phase 2)

Must complete before writing `client/endpoints.py`.

- [ ] Read `mem0ai/grok3-api` source: extract current endpoint URLs, request shapes, response format
- [ ] Read `EveripediaNetwork/grokit` source: cross-reference endpoints, cookie set, bearer token value
- [ ] Capture a live browser session at `x.com/i/grok`: inspect Network tab for `send-message` request payload
  — identify the parameter that activates web search mode vs. X search mode
  — **requires user present at browser**: pause and wait for confirmation before proceeding
- [ ] Record: base URL, conversation init endpoint, message endpoint, streaming protocol, all required headers

Outputs: annotated endpoint reference committed to `docs/endpoints.md`.

---

## Phase 1 — Auth Module

**Goal:** `python -m grok_research_mcp auth` runs browser, captures cookies, stores to DPAPI, confirms.

### Tasks

- [ ] `pyproject.toml` — project scaffold: `mcp`, `playwright`, `httpx`, `pywin32`, `pytest`, `pytest-asyncio`
- [ ] `tests/auth/test_store.py`
  - `save()` writes encrypted blob to expected path
  - `load()` round-trips: save then load returns original dict
  - `load()` raises `AuthRequired` when file missing
  - `is_expired()` returns True when `sso` expiry is in the past
  - `is_expired()` returns False when `sso` expiry is in the future
- [ ] `auth/store.py`
  - `save(data: dict)`: JSON → bytes → `CryptProtectData(dwFlags=CRYPTPROTECT_LOCAL_MACHINE=False)` → write `~/.grok-mcp/auth.dpapi`
  - `load() -> dict`: read blob → `CryptUnprotectData` → JSON parse; raise `AuthRequired` if file missing
  - `is_expired() -> bool`: check `sso` cookie `expires` field vs. `time.time()`
- [ ] `tests/auth/test_browser.py`
  - Cookie detection logic: given a cookie list, correctly identifies when `sso` + `sso-rw` are both present
  - Bearer token extraction: correctly parses token from intercepted request header
- [ ] `auth/browser.py`
  - Playwright async: launch Chromium headed
  - Navigate to `x.com/i/grok`
  - Poll `context.cookies()` every 2s; done when `sso` + `sso-rw` both present
  - Capture: all target cookies + bearer token from `on_request` handler (intercept `api.x.com` calls)
  - Return cookie dict; close browser
- [ ] `__main__.py` auth subcommand: call browser → save → print confirmation

**Verification:** `pytest tests/auth/` passes; run auth, confirm `~/.grok-mcp/auth.dpapi` written.

---

## Phase 2 — Grok Client

**Goal:** `GrokClient` can send a message with web/X search mode and return streamed response.
Depends on Phase 0 discovery outputs.

### Tasks

- [ ] `tests/client/test_endpoints.py`
  - `new_conversation()` sends correct request shape; returns conv_id from mocked response
  - `send_message()` includes correct mode parameter for `"web"`, `"x"`, `"none"`
  - `parse_citations()` extracts title + url from known response fixture
- [ ] `client/endpoints.py`
  - `new_conversation(session) -> conv_id`
  - `send_message(session, conv_id, text, mode: Literal["web", "x", "none"]) -> AsyncIterator[str]`
  - `parse_citations(raw_response) -> list[dict]`
  - Populate from `docs/endpoints.md`
- [ ] `tests/client/test_session.py`
  - `build_session()` injects cookies and bearer token into every request
  - `with_auth_retry()` retries once on 401; does not retry on second 401
- [ ] `client/session.py`
  - `build_session(auth: dict) -> httpx.AsyncClient`: inject cookies + `Authorization: Bearer <token>`
  - `with_auth_retry(fn)`: decorator — on 401/403, call `store.load()`, check `is_expired()`,
    re-auth if needed, rebuild session, retry once
- [ ] Manual integration test: send a known query in web search mode, print raw response

**Verification:** `pytest tests/client/` passes; query returns text + at least one citation.

---

## Phase 3 — MCP Server

**Goal:** Any MCP client can call `grok_web_search` and `grok_x_search` tools.

### Tasks

- [ ] `tests/tools/test_research.py`
  - `grok_web_search()` returns string containing response text and `Sources:` section
  - `grok_x_search()` same
  - Citation formatting: given parsed citations, output matches expected markdown
- [ ] `tools/research.py`
  - `grok_web_search(query: str) -> str`: new conv → send (mode=web) → collect stream → format result with citations
  - `grok_x_search(query: str) -> str`: same, mode=x
  - Result format: `<response text>\n\nSources:\n- [title](url)\n...`
- [ ] `server.py`
  - MCP stdio server via `mcp` Python SDK
  - On startup: `store.load()` — if `AuthRequired`, exit with message "Run: python -m grok_research_mcp auth"
  - Register `grok_web_search` and `grok_x_search`
- [ ] `__main__.py` serve subcommand: start MCP server

**Verification:** `pytest tests/tools/` passes; connect an MCP client → call `grok_web_search("test")` → returns result.

---

## Phase 4 — Integration + Packaging

### Tasks

- [ ] `README.md`: install steps, auth setup, MCP client config examples (Claude Code, Cursor, Cline)
- [ ] Error handling review: auth expiry UX, API shape changes, network errors
- [ ] `uv` / `pip` install verified from clean environment

---

## Dependencies

```toml
[project]
name = "grok-research-mcp"
requires-python = ">=3.11"

dependencies = [
  "mcp>=1.0",
  "playwright>=1.40",
  "httpx>=0.27",
  "pywin32>=306",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
]
```

Install Playwright browsers after install:
```
playwright install chromium
```

---

## Open Questions

1. **Research mode parameter** — exact field name + value in `send_message` payload that activates web vs. X search. Resolved in Phase 0.
2. **Bearer token** — static value or rotated? If rotated per session, must capture fresh each auth run. If static, can hardcode from discovery. Resolved in Phase 0.
3. **Streaming protocol** — SSE, chunked JSON, or other? Determines `stream_response()` implementation. Resolved in Phase 0.
4. **Conversation reuse** — can one `conv_id` accept multiple queries, or must each query start a new conversation? Affects latency. Resolved in Phase 2 testing.
