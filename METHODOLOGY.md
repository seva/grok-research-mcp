# Methodology

---

## Artifacts

| Artifact | Purpose |
|---|---|
| `AGENTS.md` | Session bootstrap |
| `CYCLE.md` | Operating loop — step selection, Definition of Success, autonomy |
| `HORIZONS.md` | Horizon doctrine — terminal bound, filter-before-rank, profile-not-total, marginal allocation, conditional commitments, error signatures |
| `ROLES.md` | Role separation — Steward, Critic, Auditor, Owner; no role grades itself |
| `IMPLEMENTATION.md` | Task state — checkboxes updated in place |
| `docs/scope.md` | Standing strategy artifact — maximal scope ladder, terminal form, compiled terminal-bound constraints. Orient measures against it every cycle; not a discovery output |
| GitHub issue per phase | Failure record — comments capture attempts and decisions |
| `docs/` outputs | Phase 0 discovery artifacts — hard gates for dependent phases |

---

## Session Protocol

**Start:** Read `AGENTS.md` → open linked GitHub issue → scan `IMPLEMENTATION.md` checkboxes.

**End:** Update checkboxes + post one comment to the open issue (what was tried, what was found, what's next).

---

## Commit Discipline

Commit at task completion, not session end. One logical unit of work per commit.

**Message format:**
```
<type>(<scope>): <summary>

Closes #N   ← for fix/feat commits that resolve a tracked issue
Refs #N     ← for commits that advance but don't close an issue
```

Rules:
- Every fix commit references its issue (`Closes #N` or `Refs #N`)
- Every phase completion is a commit
- Do not batch unrelated changes into one commit
- `IMPLEMENTATION.md` checkbox updates go in the same commit as the work they track
- Any commit that changes a component's public contract (function signatures, error types, endpoints, CLI interface) must update the corresponding section of `ARCHITECTURE.md` in the same commit

---

## Failure Handling

Any failure triggers the research sequence: **Hypothesis → online (docs + community) → source code.**

Do not retry without diagnosis. Do not proceed to the next task until the failure is understood.
Document findings as a comment on the open phase issue.

---

## Phase Gate

Discovery outputs (Phase 0) are hard prerequisites for implementation phases. No implementation code is written against undiscovered interfaces, APIs, or contracts.

---

## What Goes Where

- **Checkboxes** — task complete or not. Binary.
- **Issue comments** — everything else: failed attempts, decisions, partial findings, blockers.
- **`docs/`** — structured discovery outputs. Committed, permanent, readable by any session.
- **`docs/scope.md`** — standing strategy artifact. Scope ladder, terminal form, compiled terminal-bound constraints (HORIZONS.md). Updated by Orient and by Revision; never provisional.
- **`AGENTS.md`** — session bootstrap: prime directive, behavioral rules, declared conventions, current-phase pointer. Updated when phase changes. Consolidation beyond pointer-only is a declared adaptation, not a deviation.
- **`docs/walrus-YYYY-MM-DD.md`** — WaLRuS-DATA session summary. Written at session end, committed.

---

## Record Economics

Prose does not execute; lessons without enforcers are wishes.

- **One home per fact.** Verification narratives live in their verdict/record file (`docs/`) or on the issue they were filed to; every other surface points at that home. Each duplicate of a narrative multiplies the drift surface. Pointers at `docs/` homes are existence-verified by the gate; issue references are accepted as declared.
- **Content standards.** `ARCHITECTURE.md` lines = decision + choice + rationale + pointers, under their declared character budget (default ≤600, gated). `IMPLEMENTATION.md` = task state + pointers. `AGENTS.md` = bootstrap pointers + declarations. Dated chronicles belong in dated records (issues, WaLRuS, verdict files), never in living rows.
- **Digest step.** Inline repair of a falsified claim is immediate honesty; the same cycle then compresses the repaired surface back to its content standard, pointing at the verdict/record. Corrections add facts, not prose.
- **Lesson-Mechanism rule.** A recorded lesson must name its executing enforcer (a test, a gate, or a checklist item in a tool) or be explicitly marked ADVISORY (unenforced). Unenforced lessons are the gate backlog.
- **Property enumeration** (extends Post-Phase Audit step 4): every declared property in touched records ("pinned", "identical", "bounded", "100%", "never") is mapped to its executing check or marked UNENFORCED.

---

## Post-Phase Audit

After each phase completion, before writing the WaLRuS, audit the current project state against the constitution — `AGENTS.md`, `METHODOLOGY.md`, `ARCHITECTURE.md`, `IMPLEMENTATION.md`.

1. **ARCHITECTURE.md** — verify every component's key interface matches current code signatures
2. **Coverage** — run coverage; classify uncovered lines as *Acceptable* (document why) or *Gap* (add test)
3. **Cross-cutting** — scan for placeholder content, missing `.gitignore` entries, undocumented error types
4. **Declared claims vs evidence** — every constitutional statement that asserts something about the world (assumptions, measured numbers, verification dates) is checked against the project's evidence (`docs/`, issues, runs); stale or falsified claims are corrected in the same commit as the falsifying evidence, or marked open. Then, per Record Economics: enumerate every declared property in touched records and map each to its executing check, or mark it UNENFORCED
5. **Engineering invariants** — scan new and changed code against `ARCHITECTURE.md` Engineering Invariants and Banned Patterns; violations are closed or declared as documented deviations in `AGENTS.md` Conventions
6. **Horizon integrity** — error-signature scan per `HORIZONS.md`: override (continuation without a successor forecast), unbounded terminal position, level-versus-margin comparisons in the decision record, stale decomposition (repairs locally successful, gap class recurring), entitlement at threshold (activation treated as allocation), unregistered threshold crossing (an Operating commitment's Continuation/Exit condition met with no transition recorded)

Items 1–3 and 5 check internal consistency (code↔records↔constitution); item 4 checks external consistency (claims↔world); item 6 checks the plan against the horizon doctrine. Internal consistency alone cannot catch a claim that survives its own falsification.

Gaps must be closed or classified before the WaLRuS is written. The audit is a gate, not a suggestion.

---

## WaLRuS-DATA

**W**ins · **L**earnings · **R**isks · **S**trategy — **D**ecisions · **A**lignment · **T**radeoffs · **A**lternatives

The first four sections are backward-looking (what happened this session). The last four are structural (what was decided and why it stands).

At the end of any session with meaningful scope (phase completion, audit, significant fixes), write a `docs/walrus-YYYY-MM-DD.md` using the template at `docs/walrus-TEMPLATE.md`.

| Section | Content |
|---|---|
| **Wins** | What was completed and verified |
| **Learnings** | Non-obvious discoveries — API quirks, wrong assumptions corrected, surprises |
| **Risks** | Known latent issues, unverified assumptions, untested paths |
| **Strategy** | Where the project goes next and why |
| **Decisions** | Key choices made and their rationale |
| **Alignment** | Standing rules the project is now operating under |
| **Tradeoffs** | Accepted costs and why they were accepted |
| **Alternatives** | Options considered and rejected |

Keep entries concrete. No filler. Each line should be a fact a future session can act on.

---

## TDD

Tests are written before implementation code. Done means tests pass, not code written.

- Test files mirror source structure
- Each implementation task is preceded by a test task in `IMPLEMENTATION.md`
- Phase 0 (discovery) is exempt — no implementation code
- Spike code (throwaway exploration) is permitted during discovery only; contracts discovered by spiking are frozen, and tests are written against the frozen contract. Spikes never merge to main.
- "Done" = the verification statement at the bottom of the phase is true

**Test authenticity.** Tests execute against real ephemeral dependencies (containerized or disposable databases, queues, caches). Mocks are restricted to external third-party APIs. Tautological tests — asserting the call behavior of internal mocks — are banned. Coverage targets apply only to the invariants declared critical (financial, security, state-machine transitions), never as an aggregate line threshold.

---

## Quality Signals

When a measure becomes a target, it ceases to be a good measure. Optimizing for a metric produces the metric, not the thing the metric was meant to proxy.

**Coverage as diagnostic, not target.** Coverage is never optimized for directly. After significant work, uncovered lines are reviewed and classified:
- *Acceptable* — untestable path (browser automation, stdio transport, subprocess-only code). Document why.
- *Gap* — missing behavior coverage. File an issue or add a test.

The metric stays meaningful because it is never the goal.

**Prefer signals that are hard to fake** — passing integration tests on real infrastructure, user-reported defects, deployment frequency — over signals that are easy to inflate.

---

## What's Excluded and Why

- **Session log** — redundant with issue comments; grows noisy.
- **Branch-per-phase** — doesn't capture intra-phase progress or failures.
