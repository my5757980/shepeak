# Tasks: Core Athlete Health & Performance System

**Feature**: `001-athlete-health-core` | **Date**: 2026-09-06
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md) | **ADR**: [ADR-0001](../../history/adr/0001-audit-log-storage-mechanism.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]** — may run in parallel with other `[P]` tasks in the same block (different files, no
  shared dependency).
- **[US1]–[US4]** — the user story the task serves. Unmarked tasks are shared infrastructure.
- **Tests are MANDATORY** (Constitution Principle VIII): written first, failing, before the
  implementation task they guard. Safety-critical behavior additionally gets a refusal-path test.

## Path Conventions

Backend `backend/src/...`, tests `backend/tests/...`, migrations `backend/migrations/...`,
frontend `frontend/src/...` — per plan.md Source Code layout.

---

## Phase 0 — Foundation and enforcement layer

Nothing in later phases is trustworthy until this phase holds. Three tasks here (T0.4, T0.7,
T0.8) were moved forward from the submitted Phase 3 because they are call-site-shaped and
expensive to retrofit.

### Project setup

- [x] T0.10 Monorepo structure — `backend/`, `frontend/`, tooling, CI entry point
- [x] T0.11 [P] JWT auth issuing verified claims for athlete and coach roles
- [x] T0.12 [P] Import-boundary test asserting `risk_engine` imports nothing from `orchestrator`,
      `api`, `audit`, `consent`, `explanation`, or any network/LLM library —
      `backend/tests/unit/test_import_boundary.py` (Principle I; guards T1.*)

### Schema and roles

- [x] T0.1 PostgreSQL schema — Athlete, ConsentRecord, HealthMetric, RuleSetVersion,
      RiskAssessment, PlanProposal, ApprovalRecord, AuditEntry, Escalation —
      `backend/migrations/001_schema.sql`
- [x] T0.2 `ENABLE` + `FORCE ROW LEVEL SECURITY` and purpose-scoped policies on all health tables
      (ADR-0001 condition 1) — `backend/migrations/002_rls.sql`
- [x] T0.3 Non-owner application role: no table ownership, no `BYPASSRLS`, not superuser
      (ADR-0001 condition 2) — `backend/migrations/003_roles.sql`
- [x] T0.4 Transaction-scoped identity propagation — `SET LOCAL` from the **verified JWT claim**,
      never a client-supplied header; policies read it — `backend/src/api/session_identity.py`

### Audit substrate

- [x] T0.6 Append-only audit triggers + hash chaining —
      `backend/migrations/004_audit_triggers.sql`
- [x] T0.7 Serialise concurrent audit appends (advisory lock on the chain) — ADR-0001 condition 4
- [x] T0.8 **Decide and document** audit write durability under caller rollback, then implement —
      ADR-0001 condition 5. The decision must state what happens to a decision whose transaction
      later aborts; a refusal that vanishes on rollback is the exact evidence Principle IV wants.
      Record the choice and its justification in the ADR or a follow-up ADR, not only in code.

### Phase 0 security tests — write before the task each guards

- [x] T0.5 [P] Read health data with session identity **unset** → zero rows (SC-006)
- [x] T0.13 [P] Read another athlete's health data as an authenticated athlete → zero rows (SC-006)
- [x] T0.14 [P] Read health data **bypassing application code**, connecting directly as the
      application role with no covering consent → zero rows (SC-006, FR-011)
- [x] T0.15 [P] `UPDATE` and `DELETE` on `AuditEntry` as the application role → fails, and the
      attempt is itself recorded (FR-009)
- [x] T0.16 [P] Concurrent audit appends under load produce an unforked, verifiable chain (T0.7)
- [x] T0.17 [P] Audit entry survives / behaves as decided when the caller transaction rolls back
      (T0.8)

### Seed

- [x] T0.9 Seed realistic women athlete data, consent records, and coach assignments — including
      one athlete with **no assigned coach** (needed by T2.12) and one with contraception-suppressed
      cycle data (needed by T1.9)

**Phase 0 checkpoint**: Principle VI PASS becomes real here. Do not proceed until T0.5, T0.13,
T0.14, T0.15 pass.

---

## Phase 1 — Risk Engine (deterministic core)

Pure module. No network, no LLM, no DB. Guarded by T0.12.

- [x] T1.1 Versioned Rule Set with content-hash identity — `backend/src/risk_engine/version.py`
- [x] T1.2 [US1] Sex-specific factors: cycle phase, contraception, iron status, RED-S indicators,
      ACL mechanics — `backend/src/risk_engine/factors.py` (FR-015)
- [x] T1.9 [US1] **Three distinct cycle states** — not recorded / recorded as absent / suppressed
      by contraception — modelled as separate values, never collapsed (FR-016). Absent menses is a
      RED-S signal, not missing data.
- [x] T1.3 [US1] Per-metric freshness windows — `backend/src/risk_engine/freshness.py` (FR-022)
- [x] T1.4 [US1] Confidence computation and 0.7 floor — `backend/src/risk_engine/confidence.py`
      (FR-023)
- [x] T1.5 [US1] Risk bands — provisional 0–39 low, 40–59 moderate, 60–79 elevated, 80–100 high.
      Mark provisional in code, not only in the spec.
- [x] T1.16 [US1] Cricket bowling workload as a first-class load input — overs bowled, spell
      density, consecutive playing days — with the rule structure kept sport-agnostic (FR-026)
- [x] T1.10 [US1] Evidence returned as part of the engine's result value — contributing metrics
      with values and capture timestamps, plus rule identifiers and versions (FR-013, FR-014,
      SA-004). Not a second call, not reconstructed.
- [x] T1.11 [US1] Refusal result type carrying a machine-readable reason, the offending input, and
      the computed confidence (FR-006, FR-007, FR-023)

### Phase 1 tests — written first, failing

- [x] T1.6 Unit tests for every rule
- [x] T1.7 Mutation testing over safety rules — a removed or inverted rule MUST fail a test
- [x] T1.8 [P] Refusal path tests: missing, stale, and low-confidence, for each condition
      introduced here (SC-004)
- [x] T1.12 [P] Boundary tests on **each side** of all six freshness windows — refusal one
      interval past, score one interval inside (SC-012)
- [x] T1.13 [P] Repeatability trials — identical inputs + rule version → identical score (SC-008,
      Principle I)
- [x] T1.14 [P] No male-default substitution: with a sex-specific input absent, assert the output
      states the absence and no default value was applied (FR-017, SC-002)
- [x] T1.15 [P] Sex-specific citation: with data present, every score cites ≥1 sex-specific factor
      (SC-001, EQ-001)

---

## Phase 2 — Core flow

- [x] T2.1 [US1] Manual metric ingestion — capture time distinct from ingestion time; source
      recorded; staleness measured against **capture** time (FR-024, FR-025)
- [x] T2.2 [US1] Risk assessment endpoint calling the pure engine
- [x] T2.6 [US1] Audit entry written before every response, including refusals (FR-008)
- [x] T2.7 [US1] Escalation on refusal — to the assigned coach, or to the athlete when unassigned
      (SA-001)
- [x] T2.8 [US1] Superseded score retained in the audit record when late-arriving data forces
      recomputation (FR-019)
- [x] T2.4 [US2] Plan proposal generation and state machine — proposed / approved / rejected /
      superseded
- [x] T2.5 [US2] Tiered approval gate — coach mandatory at elevated and high; athlete may
      self-approve below (FR-021, FR-004)
- [x] T2.9 [US2] Approval invalidation — an approval does not survive modification of the approved
      artifact; re-approval required (FR-005)
- [x] T2.3 [US2] Boundary re-check — narrative contradicting the deterministic verdict returns an
      error, not the narrative (FR-003) — `backend/src/orchestrator/boundary.py`
- [x] T2.13 [US2] Diagnosis / treatment guard — a request whose output would constitute diagnosis
      or treatment is refused and escalated (FR-020, SA-005)
- [x] T2.14 [US4] Consent grant and withdrawal — purpose-scoped, revocable; withdrawal stops
      future processing within the declared window while retaining prior audit entries (FR-012)
- [x] T2.15 Log, trace, and error scrubbing — no raw health data in any of them (FR-018)

### Phase 2 tests — written first, failing

- [x] T2.10 [P] [US2] Activation attempted through every path with no approval record → refused
      and the refused attempt recorded (SC-003)
- [x] T2.11 [P] [US2] Athlete self-approval of an elevated/high-risk plan → refused (SC-011)
- [x] T2.12 [P] [US2] Athlete with **no assigned coach** + elevated risk → plan stays inactive,
      reason names the absent coach approver. Fails closed; does **not** fall back to
      self-approval (US2 scenario 8)
- [x] T2.16 [P] [US4] Consent withdrawal stops processing within the declared window (SC-010)
- [x] T2.17 [P] [US1] Every score response carries contributing metrics with timestamps and the
      rule versions that fired (SC-007)
- [x] T2.18 [P] Audit entry exists **before** the response is observable by the caller (FR-008)

---

## Phase 3 — Independence and hardening

- [x] T3.5 [US1] **Pin the exact LLM model ID** — do this *before* T3.6, not after. FR-008
      requires the model version in every audit entry, so an unpinned provider blocks the
      explanation service, not the other way round.
- [x] T3.6 [US1] Explanation service — narrative only, generated from the same computation that
      produced the score (FR-002, FR-014)
- [x] T3.7 [US1] Explanation-unavailable fallback — the score and its structured evidence are
      still delivered when narrative generation fails (spec edge case)
- [x] T3.8 [P] Test: LLM output cannot alter any score, threshold, or band (FR-002, Principle I)
- [x] T3.2 [US3] Independent integrity check — verifiable with read access and the chain rule
      alone, without trusting the application (FR-010)
- [x] T3.9 [P] [US3] Altered-entry detection trials → detected 100% (SC-005)
- [x] T3.3 End-to-end refusal tests across the full stack — integration only; the per-path unit
      refusal tests belong to T1.8 and T2.10–T2.12 and must already pass

### Deferred to roadmap — demo-first cut (2026-09-06)

Not deleted. Stated in the submission as roadmap, and **not claimed as delivered**.

- [ ] ~~T3.1 External chain-head anchoring (FR-010a)~~ → **Principle V remains PARTIAL. The
      submission, pitch deck, and demo video MUST NOT describe the audit log as "independently
      verifiable" or "tamper-proof". Accurate wording: "append-only and tamper-evident against
      the application; independent anchoring is on the roadmap."**
- [ ] ~~T3.10 Rewritten-chain detection (SC-005a)~~ — depends on T3.1
- [ ] ~~T3.4 Concurrent load tests~~ — moot at prototype volumes

---

## Phase 4 — Frontend and demo

- [x] T4.1 [US1] Athlete dashboard — score, evidence, and **refusal states as first-class UI**
      with the stated reason; not an error toast
- [x] T4.7 [P] [US1] Evidence display component — metrics with capture times, rules with versions,
      sex-specific factors surfaced
- [x] T4.2 [P] [US2] Coach approval view — risk band shown, and why coach approval is required
- [x] T4.3 [US2] Plan proposal review, approve, reject
- [x] T4.8 [P] [US4] Consent management view — grant and withdraw by purpose
- [x] T4.10 [P] Accessibility — WCAG 2.2 AA across athlete and coach surfaces; score, evidence and
      refusal reason each completable by keyboard and screen reader alone (FR-027, SC-013)
- [x] T4.11 [P] Second language covering refusal reasons and evidence labels, not only navigation
      (FR-028, SC-014)
- [x] T4.4 Seed demo data covering happy path **and** refusal path scenarios

### Submission deliverables (competition rules, not engineering)

- [x] T4.12 **USP statement** — one page: what ShePeak does that existing tools do not, and why
      the deterministic safety core plus tiered human approval plus sex-specific physiology is a
      combination nobody else ships. Feeds judging criterion 1 (**25%**, our weakest). Write this
      first — it shapes the deck and the video.
- [x] T4.13 Written summary, max 2 pages — problem statement, proposed solution, impact for women
      in sport (required minimum submission; currently missing)
- [x] T4.6 Pitch deck, max 5 slides
- [x] T4.5 3-minute demo video **script**
- [ ] T4.14 **Record and edit the demo video**, 3 min hard maximum — the script is not the
      deliverable
- [x] T4.15 Submission accuracy review — automated as `tests/unit/test_submission_claims.py`
      rather than left as a checklist item; a review that must be remembered under deadline
      pressure is a review that does not happen. Original scope: — verify no artifact claims independent auditability
      (T3.1 deferred), and that risk band numbers are presented as provisional

### Deferred to roadmap

- [ ] ~~T4.9 Comprehension study, 90% unaided (SC-009)~~ — needs real athletes and recruiting lead
      time; restated as post-submission validation

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 0 blocks everything.** T0.4 (identity propagation) blocks every RLS guarantee; T0.6–T0.8
  block every audit write in Phase 2.
- **Phase 1 depends on** T0.12 only (the purity guard). It is otherwise independent of Phase 0 —
  the Risk Engine touches no database, so Phases 0 and 1 can proceed in parallel by two people.
- **Phase 2 depends on** Phase 0 (schema, audit, RLS) and Phase 1 (engine, evidence, refusal type).
- **Phase 3 depends on** Phase 2, except T3.5 which can be decided at any time and blocks T3.6.
- **Phase 4 depends on** Phase 2 for real data; T4.9 needs recruiting lead time.

### Critical path

T0.1 → T0.2 → T0.3 → T0.4 → T0.6 → T0.7/T0.8 → T2.2 → T2.6 → T2.5 → T3.1 → T3.10

### Parallel opportunities

- All Phase 0 security tests (T0.5, T0.13–T0.17) are independent of each other.
- Phase 1 in full can run alongside Phase 0.
- All Phase 1 test tasks T1.8, T1.12–T1.15 are independent.
- T4.2, T4.7, T4.8 are separate components.

---

## Requirement Coverage

Every FR, SA and SC traced to the task that satisfies it. Rows marked **+** were not in the
submitted task list.

| Req | Task(s) | | Req | Task(s) |
|---|---|---|---|---|
| FR-001 | T1.1, T1.13 | | FR-020 **+** | T2.13 |
| FR-002 **+** | T3.6, T3.8 | | FR-021 | T2.5, T2.11, T2.12 |
| FR-003 | T2.3 | | FR-022 | T1.3, T1.12 |
| FR-004 | T2.5, T2.10 | | FR-023 | T1.4, T1.11 |
| FR-005 **+** | T2.9 | | FR-024 | T2.1 |
| FR-006 | T1.11, T1.8 | | FR-025 | T2.1 |
| FR-007 | T1.11 | | SA-001 | T2.7, T1.8 |
| FR-008 | T2.6, T2.18 | | SA-002 | T2.5, T2.10 |
| FR-009 **+** | T0.15 | | SA-003 | T0.2, T0.14 |
| FR-010 | T3.2 | | SA-004 | T1.10, T2.17 |
| FR-010a | T3.1 | | SA-005 **+** | T2.13 |
| FR-011 | T0.2, T0.14 | | SC-001 **+** | T1.15 |
| FR-012 **+** | T2.14, T2.16 | | SC-002 **+** | T1.14 |
| FR-013 | T1.10, T2.17 | | SC-003 | T2.10 |
| FR-014 **+** | T1.10, T3.6 | | SC-004 | T1.8, T3.3 |
| FR-015 | T1.2 | | SC-005 **+** | T3.9 |
| FR-016 **+** | T1.9 | | SC-005a **+** | T3.10 |
| FR-017 **+** | T1.14 | | SC-006 **+** | T0.5, T0.13, T0.14 |
| FR-018 **+** | T2.15 | | SC-007 **+** | T2.17 |
| FR-019 **+** | T2.8 | | SC-008 **+** | T1.13 |
| | | | SC-009 **+** | T4.9 |
| | | | SC-010 **+** | T2.16 |
| | | | SC-011 | T2.11 |
| | | | SC-012 **+** | T1.12 |
| FR-026 | T1.16 | | SC-013 | T4.10 |
| FR-027 | T4.10 | | SC-014 | T4.11 |
| FR-028 | T4.11 | | | |

**Coverage: 29/29 FR, 5/5 SA, 15/15 SC.**

Two criteria are **deferred, not covered**, by the demo-first cut: SC-005a (T3.10) and SC-009
(T4.9). Both are stated as roadmap in the submission rather than claimed.

---

## 🔴 Blocking, outside this task list

**The team has no female contributor.** The competition rule — "Team must consist of at least one
female contributor" — is an eligibility gate. Until it is resolved, every task above produces work
that cannot be submitted. It is the highest-priority item in the project and belongs to the first
week. See [hackathon-alignment.md](./hackathon-alignment.md).

---

## Definition of Done (every task)

- Tests written first and failing before the implementation
- Refusal paths covered where the task introduces one
- Constitution principles touched are stated in the commit
- Audit entry created where the task produces a decision
- No raw health data in logs, traces, or error messages (FR-018)

> **Note**: the repository is not currently a git repository, so "stated in the PR/commit" has
> nowhere to land. Run `git init` before Phase 0 — the DoD, the ADR trail, and Principle VIII's
> review gate all assume version control.
