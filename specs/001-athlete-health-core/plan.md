# Implementation Plan: Core Athlete Health & Performance System

**Branch**: `001-athlete-health-core` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-athlete-health-core/spec.md`
**Constitution**: [v1.0.0](../../.specify/memory/constitution.md) | **ADR**: [ADR-0001 (Accepted)](../../history/adr/0001-audit-log-storage-mechanism.md)

## Summary

Deliver deterministic injury-risk scoring for women athletes, with sex-specific physiology
modelled as first-class input, plan proposals that cannot activate without a tiered human
approval, and every decision written to a tamper-evident audit chain before the response returns.
Technical approach: a pure-Python deterministic Risk Engine with no network or LLM dependency, a
thin orchestrator that re-checks the deterministic verdict at the response boundary, and
PostgreSQL carrying both guarantees below the application — append-only hash chaining via triggers
and consent enforcement via forced Row-Level Security (ADR-0001).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy or asyncpg, Next.js 15, Tailwind CSS
**Storage**: PostgreSQL 16+ — RLS with `FORCE ROW LEVEL SECURITY`, append-only audit triggers
**Testing**: pytest, plus mutation testing (mutmut or cosmic-ray) over the Risk Engine
**Target Platform**: Linux server; browser client
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Not constrained — Prototype track. The audit write is on the request's
critical path by design (FR-008); correctness precedes latency here.
**Constraints**: Risk Engine must be pure and offline-capable; audit entry must be durable before
response; no raw health data in logs, traces, or errors (FR-018)
**Scale/Scope**: Demo scale — tens of athletes, single coach org, manual metric entry only (FR-025)

**LLM usage**: confined to narrative explanation (FR-002). The provider is **not yet decided** —
see Deferred Decisions. Whichever is chosen, the exact model ID must be pinned and recorded in
every audit entry (FR-008 requires model versions), so "Claude / GPT-4o" is not a resolvable
choice as written.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate question | Status | Evidence |
|---|-----------|---------------|--------|----------|
| I | Guarantee in code | Safety-critical thresholds deterministic and re-checked at the API boundary? LLM confined to explanation? | PASS | Risk Engine is a pure module, no network/LLM import. Boundary re-check per FR-003. Rule set identified by content hash so the pinned version is not merely declared. |
| II | Human-in-the-loop | Every irreversible action requires explicit recorded approval? | PASS | Tiered approval FR-021; elevated/high → coach only; unaffiliated athlete at elevated risk fails closed (US2 scenario 8). |
| III | Women-first | Measurable equity claim and sex-specific factors modelled? | PASS | EQ-001/002; FR-015, FR-016 (three distinct cycle states), FR-017 (no male-default substitution). |
| IV | Fail closed | Missing / stale / low-confidence → withhold and escalate? | PASS | FR-006, FR-022 (per-metric windows), FR-023 (0.7 floor), SA-001. |
| V | Auditability | Hash-chained and independently verifiable? | **PARTIAL — see Complexity Tracking** | Chain + triggers per ADR-0001 hold against the application and its callers. Independence from the database operator requires FR-010a, which is not delivered until Phase 3. |
| VI | Privacy & consent | Consent enforced at the data-store layer? | **PASS, conditional** | RLS + `FORCE ROW LEVEL SECURITY` + non-owner, non-`BYPASSRLS` app role (ADR-0001 conditions 1–2). Conditional on the caller-identity propagation mechanism below being built in Phase 0 — without it RLS has no subject to filter on. |
| VII | Explainability | Every score returns evidence from the same computation? | PASS | FR-013, FR-014 — the Risk Engine returns evidence as part of its result value, not via a second call. |
| VIII | Spec-driven | Failing tests exist, including refusal paths? | **PASS, conditional** | SC-003, SC-004, SC-005, SC-005a, SC-008, SC-011, SC-012 are all test obligations. Conditional on refusal tests being written in the phase that builds each path, not deferred — see Complexity Tracking. |

**Re-check after Phase 1 design**: required. Principle V stays PARTIAL until FR-010a ships.

### Gate blocker resolved during planning: RLS caller identity

Principle VI's PASS depends on something the submitted plan did not specify. RLS policies filter
on a subject, and a pooled application connection has no inherent notion of "the current athlete".
The application must propagate caller identity into the database session — a transaction-scoped
session setting (`SET LOCAL`) read by the policy expression, set from the verified JWT claim at
the start of every request transaction, and never from a client-supplied header.

This is load-bearing: if it is missed, RLS policies still exist, still appear enforced, and filter
against an empty or wrong subject. Phase 0 must include a test that reads health data with the
session setting unset and asserts zero rows.

## Project Structure

### Documentation (this feature)

```text
specs/001-athlete-health-core/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality validation
└── tasks.md             # Phase 2 output (/sp.tasks — NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── risk_engine/          # PURE. No network, no LLM, no DB imports.
│   │   ├── rules.py          # Version-pinned deterministic rules
│   │   ├── factors.py        # Sex-specific factor modelling (FR-015, FR-016)
│   │   ├── freshness.py      # Per-metric windows (FR-022)
│   │   ├── confidence.py     # Confidence computation (FR-023)
│   │   └── version.py        # Rule set identity by content hash
│   ├── orchestrator/
│   │   ├── assess.py         # Risk assessment flow
│   │   ├── propose.py        # Plan proposal generation
│   │   ├── approval.py       # Tiered approval gate (FR-021)
│   │   └── boundary.py       # Verdict re-check before serialisation (FR-003)
│   ├── audit/
│   │   ├── writer.py         # Append; serialised (ADR-0001 condition 4)
│   │   ├── verifier.py       # Independent chain verification (FR-010)
│   │   └── anchor.py         # External chain-head publication (FR-010a)
│   ├── consent/              # Purpose-scoped consent records
│   ├── explanation/          # LLM narrative ONLY (FR-002, FR-014)
│   ├── api/                  # FastAPI routes, auth, session identity propagation
│   └── models/               # Persistence models
├── migrations/               # Schema, RLS policies, audit triggers
└── tests/
    ├── contract/
    ├── integration/
    ├── refusal/              # Every SA-001 refusal path (SC-004)
    ├── security/             # RLS bypass attempts, audit tamper attempts
    └── unit/

frontend/
├── src/
│   ├── components/           # Evidence display, approval controls
│   ├── pages/                # Athlete dashboard, coach approval view
│   └── services/
└── tests/
```

**Structure Decision**: Web application — a FastAPI backend and a Next.js frontend, as the feature
has both a coach approval surface and an athlete dashboard. The Risk Engine is deliberately a
sibling package to the orchestrator rather than a layer inside it, so its purity (Principle I) is
enforceable by an import test rather than by convention: `risk_engine` may not import from
`orchestrator`, `api`, `audit`, or any network or LLM library.

## Implementation Phases

Phase ordering below differs from the submitted plan. See Complexity Tracking for why.

### Phase 0 — Foundation and enforcement layer

- Project structure; backend and frontend scaffolds
- PostgreSQL schema; RLS policies with `FORCE ROW LEVEL SECURITY`; append-only audit triggers
- Non-owner, non-`BYPASSRLS` application role
- **Caller identity propagation into the database session** (gate blocker above)
- **Audit write durability decided and implemented** — ADR-0001 condition 5
- **Serialised chain append** — ADR-0001 condition 4
- Auth (JWT); seed data for women athletes
- Security tests: RLS bypass attempts, audit `UPDATE`/`DELETE` attempts, unset-identity read

### Phase 1 — Risk Engine

- Deterministic scoring; version-pinned rules identified by content hash
- Sex-specific factors as first-class inputs (FR-015, FR-016, FR-017)
- Per-metric freshness (FR-022) and confidence (FR-023)
- Unit tests plus mutation testing; repeatability trials (SC-008); boundary tests on each side of
  every freshness window (SC-012)
- **Refusal-path tests for every condition this phase introduces** (SC-004)

### Phase 2 — Core flow

- Manual metric ingestion, with capture time distinct from ingestion time (FR-024)
- Risk assessment endpoint; boundary verdict re-check (FR-003)
- Plan proposal generation and state machine
- Tiered approval gate (FR-021), including refused self-approval and the no-coach case
- **Refusal and approval-refusal tests written with each path** (SC-003, SC-011)

### Phase 3 — Independence and hardening

- External chain-head anchoring (FR-010a) → closes Principle V to PASS
- Rewritten-chain detection trials (SC-005a)
- Explanation service with the unavailable-path fallback (spec edge case: score and evidence must
  still be deliverable)
- Log/trace scrubbing verification (FR-018)

### Phase 4 — Frontend and demo

- Athlete dashboard with evidence display
- Coach approval view showing risk band and why approval is required
- Refusal states rendered as first-class UI, not error toasts — a withheld score with a stated
  reason is a product feature (Principle IV), not a failure
- Demo script and video

## Deferred Decisions

- **LLM provider and model ID**: unresolved. "Claude / GPT-4o" cannot be pinned, and FR-008
  requires the model version in every audit entry. Pick one provider and pin an exact current
  model ID before Phase 3. If Claude, use a current model (the Claude 5 family — e.g.
  `claude-sonnet-5`); `gpt-4o` is a notably older model and a poor default for new work.
  Low-stakes under Principle I — the LLM cannot affect any score — but it must be *recorded*.
- **Risk band boundaries** (0–39 / 40–59 / 60–79 / 80–100): provisional engineering defaults per
  spec Assumptions. Need sports-science validation before any non-prototype use. The tiering rule
  (FR-021) is fixed; the numbers are not.
- **Hosting**: Railway / Vercel / local — no architectural consequence at this scale.

## Out of Scope for Prototype

Real wearable integrations; mobile app; team or squad analytics; season periodisation; any
diagnosis or treatment feature (permanently out of scope, FR-020).

## Risks

| Risk | Blast radius | Mitigation / guardrail |
|------|--------------|------------------------|
| Principle V unmet during Phases 0–2 | Any audit evidence gathered before Phase 3 is not defensible against a database operator | Do not present the prototype as independently auditable until FR-010a ships. Tracked below. |
| RLS identity propagation missed or subverted | Total consent bypass, silent — policies appear enforced while filtering on nothing | Phase 0 test asserting zero rows with identity unset; identity set only from a verified token claim, never a client header |
| Risk bands not clinically validated | Wrong approval tier applied; athlete self-approves a genuinely high-risk plan | Marked provisional in spec Assumptions; validate before non-prototype use |
| Concurrent audit inserts fork the chain | Verification fails, or worse, passes over a fork | Serialised append (advisory lock); concurrency test in Phase 0 |
| Audit lost on transaction rollback | Refusals — the exact evidence Principle IV wants — vanish | Decided explicitly in Phase 0 per ADR-0001 condition 5 |
| Risk Engine purity erodes by import creep | Principle I silently violated | Automated import-boundary test in CI, not code review |

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Principle V is PARTIAL, not PASS, at the gate.** The submitted plan recorded this as "PARTIAL → PASS after FR-010a". That is a forecast, not a gate result — the gate asks what is true now. Phases 0–2 produce a system whose audit chain is tamper-evident against the application but not against a database operator. | FR-010a's external anchoring depends on an audit chain existing to anchor, so it cannot precede Phase 0. Sequencing it into Phase 3 is a genuine dependency, not a convenience. | Building anchoring in Phase 0 was rejected as impossible (nothing to anchor). Claiming PASS on the strength of a later phase was rejected because it is exactly the tick the constitution's compliance review exists to prevent — a partially met principle recorded as met is indistinguishable from a met one at review time. **Guardrail**: the prototype must not be described as independently auditable, in the demo or elsewhere, until FR-010a ships. |
| **Refusal-path tests distributed across phases rather than gathered in a hardening phase.** The submitted plan placed "full refusal path tests" in Phase 3. | Principle VIII requires tests written and failing before implementation. A refusal path built in Phase 1 and tested in Phase 3 is untested code in the interim, and the interim is where demos happen. | Deferring all refusal tests to a hardening phase was rejected: it inverts Principle VIII, and the refusal paths are the safety guarantee, not a finishing touch. Phase 3 retains only the tests that genuinely depend on Phase 3 artifacts (SC-005a rewritten-chain detection). |
| **Audit durability, chain serialisation, and RLS identity propagation moved from Phase 3 to Phase 0.** | All three are schema- and call-site-shaped. Retrofitting an autonomous audit write after Phase 2 changes every call site that writes an audit entry; retrofitting identity propagation changes every policy and every request path. | Leaving them in a hardening phase was rejected as a false economy — they are cheap to build first and expensive to insert later, and until they exist the Principle VI PASS is not real. |

## Next Steps

1. `/sp.tasks` to generate the dependency-ordered task list from this plan.
2. Resolve the LLM provider and pin an exact model ID before Phase 3.
3. Re-run the Constitution Check after Phase 1 design, per the gate.
