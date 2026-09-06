# Specification Quality Checklist: Core Athlete Health & Performance System

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-06
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Constitution Alignment (ShePeak v1.0.0)

- [x] Principle III — Equity Claim section present with measurable criterion (EQ-001 → SC-001/002)
- [x] Principle III — sex-specific factors enumerated; male-default baseline forbidden (FR-017)
- [x] Principle I — deterministic scoring and boundary re-check stated (FR-001, FR-003)
- [x] Principle II — approval required, approval invalidated on change (FR-004, FR-005)
- [x] Principle IV — refusal paths specified with reasons and escalation (FR-006, FR-007, SA-001)
- [x] Principle V — audit entry written before response; tamper-evident (FR-008, FR-009, FR-010)
- [x] Principle VI — purpose-scoped consent, data-store-layer enforcement (FR-011, FR-012)
- [x] Principle VII — evidence returned with every score (FR-013, FR-014, SA-004)
- [x] Principle VIII — success criteria are test-shaped, refusal paths included (SC-003, SC-004)

## Validation Findings

### Iteration 1 — issues found and fixed

1. **Success criteria were not measurable.** The source input offered "Audit chain integrity
   verifiable independently" — a capability statement, not a metric. Replaced with SC-005, which
   states a detection rate over tamper trials.
2. **No refusal-path coverage criterion.** FR-006 was untestable as written. Added SC-004 tying
   coverage to the SA-001 conditions.
3. **Determinism was asserted but not measured.** Added SC-008 (repeatability trials) so
   Principle I has an observable check.
4. **Cycle-data states were conflated.** "Missing data" hid three clinically distinct cases.
   Split into FR-016 (not recorded / recorded as absent / suppressed by contraception), because
   absent menses is itself a RED-S signal, not an absence of signal.
5. **Scope boundary for medical advice was unstated.** Added FR-020 and SA-005.
6. **No out-of-scope section.** Added, including the permanent exclusion required by Principle II.
7. **Narrative/verdict mismatch was unaddressed.** The constitution requires the boundary to error
   rather than serialise a contradicting narrative. Added FR-003 and US2 scenario 5.
8. **Approval staleness was unaddressed.** An approval could silently carry to a modified plan.
   Added FR-005 and US2 scenario 4.

### Iteration 2 — clarifications resolved

All three markers answered by the project owner on 2026-09-06 and encoded as requirements:

1. **Data ingestion scope** → manual entry only, integration-shaped seams. FR-024, FR-025.
2. **Approval authority** → tiered; coach mandatory at elevated/high risk. FR-021, SC-011,
   US2 scenarios 6–8.
3. **Freshness windows and confidence threshold** → per-metric table plus 0.7 confidence floor.
   FR-022, FR-023, SC-012.

### Iteration 3 — consequences surfaced by the answers

Resolving the three questions exposed three further gaps, all closed in-spec rather than raised
as new clarifications:

1. **Risk bands were referenced but never defined.** FR-021 tiers on "elevated" and "high" with no
   boundaries, leaving the rule untestable. Bands recorded in Assumptions (0–39 low, 40–59
   moderate, 60–79 elevated, 80–100 high), explicitly flagged as provisional engineering defaults
   requiring sports-science validation. The *tiering rule* is fixed; the *numbers* are not.
2. **Unaffiliated athlete at elevated risk was undefined.** The tiered rule requires a coach, but
   an athlete may not have one. Resolved fail-closed: the plan stays inactive and the reason is
   stated. Recorded in Assumptions and US2 scenario 8. Explicitly not resolved by falling back to
   self-approval, which would defeat FR-021.
3. **Freshness is only as trustworthy as its capture time.** With manual entry, capture time is
   asserted by the person entering it, so FR-022's windows are enforced against a claim. FR-024
   separates capture from ingestion time so the distinction is recorded rather than hidden, and
   the limitation is stated in Assumptions.

### Deliberate exceptions

- **"Data-store layer" (FR-011) and "hash-chained" (FR-008) are mechanism, not outcome.** This
  would normally fail the *no implementation details* item. They are retained because Constitution
  Principles V and VI mandate the mechanism itself — application-layer-only enforcement is exactly
  the failure mode Principle VI names. Documented in the spec's Assumptions.

## Notes

- Items marked incomplete require spec updates before `/sp.clarify` or `/sp.plan`.
- **All items pass as of 2026-09-06.** The spec is ready for `/sp.plan`. `/sp.clarify` is not
  needed — the three questions it would have asked were answered directly.
- Carried into planning, not blocking: the risk band boundaries are provisional and need
  sports-science validation before non-prototype use.
- **Audit-log storage decided** in [ADR-0001](../../../history/adr/0001-audit-log-storage-mechanism.md)
  (PostgreSQL + triggers + RLS). Writing it surfaced a gap in FR-010: a hash chain detects an
  altered *entry* but not a *rewritten chain*, so "independently verifiable" did not hold against
  anyone able to write to the store directly. Added FR-010a (external chain-head anchoring) and
  SC-005a. Principle V is only fully met once FR-010a is implemented; the plan's Constitution
  Check must record it as partial until then.
