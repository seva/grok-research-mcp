# Operating Cycle

A simple, iterative, scope-anchored loop. Deterministic: identical state yields identical next action. WIP limit = 1. Runs until the terminal form declared in the project's scope document (`docs/scope.md`).

---

## The Cycle

### 1. Orient — status quo against maximal scope

Inputs: `docs/scope.md` (including its compiled terminal-bound constraints), `IMPLEMENTATION.md`, open issues, latest WaLRuS, and realized RAROC of completed tasks.
Output: current scope position and the gap to the next rung.
Question answered: *where is the project on its ladder, and what is missing to reach the next level?*

Horizon check (`HORIZONS.md`): the compiled terminal-bound constraints are compared against the current reading — one comparison, no recomputation. A crossing found fires re-derivation of the affected commitment's far positions; a crossing absorbed without registering is a gap. Realized RAROC is itself a reading: it expires with substrate drift, and calibration older than the drift it measured is a stale claim, not evidence (Audit item 4 applies).

Commitment sweep (`HORIZONS.md`, Conditional commitments): each Operating commitment's Continuation and Exit conditions are compared against the current reading, with the declared hysteresis applied. A threshold crossed without a registered transition is a gap. A met Exit condition makes the transition eligible for exit capital even when expansion no longer pays; eligibility, not entitlement — the transition step still runs the selection function.

### 2. Decide — the next required atomic step

Select exactly one step satisfying all four:

- **Atomic** — completable in one session, one commit unit, verifiable
- **Gated** — depends on no undiscovered interface (METHODOLOGY.md Phase Gate)
- **Choosable** — requires no unsanctioned external dependency
- **Maximal** — highest RAROC among choosable steps that advance scope position and meet their Activation condition

**Decomposability** — atomicity constrains step granularity, never goal eligibility. A direction (a multi-step goal) that outranks the current step on RAROC must be decomposed into atomic steps and scored; it may not be dismissed as infeasible. Ranking ranks directions; Decide picks the next atomic step toward the top-ranked direction.

**Filter before rank** (`HORIZONS.md`) — directions carrying commitments that are negative at the terminal bound, or that spend irrecoverable margin for recoverable return, are excluded before any scoring runs. The boundary is a filter, not a term in a sum; no near return outweighs it, and no ratio computes it.

**Marginal, not level** — a step is scored by what the next increment of budget buys, at its commitment's current phase. Banked value of incumbent commitments never enters the comparison; a newcomer's full projected profile against an incumbent's remaining margin is the serial-abandonment error. Projected rates carry an epistemic discount (a lower P) — never a temporal one, and never disqualification.

**Refinement level scales with commitment cost** — recoverable steps are scored on scalar RAROC; steps committing irrecoverable margin are scored per horizon position (profile, not total) at the refinement set the commitment costs, and their profile is never aggregated into a single number.

RAROC = (V × P) / C — V: value protected or unlocked (1–5), P: probability it materializes (0–1), C: cost to remediate or execute (1–5). P is the epistemic discount; distance in time discounts nothing by itself.

Default Activation for recoverable scalar-scored steps is forecast RAROC ≥ 1, with V, P, C named on a channel independent of the claim. Steps committing irrecoverable margin take no scalar default — their Activation is a checkable profile condition at the refinement set their cost licenses (`HORIZONS.md`, Conditional commitments). The floor is universal for recoverable scalar steps: a step forecasting below it is ineligible, and argmax runs over eligible steps only. When choosable steps exist but none is eligible, none executes — the best sub-unit direction is surfaced to the Owner as a legislative signal (`surface` in the selection function); that branch never ends silently. Sub-unit = forecast RAROC < 1, below breakeven on the unit of account; the signal carries the best sub-floor choosable step and the direction it belongs to.

Every step that advances scope position is scored and its value made visible — including steps requiring unsanctioned external dependencies. Whenever the top-scoring feasible step is unchoosable solely for lack of sanction, it is surfaced to the Owner as a sanction decision — whether or not a lower-scoring choosable step executes. "Choosable" governs whether the cycle stalls, never whether a step is scored or surfaced.

Output: the step, recorded as a GitHub issue or an `IMPLEMENTATION.md` task, together with its expected-RAROC forecast (V, P, C) — the value that success must demonstrate. Steps that open or extend a commitment carry the conditional commitment record (`HORIZONS.md`, Conditional commitments — six fields, Activation through Authority), stated before execution, so the withdrawal conditions exist from the moment capital is committed. A met activation threshold makes a step eligible; selection still runs (entitlement at threshold is an error signature).
Never queue a second step; the next is chosen only after the current one completes.

### 3. Execute

TDD per METHODOLOGY.md — tests first. Done means the Definition of Success holds (below), not that code was written. Commit discipline applies; public-contract changes update `ARCHITECTURE.md` in the same commit.

### 4. Audit — evaluate against the constitution

Post-Phase Audit procedure (METHODOLOGY.md), generalized, executed per the role separation in `ROLES.md`: the Auditor verifies, the Critic falsifies, the Steward does not grade its own work.

1. `ARCHITECTURE.md` interfaces versus current code
2. Coverage run; uncovered lines classified *Acceptable* or *Gap*
3. Cross-cutting: placeholders, `.gitignore`, record sync (issues ↔ `IMPLEMENTATION.md`), session-protocol compliance
4. Declared claims versus evidence: constitutional statements about the world (assumptions, measured numbers, verification dates) checked against `docs/` and issue evidence; stale or falsified claims corrected or marked open
5. Engineering invariants: new and changed code scanned against `ARCHITECTURE.md` Engineering Invariants and Banned Patterns; violations closed or declared as deviations
6. Horizon integrity: error-signature scan per `HORIZONS.md` — override (continuation without a successor forecast), unbounded terminal position, level-versus-margin comparisons in the record, stale decomposition, under-refinement against the split signals, entitlement at threshold, unregistered threshold crossing

Output: classified gap list. Zero gaps is the only passing state.

### 5. Repair

Gaps ranked by RAROC, executed in order. Each gap is an atomic step of a repair sub-cycle — the same Definition of Success applies: return to step 4 after repairs until the audit passes clean.

**Revision escalation** (`HORIZONS.md`): repair inside the current decomposition is Adaptation. When repairs repeatedly succeed locally while the same audit findings or gap class recurs — no aggregate recovery — the decomposition itself has expired. Escalate to Revision: rebuild the phase and term structure (`IMPLEMENTATION.md`, `docs/scope.md`, declared non-drifting terms) instead of repairing within it. The recurrence record is one trigger; a decomposition that no longer yields any feasible step before the terminal form (feasible = ∅, selection function) is the second.

### 6. Repeat

Loop invariant at cycle exit: constitution clean, scope position non-decreasing.
Session end within a cycle: checkboxes updated, comment on the open issue, WaLRuS if the session had meaningful scope.

---

## Definition of Success

An atomic task succeeds iff all five hold. Success is a decidable conjunction, not a judgment:

1. **Pre-declared verification** — before execution, the task states one concrete, observable verification statement. Success is that statement being true. A task without a verification statement is not started.
2. **Proof, not claim** — proof is a working solution in production, actively demonstrating the expected RAROC. Tests, CI, and remote confirmations are correctness checks, not proof of value. Self-report is not evidence. Until a production surface exists, verification statements grant provisional success only — convertible to proof when the solution demonstrates its forecast value live.
3. **No constitutional regression** — `ARCHITECTURE.md` matches code; records in sync (issues ↔ `IMPLEMENTATION.md`); commit discipline observed; coverage has not regressed, and any new gap is closed or classified.
4. **Scope delta ≥ 0** — after completion, scope position is non-decreasing, and the task's contribution toward the next rung is nameable. Repair tasks satisfy this at delta = 0 by restoring the loop invariant.
5. **Legible** — completion leaves a trace: commit references its issue, checkbox flipped in the same commit, comment on the open issue.

**Corollary (atomicity test):** if any condition is undecidable within one session, the task is not atomic — split it until success becomes decidable. Atomicity and decidability of success define each other.

**Feedback:** realized RAROC of completed tasks is recorded at success and consumed by Orient to calibrate future forecasts. The selection loop is closed — estimates that do not materialize correct themselves.

---

## Autonomy

The cycle is self-sufficient by default: no step may require owner action or externally provisioned resources. When a step appears blocked on an external dependency, the dependency is inverted — the production surface is generated or reused by the project itself — before the step may be declared blocked.

The owner stands outside the cycle as its legislative layer and may sanction exceptions by prompt. A sanctioned prompt is an auditable constitutional act and the only legitimate path by which an external dependency enters the cycle. Every sanction is recorded on the relevant issue. Absent sanction, the cycle never stalls on external provisioning.

External prerequisites are real: they block the deployments they gate, and gap analysis states them plainly. Sanction is permission, not provision — the owner legislates the exception; the provisioning work belongs to the cycle (autonomous stand-up). "Blocked on owner" is not a state the cycle may occupy; absent sanction, the state is inversion, not waiting.

Disposition is legislative. Deciding that a commitment has reached Acceptance — longevity (preserve the substrate, extend current positions) versus seeding (fund a successor, release the substrate) — and deriving a successor at Reinception are Owner acts of the sanction class: surfaced by the cycle with its evidence, decided outside it, recorded on the relevant issue. The cycle never disposes of the entity it runs in.

---

## Selection function (compressed)

```
filter    = directions whose commitments are negative at the terminal bound, or that spend
            irrecoverable margin for recoverable return, are excluded before scoring
            (HORIZONS.md) — the boundary is never a term in a sum
feasible  = { s : advances scope position ∧ passes phase gate ∧ atomic ∧ survives filter }
choosable = { s ∈ feasible : requires no unsanctioned external dependency }
scored    = feasible — every feasible step is scored and made visible, sanctioned or not
score     = marginal return of the next budget increment at the commitment's current
            phase; banked value never enters; projections carry an epistemic discount P,
            never a temporal one
refine    = recoverable steps scored scalar; steps committing irrecoverable margin scored
            per-position (profile, not total) at the set their cost licenses
decompose = atomicity constrains step granularity, never goal eligibility; a direction
            that outranks the current step is decomposed into atomic steps and scored,
            never dismissed whole; ranking ranks directions, Decide picks the next atomic
            step toward the top-ranked direction
eligible  = { s ∈ choosable : s meets its Activation condition — forecast RAROC ≥ 1 for
            recoverable scalar steps; the licensed profile condition for steps committing
            irrecoverable margin (HORIZONS.md, Conditional commitments) }
next_step = argmax RAROC(s) over s ∈ eligible, if eligible ≠ ∅
            else no step executes; choosable = ∅ with feasible ≠ ∅ ⇒ the top-scoring
            feasible step awaits sanction; eligible = ∅ with choosable ≠ ∅ ⇒ sub-unit
            signal (surface); feasible = ∅ ⇒ neither signal has a referent — Orient
            resolves which state obtains (surface)
commit    = evaluated after next_step, on the step that opens or extends a commitment:
            s survives filter ∧ activation evidence valid ∧ s = next_step
            (HORIZONS.md, Conditional commitments) — a met threshold establishes
            eligibility, never entitlement; Operating commitments are swept each
            Orient for Continuation/Exit with declared hysteresis
surface   = two legislative signals to the Owner: the top-scoring feasible step is
            unchoosable ⇒ sanction decision, whether or not a choosable step executes;
            choosable ≠ ∅ and every choosable step falls below its Activation condition
            ⇒ sub-unit signal — the best sub-unit direction is surfaced, never a
            silent stall. feasible = ∅ routes to Orient, not to a signal: the terminal
            form is reached (convergence, Termination) or the decomposition yields no
            steps (expired — escalate to Revision, joining the recurrence record as a
            second trigger)
revise    = (repairs locally successful ∧ gap class recurs) ∨ feasible = ∅ before the
            terminal form ⇒ decomposition expired; rebuild term/phase structure instead
            of repairing within it
proof     = working in production ∧ expected RAROC actively demonstrated
```

---

## Termination

Asymptotic. The cycle runs until the terminal form declared in `docs/scope.md`. There is no completion, only convergence.

Scale condition (`HORIZONS.md`): cycle termination is project-scale — a successor state exists, so the record of where Ends fell against where they were called calibrates the next cycle. The operator-scale bound is never modeled inside the cycle; modeling it there would give the terminal position a successor, unbound it, and remove the filter. It lives compiled in `docs/scope.md` and is owned by the Owner.
