# grok-research-mcp — Implementation Plan

---

## Phase 0 — Discovery (prerequisite to Phase 2)

Must complete before writing `client/endpoints.py`.

- [x] Read `mem0ai/grok3-api` source: extract current endpoint URLs, request shapes, response format
- [x] Read `EveripediaNetwork/grokit` source: cross-reference endpoints, cookie set, bearer token value
- [x] Record: base URL, conversation init endpoint, message endpoint, streaming protocol, all required headers

Outputs: annotated endpoint reference committed to `docs/endpoints.md`.

---

## Phase 1 — Auth Module

**Goal:** `python -m grok_research_mcp auth` runs browser, captures cookies, stores to DPAPI, confirms.

### Tasks

- [x] `pyproject.toml` — project scaffold: `mcp`, `playwright`, `httpx`, `pywin32`, `pytest`, `pytest-asyncio`
- [x] `tests/auth/test_store.py`
  - `save()` writes encrypted blob to expected path
  - `load()` round-trips: save then load returns original dict
  - `load()` raises `AuthRequired` when file missing
  - `is_expired()` returns True when `sso` expiry is in the past
  - `is_expired()` returns False when `sso` expiry is in the future
- [x] `auth/store.py`
  - `save(data: dict)`: JSON → bytes → `CryptProtectData(dwFlags=CRYPTPROTECT_LOCAL_MACHINE=False)` → write `~/.grok-mcp/auth.dpapi`
  - `load() -> dict`: read blob → `CryptUnprotectData` → JSON parse; raise `AuthRequired` if file missing
  - `is_expired() -> bool`: check `sso` cookie `expires` field vs. `time.time()`
- [x] `tests/auth/test_browser.py`
  - Cookie detection logic: given a cookie list, correctly identifies when `sso` + `sso-rw` are both present
  - statsig ID extraction: correctly parses ID from localStorage snapshot
- [x] `auth/browser.py`
  - Playwright async: launch Chromium headed
  - Navigate to `grok.com` (Phase 0: API is grok.com, not x.com/i/grok)
  - Poll `context.cookies()` every 2s; done when `sso` + `sso-rw` both present
  - Capture: all cookies + statsig_id from localStorage (Phase 0: no bearer token needed)
  - Return data dict; close browser
- [x] `__main__.py` auth subcommand: call browser → save → print confirmation

**Verification:** `pytest tests/auth/` passes (11/11); `~/.grok-mcp/auth.dpapi` written with 84 cookies, sso+sso-rw present.
Note: `statsig_id` null at auth time — captured fresh at request time in Phase 2.

---

## Phase 2 — Grok Client

**Goal:** Grok client module can send a message with web/X search mode and return streamed response.
Depends on Phase 0 discovery outputs.

### Tasks

- [x] `tests/client/test_endpoints.py`
  - `send_message()` hits correct endpoint for new/existing conversation
  - `send_message()` includes correct mode parameter for `"web"`, `"x"`, `"none"`
  - `send_message()` yields `(token, conv_id, model_response)` 3-tuple
  - `parse_citations()` extracts title + url from webSearchResults fixture
- [x] `client/endpoints.py`
  - `send_message(session, conv_id, text, mode)` — conv_id=None → /conversations/new; else /conversations/{id}/responses
  - `parse_citations(model_response: dict) -> list[dict]` — reads `webSearchResults`
  - Note: no separate `new_conversation()` — conv_id returned in stream (Phase 0 gap resolved)
- [x] `tests/client/test_session.py`
  - `build_session()` injects cookies and statsig header into every request
  - `build_session()` raises `AuthExpired` on 401/403 response
- [x] `client/session.py`
  - `build_session(auth: dict)` async context manager: inject cookies + required headers + x-statsig-id
  - On 401/403: raise `AuthExpired`
- [x] Manual integration test: "Latest SpaceX news" → 45 citations, conv_id captured

**Verification:** `pytest tests/client/` 13/13; live query returns text + 45 citations.

---

## Phase 3 — MCP Server

**Goal:** Any MCP client can call `grok_web_search` and `grok_x_search` tools.

### Tasks

- [x] `tests/tools/test_research.py`
  - `grok_web_search()` returns string containing response text and `Sources:` section
  - `grok_x_search()` uses mode=x
  - Citation formatting: given parsed citations, output matches expected markdown
- [x] `tools/research.py`
  - `grok_web_search(query: str) -> str`: new conv → send (mode=web) → collect stream → format result with citations
  - `grok_x_search(query: str) -> str`: same, mode=x
  - Result format: `<response text>\n\nSources:\n- [title](url)\n...`
- [x] `server.py`
  - MCP stdio server via `FastMCP`
  - On startup: `store.load()` — if `AuthRequired`, exit with message
  - Registers `grok_web_search_tool` and `grok_x_search_tool`
- [x] `__main__.py` serve subcommand: start MCP server

**Verification:** `pytest tests/` 28/28. MCP client connection pending.

---

## Phase 4 — Integration + Packaging

### Tasks

- [x] `README.md`: install steps, auth setup, MCP client config examples (Claude Code, Cursor, Cline)
- [x] Error handling review: auth expiry checked on startup; AuthExpired + NetworkError caught in tools layer
- [x] `pip install -e .` verified from clean venv — all imports ok

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

## Phase 5 — Post-Release Fixes and Enhancements

### Audit fixes (commit `80ae163`)
- [x] `auth/store.py` — removed mkdir side effect from `_auth_path()`; `load()` wraps decrypt in try/except → `AuthRequired`; `is_expired()` checks both `sso` and `sso-rw`
- [x] `client/session.py` — distinguished 401 (`AuthExpired`) from 403 (`AccessDenied`); added `httpx.Timeout(120.0, connect=10.0)`
- [x] `client/endpoints.py` — fixed `_payload` signature; `parentResponseId` included when `response_id` set
- [x] `tools/research.py` — `modelResponse.message` as canonical text; `AccessDenied` handled; `grok:render` tags stripped (Closes #18)

### #19 — Anti-bot: human request patterns
- [x] `tests/client/test_session.py` — tests for `Accept-Language`, `sec-ch-ua*`, `DNT` headers
- [x] `tests/tools/test_research.py` — jitter delay tests (first call undelayed; consecutive calls sleep)
- [x] `client/session.py` — enriched Chrome fingerprint headers; `_CHROME_VERSION` constant
- [x] `tools/research.py` — per-query jitter (2–8s, applied between consecutive calls only)

### #20 — HTTP 400 retry with exponential backoff
- [x] `tests/tools/test_research.py` — retry-then-succeed and exhausted-retry tests
- [x] `tools/research.py` — retry loop: 3× max, 30s/60s/120s backoff, "Grok appears to be down" on exhaustion

### #21 — `query` CLI subcommand
- [x] `tests/test_main.py` — routing, mode, error exit, subprocess auth-missing tests
- [x] `__main__.py` — `query [--mode web|x] [--reasoning] QUERY...` subcommand; exit 0/1 contract

### #22 — `isReasoning` as tool parameter
- [x] `tests/client/test_endpoints.py` — payload tests for `is_reasoning` true/false
- [x] `tests/tools/test_research.py` — threading tests through `_run_query`
- [x] `client/endpoints.py` — `_payload` and `send_message` accept `is_reasoning: bool = False`
- [x] `tools/research.py` — `grok_web_search` and `grok_x_search` expose `is_reasoning`
- [x] `server.py` — MCP tools expose `is_reasoning` with description

**Verification:** `pytest tests/` 58/58. Integration confirmed by external Claude Code session.

---

## Open Questions

1. **Research mode parameter** — exact field name + value in `send_message` payload that activates web vs. X search. Resolved in Phase 0.
2. **Bearer token** — static value or rotated? If rotated per session, must capture fresh each auth run. If static, can hardcode from discovery. Resolved in Phase 0.
3. **Streaming protocol** — SSE, chunked JSON, or other? Determines `stream_response()` implementation. Resolved in Phase 0.
4. **Conversation reuse** — can one `conv_id` accept multiple queries, or must each query start a new conversation? Affects latency. Resolved in Phase 2 testing.
