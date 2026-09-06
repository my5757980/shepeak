---
id: 0005
title: Implementation Plan Constitution Check
stage: plan
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: 001-athlete-health-core
branch: 001-athlete-health-core (no git repo; directory naming only)
user: ms5373268@gmail.com
command: /sp.plan
labels: ["plan", "constitution-check", "rls", "audit-chain", "phase-ordering", "fastapi", "postgresql"]
links:
  spec: specs/001-athlete-health-core/spec.md
  ticket: null
  adr: history/adr/0001-audit-log-storage-mechanism.md
  pr: null
files:
  - specs/001-athlete-health-core/plan.md
  - history/adr/0001-audit-log-storage-mechanism.md
tests:
  - none run (planning artifact; test obligations assigned to phases)
---

## Prompt

/sp.Plan — Core Athlete Health & Performance System

**Feature**: 001-athlete-health-core  
**Track**: Prototype  
**Date**: 2026-09-06  
**Status**: Ready for implementation  
**Constitution Version**: 1.0.0  
**ADR**: ADR-0001 (Accepted) — PostgreSQL + Triggers + RLS + external chain-head anchoring

---

## 1. Constitution Check

| # | Principle | Gate Question | Status | Evidence |
|---|-----------|---------------|--------|----------|
| I | Guarantee in code | Are all safety-critical thresholds deterministic and re-checked at the API boundary? Is the LLM confined to explanation? | PASS | Risk Engine is pure deterministic Python module. LLM only used for narrative. Boundary re-check required (FR-003). |
| II | Human-in-the-loop | Does every irreversible action require explicit recorded coach/athlete approval? | PASS | Tiered approval (FR-021). Elevated/High → Coach only. Low/Moderate → Athlete self-approve allowed. |
| III | Women-first | Measurable equity claim + sex-specific factors modelled? | PASS | EQ-001/002 + FR-015, FR-016, FR-017. |
| IV | Fail closed | Missing/stale/low-confidence → withhold + escalate? | PASS | FR-006, FR-022, FR-023 + SA-001. |
| V | Auditability | Hash-chained + independently verifiable? | PARTIAL → PASS after FR-010a | ADR-0001 + FR-010a (external chain head). |
| VI | Privacy & Consent | Consent enforced at database layer? | PASS | RLS + FORCE ROW LEVEL SECURITY (ADR-0001). |
| VII | Explainability | Every score returns exact evidence from same computation? | PASS | FR-013, FR-014. |
| VIII | Spec-driven | Failing tests exist including refusal paths? | PASS | All SC and acceptance scenarios require tests first. |

---

## 2. Architecture Overview



─────────────────────────────┐
│   Next.js 15 Frontend       │
│   (Athlete + Coach views)   │
└──────────────┬──────────────┘
│
┌──────────────▼──────────────┐
│   FastAPI Backend           │
│   - Auth (JWT)              │
│   - Orchestrator            │
│   - Risk Engine (pure)      │
│   - Plan Generator          │
│   - Approval Gate           │
│   - Explanation (LLM)       │
└──────────────┬──────────────┘
│
┌──────────────▼──────────────┐
│   PostgreSQL                │
│   - RLS + FORCE             │
│   - Audit triggers          │
│   - Hash-chained log        │
│   - Consent tables          │
└─────────────────────────────┘



### Key Components

1. **Risk Engine** (Python, pure functions)
   - Deterministic only
   - Version-pinned rules
   - Sex-specific factors first-class
   - Confidence calculation
   - No network / no LLM dependency

2. **Orchestrator**
   - Calls Risk Engine
   - Calls Plan Generator (if score available)
   - Calls Explanation service (optional)
   - Writes audit entry before response
   - Enforces approval gate

3. **Audit System** (ADR-0001)
   - Append-only via PostgreSQL triggers
   - Hash chain
   - External chain-head publication (FR-010a)
   - Application role cannot UPDATE/DELETE

4. **Consent & RLS**
   - Purpose-scoped consent records
   - FORCE ROW LEVEL SECURITY
   - Application role is non-owner, no BYPASSRLS

---

## 3. Tech Stack (Prototype)

| Layer              | Choice                          | Reason |
|--------------------|----------------------------------|--------|
| Frontend           | Next.js 15 + TypeScript + Tailwind | Fast, modern, good for demo |
| Backend            | FastAPI (Python)                 | Perfect for deterministic engine + agents |
| Database           | PostgreSQL + RLS + Triggers      | ADR-0001 |
| Auth               | JWT (simple for prototype)       | Enough for demo |
| LLM                | Claude / GPT-4o (explanation only) | Narrative generation |
| Testing            | pytest + mutation testing        | Constitution requirement |
| Deployment         | Local + Railway / Vercel         | Quick demo |

---

## 4. Data Model (High Level)

- Athlete
- ConsentRecord
- HealthMetric (with source, capture_time, ingestion_time, freshness)
- RuleSetVersion
- RiskAssessment (immutable)
- PlanProposal (versioned, state machine)
- ApprovalRecord
- AuditEntry (hash-chained)
- Escalation

---

## 5. Implementation Phases

### Phase 0 – Foundation
- Project structure
- PostgreSQL schema + RLS + triggers
- Basic auth
- Seed data (women athletes)

### Phase 1 – Risk Engine
- Deterministic scoring
- Sex-specific factors
- Freshness + confidence checks
- Full unit + mutation tests

### Phase 2 – Core Flow
- Metric ingestion (manual)
- Risk assessment endpoint
- Plan proposal generation
- Approval gate (tiered)
- Audit writing

### Phase 3 – Safety Hardening
- External chain-head anchoring (FR-010a)
- Concurrent insert protection
- Autonomous audit writes
- Full refusal path tests

### Phase 4 – Frontend + Demo
- Athlete dashboard
- Coach approval view
- Evidence display
- Demo script + 3-min video

---

## 6. Out of Scope for Prototype
- Real wearable integrations
- Mobile app
- Team/squad analytics
- Season periodisation
- Medical diagnosis features

---

## 7. Risks & Mitigations

| Risk | Mitigation |
|------|----------|
| Risk band numbers not clinically validated | Clearly marked as provisional in Assumptions |
| Concurrent audit inserts | Advisory locks or serialisable isolation |
| Audit lost on rollback | Autonomous transaction / separate connection |
| Table owner bypasses RLS | FORCE ROW LEVEL SECURITY + non-owner app role |

## Response snapshot

ADR-0001 moved Proposed → Accepted per the owner's header. Wrote
`specs/001-athlete-health-core/plan.md` against the plan template, keeping the submitted stack,
data model, and scope, and changing three things.

**1. Principle V recorded as PARTIAL, not "PARTIAL → PASS after FR-010a".** The gate asks what is
true now; a forecast is not a gate result. Phases 0–2 produce a system that is tamper-evident
against the application but not against a database operator. Moved to Complexity Tracking with the
sequencing justification (anchoring needs a chain to anchor, so it genuinely cannot precede
Phase 0) and a guardrail: the prototype must not be described as independently auditable until
FR-010a ships.

**2. Gate blocker found under Principle VI: RLS has no subject.** The plan asserted PASS on
"RLS + FORCE ROW LEVEL SECURITY", but a pooled application connection has no inherent notion of
the current athlete, and nothing in the plan propagated caller identity into the database session.
Without it the policies exist, appear enforced, and filter against nothing. Added as an explicit
gate-blocker section: transaction-scoped `SET LOCAL` from a verified JWT claim, never a
client-supplied header, plus a Phase 0 test asserting zero rows when the setting is unset.
Principle VI is PASS *conditional* on this being built.

**3. Phase ordering changed.** Three items moved from Phase 3 to Phase 0 — audit write durability
(ADR-0001 condition 5), serialised chain append (condition 4), and RLS identity propagation. All
three are schema- and call-site-shaped: retrofitting an autonomous audit write after Phase 2
changes every call site that writes one. Refusal-path tests were distributed into the phases that
build each path rather than gathered into "Phase 3 – Safety Hardening", because Principle VIII
requires tests written and failing *before* implementation, and a refusal path built in Phase 1
and tested in Phase 3 is untested code during exactly the window in which demos happen. Phase 3
retains only tests that genuinely depend on Phase 3 artifacts (SC-005a).

Smaller additions: the Risk Engine is a sibling package to the orchestrator so its purity is
enforceable by an automated import-boundary test rather than convention (Principle I erodes by
import creep, not by decision); rule set identity by content hash so "version-pinned" is a fact
rather than a declaration; refusal states specified as first-class UI rather than error toasts —
a withheld score with a stated reason is a product feature under Principle IV; and the risk table
gained blast-radius columns.

**LLM choice flagged as unresolved.** "Claude / GPT-4o" cannot be pinned, and FR-008 requires the
model version in every audit entry. Noted that `gpt-4o` is an older model and a weak default for
new work; if Claude, the current family is Claude 5 (e.g. `claude-sonnet-5`). Stakes are low under
Principle I — the LLM cannot move a score — but the choice must be recorded.

## Outcome

- ✅ Impact: Plan written with an honest Constitution Check — one PARTIAL and two conditional
  PASSes, all justified in Complexity Tracking. One silent consent-bypass gap caught before any
  code exists.
- 🧪 Tests: None run. Test obligations assigned per phase: Phase 0 security tests (RLS bypass,
  audit UPDATE/DELETE, unset identity, concurrent append), Phase 1 mutation + boundary +
  repeatability, Phase 2 approval refusals, Phase 3 rewritten-chain detection.
- 📁 Files: `specs/001-athlete-health-core/plan.md` (new),
  `history/adr/0001-audit-log-storage-mechanism.md` (status → Accepted).
- 🔁 Next prompts: `/sp.tasks`; resolve LLM provider and pin a model ID before Phase 3; re-run the
  Constitution Check after Phase 1 design.
- 🧠 Reflection: The RLS identity gap is the one that would actually have shipped. It fails in the
  most dangerous direction available — the policies are present, the code reviews clean, the
  Constitution Check ticks, and the guarantee is absent. Mechanisms named in a plan are not the
  same as mechanisms wired to a subject.

## Evaluation notes (flywheel)

- Failure modes observed: (a) a gate row recording a future state as its status — "PARTIAL → PASS
  after FR-010a" — which reads as PASS at review time; (b) Principle VI marked PASS on the strength
  of naming RLS, without the identity propagation that gives RLS anything to filter on; (c) safety
  work batched into a late hardening phase, inverting Principle VIII for the phases before it.
- Graders run and results (PASS/FAIL): PASS — all template sections present; PASS — every
  Constitution Check row cites specific FRs rather than asserting; PASS — every violation carries a
  rejected simpler alternative; FAIL then FIXED — Principle V status was a forecast; FAIL then
  FIXED — Principle VI lacked its subject.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): add a rule to the plan template's Constitution Check —
  a status cell must describe the present state only, and any row citing a mechanism must also cite
  the mechanism's subject or trigger. Both of this session's gate failures would have been caught
  at authoring.
