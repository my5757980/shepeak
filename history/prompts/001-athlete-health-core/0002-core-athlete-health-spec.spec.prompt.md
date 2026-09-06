---
id: 0002
title: Core Athlete Health Spec
stage: spec
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: 001-athlete-health-core
branch: 001-athlete-health-core (no git repo; directory naming only)
user: ms5373268@gmail.com
command: /sp.specify
labels: ["spec", "athlete-health", "injury-risk", "consent", "audit", "human-in-the-loop"]
links:
  spec: specs/001-athlete-health-core/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-athlete-health-core/spec.md
  - specs/001-athlete-health-core/checklists/requirements.md
tests:
  - none run (specification artifact; no executable code yet)
---

## Prompt

# ShePeak Spec

**Feature**: Core Athlete Health & Performance System  
**Track**: Prototype  
**Date**: 2026-09-06  
**Status**: Draft → Ready for Constitution Check

## Problem Statement
Women athletes experience higher rates of certain injuries (especially ACL), inconsistent access to specialised coaching, and recovery tools that are largely built on male physiological defaults. Existing solutions rarely model menstrual cycle, hormonal contraception, iron status, or RED-S risk explicitly.

## Solution
ShePeak is a multi-agent system that monitors training load and recovery markers for women athletes, produces deterministic injury-risk scores, generates personalised training/recovery plans, and keeps a human coach in final control of every irreversible action.

## Equity Claim (Principle III – Mandatory)
- **EQ-001**: Improves performance and injury prevention equity for women athletes by explicitly modelling sex-specific factors (menstrual phase, ACL mechanics, iron status, RED-S risk). Measured by: every risk score and plan must include at least one sex-specific factor when data is available (SC-001).
- **EQ-002**: Sex-specific factors modelled: menstrual cycle phase, hormonal contraception status, ACL injury mechanics, iron status, RED-S risk indicators. Male-default baselines are forbidden.

## User Stories

1. As a woman athlete, I want an early injury risk score with clear evidence so I can adjust training before injury occurs.
2. As a coach, I want AI-proposed weekly plans that respect female physiology and that I must explicitly approve before they become active.
3. As a coach/athlete, I want every recommendation to be fully auditable and reconstructable.
4. As an organisation, I want consent and data access enforced at the database layer.

## Functional Requirements
- FR-001: System MUST compute injury risk score using deterministic rules only.
- FR-002: LLM MAY only generate explanations; it MUST NOT set thresholds or final prescriptions.
- FR-003: Every plan MUST require explicit recorded approval (coach or athlete).
- FR-004: System MUST fail closed on missing/stale data or low confidence.
- FR-005: Every decision MUST be written to hash-chained audit log before response.
- FR-006: Consent MUST be purpose-scoped and enforced via database RLS.

## Safety & Consent Requirements (Mandatory)
- SA-001: Refusal path — missing/stale data → withhold + escalate with reason.
- SA-002: Approval — no plan applied without explicit recorded approval.
- SA-003: Consent — health data processing requires purpose-scoped consent record (DB layer).
- SA-004: Evidence — every score returns exact metrics + rule versions.

## Success Criteria
- SC-001: 100% of risk scores include sex-specific factor citation when data present.
- SC-002: 0 irreversible actions can be applied without human approval (proven by tests).
- SC-003: Audit chain integrity verifiable independently.
- SC-004: All refusal paths covered by automated tests.

## Response snapshot

Created feature `001-athlete-health-core` via
`.specify/scripts/powershell/create-new-feature.ps1 -Json -Number 1 -ShortName "athlete-health-core"`.
The repo is not a git repository, so the script skipped branch creation and used directory
naming only (it exited 128 from its internal `git rev-parse` but its fallback path completed
correctly and emitted valid JSON).

Wrote `specs/001-athlete-health-core/spec.md`: four prioritised, independently testable user
stories (P1 evidenced risk score → P2 coach approval → P3 auditability → P3 consent), 19
acceptance scenarios, 9 edge cases, 20 functional requirements, the mandatory Equity Claim and
Safety & Consent sections, 9 key entities, 10 measurable success criteria, Assumptions, and
Out of Scope.

Requirements added beyond the source input, each traced to a constitution principle:

- **FR-003** — boundary re-check must ERROR when narrative contradicts the deterministic verdict
  (Principle I). The source input covered "LLM may only explain" but not what happens when the
  explanation disagrees.
- **FR-005** — an approval is invalidated when the approved artifact changes; re-approval
  required (Principle II). Without this, approval silently carries to a modified plan.
- **FR-016** — "not recorded" / "recorded as absent" / "suppressed by contraception" are three
  distinct cycle states. Collapsing them is a clinical error: absent menses is a RED-S signal,
  not missing data.
- **FR-019** — a superseded score is retained when late-arriving data forces recomputation.
- **FR-020 / SA-005** — output that would constitute diagnosis or treatment is refused and
  escalated.

Success criteria were rewritten to be measurable: the source's "Audit chain integrity verifiable
independently" became SC-005 (detection rate over tamper trials), and SC-008 was added so
Principle I's determinism claim has an observable repeatability check.

Also wrote `specs/001-athlete-health-core/checklists/requirements.md` with the validation run.
All Content Quality, Feature Readiness, and Constitution Alignment items pass. One item fails:
three `[NEEDS CLARIFICATION]` markers remain, presented to the user as Q1–Q3 (data ingestion
scope; approval authority; freshness windows and confidence threshold). Each was retained rather
than defaulted because each changes what gets built or what "safe" means.

One deliberate exception to "no implementation details" is documented: FR-008's "hash-chained"
and FR-011's "data-store layer" are mechanism, retained because Constitution Principles V and VI
mandate the mechanism itself, not merely the outcome.

## Outcome

- ✅ Impact: Feature 001 specified and validated against ShePeak Constitution v1.0.0; ready for
  `/sp.clarify` once Q1–Q3 are answered.
- 🧪 Tests: None run — specification artifact. The spec defines the test obligations
  (SC-003, SC-004, SC-005, SC-008) that Principle VIII will enforce at `/sp.tasks`.
- 📁 Files: `specs/001-athlete-health-core/spec.md`,
  `specs/001-athlete-health-core/checklists/requirements.md`.
- 🔁 Next prompts: answer Q1–Q3, then `/sp.plan`. An ADR for audit-log storage (Principle V)
  is still outstanding from the constitution session.
- 🧠 Reflection: The riskiest gap is not in the spec but in the sequencing — FR-011 (data-store
  layer enforcement) and FR-008 (hash chain) both constrain the storage engine, and the ADR that
  should decide it has not been written yet. `/sp.plan` will be forced to decide it implicitly
  unless the ADR comes first.

## Evaluation notes (flywheel)

- Failure modes observed: `create-new-feature.ps1` returns exit code 128 in a non-git repo even
  though its no-git fallback succeeds — the nonzero exit is misleading and could abort a stricter
  caller.
- Graders run and results (PASS/FAIL): PASS — all mandatory template sections present in order;
  PASS — every FR is testable; PASS — success criteria measurable and technology-agnostic; PASS —
  all 8 constitution principles have at least one FR; FAIL (expected) — 3 clarification markers
  remain, within the limit of 3.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): write the audit-log storage ADR before `/sp.plan`, so
  the Constitution Check for Principle V has a decided mechanism to gate against rather than
  inventing one during planning.
