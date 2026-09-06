---
id: 0006
title: Task Breakdown Coverage Audit
stage: tasks
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: 001-athlete-health-core
branch: 001-athlete-health-core (no git repo; directory naming only)
user: ms5373268@gmail.com
command: /sp.tasks
labels: ["tasks", "traceability", "coverage-audit", "refusal-paths", "consent", "audit-chain"]
links:
  spec: specs/001-athlete-health-core/spec.md
  ticket: null
  adr: history/adr/0001-audit-log-storage-mechanism.md
  pr: null
files:
  - specs/001-athlete-health-core/tasks.md
tests:
  - none run (task planning artifact; 20 test tasks defined across 4 phases)
---

## Prompt

/sp.Tasks — 001-athlete-health-core

**Feature**: Core Athlete Health & Performance System  
**Track**: Prototype  
**Date**: 2026-09-06  
**Plan**: [plan.md](./plan.md)  
**Spec**: [spec.md](./spec.md)

---

## Phase 0 – Foundation (Must be solid)

### Database & Security
- [ ] T0.1 Create PostgreSQL schema (Athlete, ConsentRecord, HealthMetric, RuleSetVersion, RiskAssessment, PlanProposal, ApprovalRecord, AuditEntry, Escalation)
- [ ] T0.2 Implement FORCE ROW LEVEL SECURITY on all health-related tables
- [ ] T0.3 Create non-owner application role (no BYPASSRLS, no table ownership)
- [ ] T0.4 Implement transaction-scoped identity propagation (SET LOCAL from verified JWT claim)
- [ ] T0.5 Write test: health data read with identity unset → returns zero rows
- [ ] T0.6 Implement append-only audit triggers + hash chaining
- [ ] T0.7 Serialise concurrent audit inserts (advisory lock or equivalent)
- [ ] T0.8 Make audit writes autonomous (survive caller rollback)
- [ ] T0.9 Seed realistic women athlete data + consent records

### Project Setup
- [ ] T0.10 Monorepo structure (frontend + backend)
- [ ] T0.11 Basic JWT auth
- [ ] T0.12 Import boundary test for Risk Engine (must stay pure)

---

## Phase 1 – Risk Engine (Deterministic Core)

- [ ] T1.1 Implement versioned Rule Set (content-hash based identity)
- [ ] T1.2 Implement sex-specific factors (cycle phase, contraception, iron, RED-S, ACL mechanics)
- [ ] T1.3 Implement freshness window checks (FR-022)
- [ ] T1.4 Implement confidence calculation + 0.7 threshold (FR-023)
- [ ] T1.5 Implement risk bands (provisional: 0-39 low, 40-59 moderate, 60-79 elevated, 80-100 high)
- [ ] T1.6 Full unit tests for every rule
- [ ] T1.7 Mutation tests for all safety rules (must fail when rule is removed)
- [ ] T1.8 Refusal path tests (missing / stale / low confidence)

---

## Phase 2 – Core Flow

- [ ] T2.1 Manual metric ingestion endpoint (with capture vs ingestion time)
- [ ] T2.2 Risk Assessment endpoint (calls pure Risk Engine)
- [ ] T2.3 Boundary re-check (narrative vs verdict mismatch → error)
- [ ] T2.4 Plan Proposal generation
- [ ] T2.5 Tiered Approval Gate (FR-021)
- [ ] T2.6 Audit entry written before every response
- [ ] T2.7 Escalation on refusal

---

## Phase 3 – Safety Hardening

- [ ] T3.1 External chain-head anchoring (FR-010a)
- [ ] T3.2 Independent integrity check endpoint
- [ ] T3.3 Full end-to-end refusal path tests
- [ ] T3.4 Concurrent load tests on audit chain
- [ ] T3.5 Pin exact LLM model version for explanations

---

## Phase 4 – Frontend + Demo

- [ ] T4.1 Athlete Dashboard (score + evidence + refusal states as first-class UI)
- [ ] T4.2 Coach Approval View
- [ ] T4.3 Plan Proposal review + approve/reject
- [ ] T4.4 Seed demo data + happy path + refusal path scenarios
- [ ] T4.5 3-minute demo video script
- [ ] T4.6 Pitch deck (max 5 slides)

---

## Definition of Done (for every task)
- Tests written first and failing
- Refusal paths covered
- Constitution principles touched are stated in the PR/commit
- Audit entry created where required

## Response snapshot

Wrote `specs/001-athlete-health-core/tasks.md`. Ran a mechanical coverage audit first — extracted
all 26 FR, 5 SA and 13 SC identifiers from the spec and matched each against the submitted task
list. **18 requirements had no task.** The submitted list covered the spine correctly; what it
missed was mostly the requirements added after the first spec draft.

Uncovered, now added:

- **FR-012 consent withdrawal** (T2.14, T2.16) — the largest gap. An entire user story (US4) had
  consent enforcement but no way to *grant or withdraw* consent, so SC-010 was unreachable.
- **FR-014 / FR-002 explanation service** (T3.6, T3.8) — no task built the LLM narrative at all,
  yet T2.3 re-checks narrative against verdict. The thing being re-checked did not exist.
- **FR-005 approval invalidation** (T2.9) — approval silently surviving artifact modification.
- **FR-020 / SA-005 diagnosis refusal** (T2.13) — entirely absent.
- **FR-018 log scrubbing** (T2.15), **FR-019 superseded scores** (T2.8), **FR-016 three cycle
  states** (T1.9), **FR-017 no male-default substitution** (T1.14), **FR-009 audit
  UPDATE/DELETE** (T0.15).
- Test-only gaps: SC-001, SC-002, SC-005, SC-005a, SC-006, SC-007, SC-008, SC-009, SC-012.

Final coverage: **26/26 FR, 5/5 SA, 13/13 SC**, with a traceability table in the file.

Ordering corrections:

- **T3.5 (pin LLM model ID) moved before T3.6 (build explanation service).** The submitted order
  had it last in Phase 3. FR-008 requires the model version in every audit entry, so an unpinned
  provider blocks the explanation service — the dependency runs the other way.
- **T3.3 rescoped** from "full end-to-end refusal path tests" to integration-only, with per-path
  refusal tests living in T1.8 and T2.10–T2.12. Same correction as the plan review: batching
  refusal tests late inverts Principle VIII for every phase before them.
- **T0.9 seed data given two specific requirements** — an athlete with no assigned coach, and one
  with contraception-suppressed cycle data — because T2.12 and T1.9 cannot be tested without them.
  Seed data is a test fixture here, not decoration.

Also noted: **Phases 0 and 1 are parallelisable.** The Risk Engine touches no database, so two
people can work simultaneously. This is the only meaningful schedule compression available, and it
falls out of the purity constraint the constitution already imposes.

Flagged **T4.9 (SC-009 athlete comprehension, 90% unaided)** as the only success criterion no
automated test can satisfy — it needs real people, so it needs recruiting lead time and should be
scheduled early despite sitting in the last phase.

Flagged that the repository is **not a git repository**, so the Definition of Done's "stated in the
PR/commit" has nowhere to land. Recommended `git init` before Phase 0.

## Outcome

- ✅ Impact: Task list expanded from 33 to 62 tasks with full requirement traceability. Two
  unbuildable dependencies caught (explanation service missing; model pinning ordered after the
  service that needs it).
- 🧪 Tests: None run. 20 test tasks defined and assigned to the phase that builds the behavior
  they guard, per Principle VIII.
- 📁 Files: `specs/001-athlete-health-core/tasks.md` (new).
- 🔁 Next prompts: `git init`; `/sp.analyze` for a cross-artifact consistency pass before
  `/sp.implement`; decide T0.8's rollback semantics, which is a design decision disguised as a task.
- 🧠 Reflection: The coverage gaps clustered exactly where requirements were added *after* the
  first draft — FR-005, FR-010a, FR-016 through FR-020 were all late additions, and all but one
  were missed. Late requirements are the ones task lists forget, because the list is usually
  written from the mental model of the first draft rather than re-derived from the current spec.

## Evaluation notes (flywheel)

- Failure modes observed: (a) 18 of 44 requirements had no task, concentrated in late-added
  requirements; (b) a task depended on an artifact no task created (T2.3 re-checks a narrative;
  nothing built the narrative); (c) T3.5 ordered after the task it blocks; (d) refusal tests
  re-batched into a hardening phase, repeating the phase-ordering error already corrected in
  plan.md — the same mistake recurred one artifact later.
- Graders run and results (PASS/FAIL): PASS — every FR/SA/SC now maps to at least one task;
  PASS — every test task precedes or accompanies the implementation it guards; PASS — critical
  path and parallel opportunities stated; FAIL then FIXED — 18 uncovered requirements;
  FAIL then FIXED — explanation service absent; FAIL then FIXED — T3.5/T3.6 inversion.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): make the requirement-coverage table a *required*
  section of the tasks template, generated by extracting IDs from the spec rather than written by
  hand. The audit that found 18 gaps was three grep commands; it should not depend on remembering
  to run them.
