# grok-research-mcp

MCP server exposing Grok web/X research tools to any MCP client via cookie auth + platform keychain (DPAPI on Windows, Keychain on macOS).

## Session Start

1. Read `METHODOLOGY.md`
2. Read `ARCHITECTURE.md` — verify component descriptions match current code before acting
3. Scan `IMPLEMENTATION.md` checkboxes — first unchecked task is current state
4. Check open GitHub issues for failures and decisions
5. Search MCP memory for relevant prior knowledge (`mcp__memory__retrieve_memory`)
6. Locate the project in the operating cycle (`CYCLE.md`) — which step is current?
7. Identify your role (`ROLES.md`; default Steward) and the declared role instances below — no role grades its own work

## Conventions

- Language: Python 3.12. Tests: `python -m pytest tests -q`. Layout mirrors source: `tests/auth/`, `tests/client/`, `tests/tools/`.
- Shell is PowerShell: no heredoc `<<'EOF'` (pwsh rejects it). Multi-line Python via `python -c "..."` or script files under `tmp/`.
- MCP memory service is operational session memory, not constitutional content (carried from pre-pin constitution).
- Scope position per `docs/scope.md` (DRAFT — Owner review pending): L1 current. Terminal-bound constraints compiled there; Decide filters before ranking.
- Role instances (proposed, Owner to confirm): Owner = Seva; Steward = OpenCode sessions; Critic = distinct-model session (first pass on the pin-bump commit pending); Auditor = MetaThrone (proposed).
- Current phase pointer: Phase 7 complete (#24 landed; #25 fixed; #26 closed by Owner ruling). #27 open as review-tracking (Critic/Auditor passes pending).

## Accepted deviations

- **Test-authenticity reading:** `tests/tools/test_research.py` mocks `send_message` — that function is the third-party API containment boundary (`client/endpoints.py` holds all unofficial Grok API knowledge), so this counts as "mocks for external third-party APIs", not mock-testing internal boundaries.
- **Invariant applicability:** no ORM, database, queues, or HTTP ingress in this codebase — repository-abstraction, schema-evolution, and re-entrant-mutation rows are N/A by vacuity. `~/.grok-mcp/query.lock` serializes queries but is a mutual-exclusion guard, not an idempotency mechanism (declared, not claimed).
