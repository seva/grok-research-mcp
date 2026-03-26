# grok-research-mcp — Architecture

MCP server that exposes Grok's web research tools (web search, X search) to any MCP client.
Authenticates as the user's X account via automated browser login; stores credentials
securely with DPAPI.

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
│      session.py  ──────────────────────→  grok.x.ai (web API)
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
Spawns a headed Chromium instance via Playwright. Navigates to `x.com/i/grok`.
Waits for user to complete login (polls for `sso` + `sso-rw` cookies appearing).
Captures the full target cookie set and the app-level bearer token from request headers.
Returns cookie dict. Browser closes immediately after capture.

### `auth/store.py`
Encrypts the cookie dict (JSON) with Windows DPAPI (`win32crypt.CryptProtectData`,
user-scoped). Writes opaque blob to `~/.grok-mcp/auth.dpapi`.
`load()` decrypts and parses. `is_expired()` checks `sso` cookie expiry timestamp.

### `client/session.py`
`httpx` async session with cookies + bearer token injected on every request.
On 401/403: raises `AuthExpired`. Caller is responsible for handling it.

### `client/endpoints.py`
Grok web API calls: `new_conversation()`, `send_message(conv_id, text, options) -> AsyncIterator[str]`.
Streaming is the return value of `send_message()` — no separate `stream_response()`.
Research mode (web search / X search) is activated via options in the `send_message` payload
— exact parameter names resolved during Phase 0 discovery.

### `tools/research.py`
Implements MCP tools:
- `grok_web_search(query: str) -> str` — web research, returns text + citations
- `grok_x_search(query: str) -> str` — X search, returns text + citations

---

## Auth Flow

```
First run (no stored auth):
  startup → store.load() → not found
         → browser.py: spawn Chromium → navigate x.com/i/grok
         → user logs in (headed, interactive)
         → poll: sso + sso-rw cookies present
         → capture cookies + bearer token
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
  → research.py: new_conversation() → conv_id
  → send_message(conv_id, query, mode=web_search) → AsyncIterator[str]
  → collect text + citations from stream
  → return formatted result to MCP client
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

---

## Required Cookie Set

Captured from browser session at `x.com/i/grok`:

| Name | Source | Purpose |
|---|---|---|
| `sso` | Browser session | Primary auth token |
| `sso-rw` | Browser session | Auth write scope |
| `ct0` | Browser session | CSRF token |
| `auth_token` | Browser session | X user auth |
| Bearer token | Request header | X app-level token (static per app version) |

---

## Constraints

- **Windows only** — DPAPI is Windows-specific. Linux/Mac would require a different secure store (keyring).
- **Unofficial API** — Grok web endpoints are undocumented and may change.
- **X ToS** — Programmatic access to the web interface is not officially sanctioned.
- **Session longevity** — `sso` cookie lifetime is typically 30 days. Re-auth required on expiry.
