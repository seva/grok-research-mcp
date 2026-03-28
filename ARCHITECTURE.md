# grok-research-mcp — Architecture

MCP server that exposes Grok's web research tools (web search, X search) to any MCP client.
Authenticates as the user's X account via automated browser login; stores credentials
securely with DPAPI.

---

## Principles

**Separation of concerns** — auth, credential storage, HTTP transport, Grok API, and MCP tooling are separate modules. No cross-cutting logic.

**Isolation of fragility** — the unofficial Grok web API is contained entirely in `client/endpoints.py`. When endpoints change, only that file updates. Nothing else knows about Grok's internal API shape.

**Security** — credentials never in plaintext on disk. DPAPI ensures only the local user can decrypt. Auth tokens never logged or surfaced in tool output.

---

## Coding Hygiene

Guard clauses. Graceful degradation. No silent failures. Explicit error types.

Code as documentation — names and structure must be self-explanatory. Comments explain why, not what. Maximize semantic and cognitive ROI.

---

## System Diagram

```
MCP client (e.g. Claude Code, Cursor, Cline)
        │  stdio
        ▼
┌─────────────────────────────────┐
│        grok-research-mcp        │
│                                 │
│  server.py  ←→  tools/          │
│      │          research.py     │
│      │                          │
│  client/                        │
│      session.py  ──────────────────────→  grok.com (web API)
│      endpoints.py               │
│                                 │
│  auth/                          │
│      browser.py  ──────────────────────→  Chromium (headed)
│      store.py    ←→  ~/.grok-mcp/auth.dpapi
└─────────────────────────────────┘
```

---

## Components

### `server.py`
MCP stdio server. Registers tools, initializes auth on startup, routes tool calls.
Uses the `mcp` Python SDK.

### `auth/browser.py`
Spawns a headed Chromium instance via Playwright. Navigates to `grok.com`.
Waits for user to complete login (polls for `sso` + `sso-rw` cookies appearing).
Captures the full cookie set and the `statsig_id` from localStorage.
Returns cookie dict. Browser closes immediately after capture.

### `auth/store.py`
Encrypts the cookie dict (JSON) with Windows DPAPI (`win32crypt.CryptProtectData`,
user-scoped). Writes opaque blob to `~/.grok-mcp/auth.dpapi`.
`load()` decrypts and parses. `is_expired()` checks `sso` cookie expiry timestamp.

### `client/session.py`
`httpx` async session with cookies + enriched Chrome fingerprint headers injected on every request.
On 401: raises `AuthExpired`. On 403: raises `AccessDenied`. Caller is responsible for handling both.

### `client/endpoints.py`
Grok web API calls. `send_message(session, conv_id, text, mode, is_reasoning)` is the single entry point:
- `conv_id=None` → `POST /conversations/new`; conversation ID returned in the stream and threaded through subsequent calls.
- `conv_id` set → `POST /conversations/{id}/responses`
- Streaming NDJSON parsed line-by-line; yields `(token, conv_id, model_response)` 3-tuples.
- `parse_citations(model_response)` extracts `webSearchResults` into `[{title, url}]`.

### `tools/research.py`
Implements MCP tools:
- `grok_web_search(query: str, is_reasoning: bool = False) -> str` — web research, returns text + citations
- `grok_x_search(query: str, is_reasoning: bool = False) -> str` — X search, returns text + citations

Applies per-query jitter delay (2–8s) between consecutive calls. Retries on HTTP 400 with exponential backoff (up to 3×, 30s/60s/120s).

### `__main__.py`
CLI entry point with three subcommands:
- `auth` — spawns browser, captures and stores credentials
- `serve` — starts MCP stdio server
- `query [--mode web|x] [--reasoning] QUERY...` — exec-callable search for non-MCP callers

---

## Auth Flow

```
First run (no stored auth):
  startup → store.load() → not found
         → browser.py: spawn Chromium → navigate grok.com
         → user logs in (headed, interactive)
         → poll: sso + sso-rw cookies present
         → capture cookies + statsig_id
         → store.save() → DPAPI encrypt → ~/.grok-mcp/auth.dpapi
         → session ready

Subsequent runs:
  startup → store.load() → DPAPI decrypt → cookie dict
          → store.is_expired()? → no → session ready
                                → yes → re-trigger browser flow

Mid-session expiry:
  send_message() → 401 → session.py raises AuthExpired
                       → tool returns error: "Auth expired. Run: python -m grok_research_mcp auth"
```

---

## Request Flow

```
MCP client: tool call grok_web_search("query")
  → research.py: [jitter delay if not first call]
  → send_message(session, conv_id=None, query, mode="web") → AsyncIterator
      stream yields: tokens → conv_id → model_response (citations)
  → strip grok:render tags from canonical message
  → format text + citations
  → return to MCP client
  [on HTTP 400: retry up to 3× with backoff before returning error]
```

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Language | Python | DPAPI via `pywin32` is mature; Grok ecosystem is Python; MCP SDK supports Python |
| Browser automation | Playwright | Async-native; `context.cookies()` API; better than Selenium for this use case |
| Browser mode | Headed | X bot detection; user must complete login/MFA visually |
| Auth storage | DPAPI (user-scoped) | OS-level encryption tied to Windows user; no key management |
| HTTP client | `httpx` | Async; cookie jar control; stream support |
| Transport | stdio | MCP standard; no port/firewall config |
| Grok client base | `mem0ai/grok3-api` + `grokit` | Verified endpoint knowledge; borrow, don't reinvent |
| Anti-bot | Per-query jitter + enriched headers | Rapid sequential calls trigger session invalidation |
| HTTP 400 | Retry with exponential backoff | 400 during Grok outage is indistinguishable from bad request without retry evidence |
| CLI exec path | `query` subcommand | Allows non-MCP callers to invoke search via shell exec |

---

## Required Cookie Set

Captured from browser session at `grok.com`:

| Name | Source | Purpose |
|---|---|---|
| `sso` | Browser session | Primary auth token — expiry checked on startup |
| `sso-rw` | Browser session | Auth write scope — expiry checked on startup |
| `statsig_id` | localStorage | Feature-flag identity header (`x-statsig-id`) |

All other cookies in the session are captured and forwarded but `sso` + `sso-rw` are the auth-critical ones.

---

## Constraints

- **Windows only** — DPAPI is Windows-specific. Linux/Mac would require a different secure store (keyring).
- **Unofficial API** — Grok web endpoints are undocumented and may change.
- **X ToS** — Programmatic access to the web interface is not officially sanctioned.
- **Session longevity** — `sso` cookie lifetime is typically 30 days. Re-auth required on expiry.
