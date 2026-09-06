---
id: 0003
title: Resolve Spec Clarifications
stage: spec
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: 001-athlete-health-core
branch: 001-athlete-health-core (no git repo; directory naming only)
user: ms5373268@gmail.com
command: /sp.specify (clarification round)
labels: ["spec", "clarification", "approval-authority", "freshness-windows", "fail-closed"]
links:
  spec: specs/001-athlete-health-core/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-athlete-health-core/spec.md
  - specs/001-athlete-health-core/checklists/requirements.md
tests:
  - none run (specification artifact; test obligations defined in SC-011, SC-012)
---

## Prompt

Q1: C
Q2: C
Q3: A

## Response snapshot

Answers applied to `specs/001-athlete-health-core/spec.md`:

- **Q1 = C** (manual entry now, integration-shaped seams) → **FR-024** separates capture time from
  ingestion time so staleness is always measured against capture; **FR-025** restricts sources to
  manual athlete/coach entry in this release while requiring the model to generalise without
  changing risk, refusal, or consent rules.
- **Q2 = C** (tiered approval) → **FR-021**: coach approval mandatory for plans derived from
  elevated or high risk; athlete may self-approve below that. Athlete self-approval of an
  elevated/high plan is refused and the refused attempt is recorded. Added US2 acceptance
  scenarios 6–8 and **SC-011**.
- **Q3 = A** (per-metric windows) → **FR-022** tabulates the windows (training load 48h, sleep 24h,
  soreness 24h, cycle phase 7d, contraception status 90d, iron status 90d); **FR-023** sets the
  0.7 confidence floor and requires the computed confidence in the refusal. **SC-012** obliges a
  test on each side of every window boundary.

SA-001 and SA-002 rewritten to name the concrete values rather than "declared" ones, so the
safety requirements are now self-contained.

Three consequences of the answers were surfaced and closed in-spec rather than raised as new
clarification markers:

1. **Risk bands were referenced but undefined.** FR-021 tiers on "elevated"/"high" with no
   boundaries, which left the rule untestable. Recorded in Assumptions as 0–39 low, 40–59
   moderate, 60–79 elevated, 80–100 high — explicitly flagged as provisional engineering defaults
   needing sports-science validation. The tiering rule is fixed; the numbers are not.
2. **Unaffiliated athlete at elevated risk.** The tiered rule assumes a coach exists. Resolved
   fail-closed per Principle IV: the plan stays inactive and the athlete is told why. Deliberately
   NOT resolved by falling back to self-approval, which would hollow out FR-021. US2 scenario 8.
3. **Manual entry makes capture time a claim, not an observation.** FR-022's windows are enforced
   against an asserted capture time in this release. FR-024 records the distinction rather than
   hiding it; the limitation is stated in Assumptions.

Spec now: 25 functional requirements, 12 success criteria, 22 acceptance scenarios, 0
`[NEEDS CLARIFICATION]` markers. Checklist `requirements.md` updated — all items pass;
`/sp.clarify` is unnecessary since its three questions were answered directly.

## Outcome

- ✅ Impact: Spec 001 is clarification-free and ready for `/sp.plan`. The refusal path (FR-006)
  is now testable, which it was not before — SC-004 could not have been evaluated against
  undeclared thresholds.
- 🧪 Tests: None run. Two new test obligations created: SC-011 (self-approval refused at elevated
  risk) and SC-012 (boundary test on each side of all six freshness windows).
- 📁 Files: `specs/001-athlete-health-core/spec.md` (7 edits),
  `specs/001-athlete-health-core/checklists/requirements.md` (validation iterations 2 and 3).
- 🔁 Next prompts: `/sp.adr audit-log-storage-mechanism` before `/sp.plan`, so Principle V has a
  decided mechanism rather than one invented during planning.
- 🧠 Reflection: Q2's tiered answer was the load-bearing one — it converted human-in-the-loop from
  a checkbox into a real second pair of eyes, but it also introduced the unaffiliated-athlete case
  that the untiered version never had. Every safety tier buys a guarantee and creates an edge.

## Evaluation notes (flywheel)

- Failure modes observed: none in tooling this round. The spec-side failure worth noting is that
  FR-021 was written referencing risk bands that did not exist anywhere in the spec — caught on
  re-validation, not at authoring time.
- Graders run and results (PASS/FAIL): PASS — 0 clarification markers remain; PASS — all mandatory
  sections present and ordered; PASS — every new FR has a matching acceptance scenario or success
  criterion; PASS — thresholds are concrete and boundary-testable.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): when writing a requirement that tiers on a named band
  or threshold, assert in the same edit that the band is defined somewhere in the spec — the
  FR-021 gap would have been caught at authoring rather than review.
