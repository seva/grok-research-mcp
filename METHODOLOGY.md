# grok-research-mcp — Development Methodology

---

## Artifacts

| Artifact | Purpose |
|---|---|
| `CLAUDE.md` | Session bootstrap — current phase, linked GitHub issue |
| `IMPLEMENTATION.md` | Task state — checkboxes updated in place |
| GitHub issue per phase | Failure record — comments capture attempts and decisions |
| `docs/endpoints.md` | Phase 0 output — hard gate for Phase 2 |

---

## Session Protocol

**Start:** Read `CLAUDE.md` → open linked GitHub issue → scan `IMPLEMENTATION.md` checkboxes.

**End:** Update checkboxes + post one comment to the open issue (what was tried, what was found, what's next).

---

## Phase Gate

Phase 2 (`client/endpoints.py`) does not start until `docs/endpoints.md` is committed.
No code is written against undiscovered endpoints.

---

## What Goes Where

- **Checkboxes** — task complete or not. Binary.
- **Issue comments** — everything else: failed attempts, decisions, partial findings, blockers.
- **`docs/`** — structured discovery outputs. Committed, permanent, readable by any session.
- **`CLAUDE.md`** — current phase pointer only. Updated when phase changes.

---

## What's Excluded and Why

- **MCP memory** — not agent-agnostic, has availability precedent, not auditable.
- **Session log** — redundant with issue comments; grows noisy.
- **Branch-per-phase** — doesn't capture intra-phase progress or failures.
