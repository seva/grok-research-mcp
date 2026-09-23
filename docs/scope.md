# Scope — Maximal Imaginable (DRAFT — Owner review pending)

Established 2026-09-23. Strategy artifact: the ladder this project climbs. Orient (CYCLE.md, step 1) measures the status quo against this document.

**Maximal mission:** any MCP client researches the live web and X through the operator's Grok session — reliably, serially, and within the account's standing.

---

## Scope ladder

| Level | Scope | Current system's contribution |
|---|---|---|
| L1 | Single operator, stdio MCP, 2 tools (web + X search), Windows + macOS | as-is |
| L2 | Linux support verified; install documented for third-party operators | keyring path exists, untested on Linux; README targets the operator only |
| L3 | Additional transports (HTTP/SSE) for non-stdio clients | stdio only; `query` CLI covers exec callers |
| Ln | Personal research interface: any model-client over any transport, within one account's standing | L1 |

---

## Functional depth

- Query serialization depth: per-process (done) → cross-process (done, #24) → backoff-aware (#25 open)
- Failure semantics: 400-retried, 429-undecided (#26 open), auth-expiry actionable
- Constitution: pinned scaffold, audited per Post-Phase Audit

---

## Survivability

- grok.com API change (unofficial endpoints): contained in `client/endpoints.py`; breaks all queries until updated
- `sso` cookie expiry (~30d): re-auth via headed browser flow
- Rate-limit escalation (429 → session invalidation): jitter + serialization mitigate; reactive policy undecided (#26)
- Credential leak (cookie blob / Keychain / DPAPI): account takeover — never logged, never in tool output

---

## Terminal bound

| Compiled constraint | Irrecoverable margin it protects |
|---|---|
| Queries serialize globally (`query.lock`); 2-8s jitter between calls | X account standing (unsanctioned programmatic access; suspension is irrecoverable) |
| Credentials never in plaintext, never logged, never in tool output | Credential confidentiality (leak = takeover) |
| Auth flow stays headed/interactive; no headless credential bypass | Account standing (bot-detection evasion escalates the ToS exposure) |
| `client/endpoints.py` owns all unofficial API knowledge | Operator time (uncontained breakage = full rewrite surface) |

| Commitment class | Refinement level (PRAROC-n, HORIZONS.md) | Terms below the cut, registered non-drifting |
|---|---|---|
| Tool behavior (retry, backoff, error text) | PRAROC-2 (dev steps) | `sso` lifetime ~30d; jitter bounds 2-8s |
| Transports, dependency changes | PRAROC-2 | stdio is the MCP standard for local use |
| Account-affecting changes (auth flow, request patterns) | PRAROC-3 (publish-facing: affects external standing) | X ToS exposure never traded for speed |

Exit margin: the headed browser re-auth path must keep working — if grok.com changes break automated flow, manual cookie refresh is the fallback before any headless workaround is considered.

---

## Terminal form

The operator asks any connected model-client a research question; the answer arrives with sources, every time, without thinking about sessions, locks, cookies, or rate limits. Account standing intact indefinitely.

---

## Constraint analysis

- L1→L2 composes (keyring abstraction already dispatches by platform; needs a Linux verification run).
- L2→L3 requires transport work in `server.py` (FastMCP HTTP); tool layer unchanged.
- Nearest anchors: OpenCode + Claude Code (connected today); `query` CLI for exec callers.
