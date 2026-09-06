<!--
SYNC IMPACT REPORT
==================
Version change: TEMPLATE (unversioned) → 1.0.0
Bump rationale: First ratification. The file was an unfilled SpecKit template with zero
defined principles; adopting a complete, binding principle set is an initial baseline
release, not an amendment. MAJOR=1 established at ratification.

Modified principles (template slot → ratified principle):
  - [PRINCIPLE_1_NAME] → I. Guarantee Lives in Code, Never in the Model
  - [PRINCIPLE_2_NAME] → II. Human-in-the-Loop for Irreversible Actions (NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. Women-First by Design
  - [PRINCIPLE_4_NAME] → IV. Fail Closed
  - [PRINCIPLE_5_NAME] → V. Full Auditability
  - [PRINCIPLE_6_NAME] → VI. Privacy and Consent First
  - (new slot)         → VII. Explainability Over Black-Box
  - (new slot)         → VIII. Spec-Driven Development

Added sections:
  - Safety and Compliance Constraints (was [SECTION_2_NAME])
  - Development Workflow and Quality Gates (was [SECTION_3_NAME])
  - Governance (populated: amendment procedure, versioning policy, compliance review)

Removed sections: none (all template slots consumed or expanded)

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check gates made concrete
  ✅ .specify/templates/spec-template.md — added mandatory "Equity Claim" (Principle III)
     and "Safety and Consent Requirements" (Principles II, IV, VI, VII) sections
  ✅ .specify/templates/tasks-template.md — tests changed from OPTIONAL to MANDATORY and
     refusal-path tests required (Principle VIII); resolved a direct conflict
  ✅ .claude/commands/*.md — reviewed; references are generic, no agent-name leakage
  ⚠ README.md / docs/quickstart.md — do not exist yet; must restate Principles I, II, IV
     and the consent model when authored

Deferred TODOs: none. RATIFICATION_DATE set to the date of this adoption (2026-09-06);
no earlier adoption record exists in the repository.
-->

# ShePeak Constitution

## Core Principles

### I. Guarantee Lives in Code, Never in the Model

All safety-critical decisions — injury risk thresholds, recovery prescriptions, training
load limits, and any medical-adjacent output — MUST be computed by deterministic,
version-pinned code and MUST be re-checked at the API boundary before a response is
returned. An LLM MAY explain, summarize, rephrase, or suggest; an LLM MUST NOT be the sole
or final authority for any threshold, limit, or prescription. Model output that contradicts
a deterministic check MUST be discarded, not reconciled.

*Rationale*: Model behavior is non-reproducible across versions and prompts. Athlete safety
cannot depend on an artifact we cannot pin, diff, or test.

### II. Human-in-the-Loop for Irreversible Actions (NON-NEGOTIABLE)

No training plan, recovery protocol, load adjustment, or medical recommendation may be
applied to an athlete without an explicit, recorded approval from an authorized coach or
the athlete themselves. Approval MUST be a distinct, affirmative action — never a default,
a timeout, or an inferred consent. Every approval MUST record actor identity, timestamp,
and the exact artifact version approved.

*Rationale*: Irreversible actions on a human body require an accountable human decision.

### III. Women-First by Design

Every feature MUST state, in its spec, how it improves equity, visibility, or performance
outcomes for women athletes, with at least one measurable acceptance criterion for that
claim. Physiological factors that differ by sex — menstrual cycle phase, hormonal
contraception, bone density and RED-S risk, ACL injury mechanics, iron status, pregnancy
and postpartum status — MUST be modelled explicitly where relevant, never inherited from a
male-default baseline. A feature that cannot state its equity claim MUST NOT ship.

*Rationale*: Sports science defaults to male physiology. Correcting that is the product,
not a nice-to-have.

### IV. Fail Closed

Missing required data, data staler than its declared freshness window, confidence below the
declared threshold, or any policy violation MUST cause the system to withhold the
recommendation and escalate to a human, with a stated reason. Degraded, partial, or
best-guess safety output is forbidden. Silent defaults and implicit fallbacks are
forbidden; every fallback MUST be explicit, tested, and logged.

*Rationale*: The cost of a wrong load prescription exceeds the cost of no prescription.

### V. Full Auditability

Every recommendation, risk score, model invocation, policy decision, and human approval or
rejection MUST be written to an append-only, hash-chained audit log before the result is
returned to the caller. Log entries MUST NOT be mutable or deletable through application
code. Each entry MUST carry the input snapshot reference, the rule and model versions, the
output, and the actor. Chain integrity MUST be verifiable by an independent check.

*Rationale*: Contested outcomes in athlete health require reconstructable history.

### VI. Privacy and Consent First

Athlete health data MUST NOT be read, processed, or used for any purpose without an
explicit, purpose-scoped, revocable consent record. Access control and data residency MUST
be enforced at the database layer (row-level security or equivalent), not only in
application code. Revoking consent MUST stop future processing and MUST be honored within
the declared window. Secrets MUST live in environment configuration, never in source.

*Rationale*: Application-layer-only enforcement fails open the moment a new caller appears.

### VII. Explainability Over Black-Box

Every risk score and recommendation MUST return the exact evidence that produced it: the
input metrics with their values and timestamps, and the rules or model identified by
version. An output that cannot cite its evidence MUST be treated as a Principle IV failure
and withheld. Explanations MUST be generated from the same computation that produced the
score, never reconstructed after the fact.

*Rationale*: A coach cannot accept accountability for a number they cannot interrogate.

### VIII. Spec-Driven Development

No feature is implemented without, in order: a spec with acceptance criteria, a Constitution
Check recorded in the plan, and tests that encode those criteria. Tests MUST be written and
MUST fail before implementation begins. Every safety-critical rule from Principles I, II,
IV, and VII MUST have at least one automated test asserting the closed (refusing) path, not
only the happy path.

*Rationale*: Untested safety guarantees are claims, not guarantees.

## Safety and Compliance Constraints

- **Deterministic safety core**: risk thresholds, load limits, and recovery rules live in a
  single versioned rules module with no network or LLM dependency. Changing a threshold is
  a reviewed code change with a test, never a runtime configuration edit.
- **API boundary re-check**: the boundary re-validates the deterministic verdict before
  serialization. A mismatch between narrative and verdict MUST return an error, not the
  narrative.
- **Not a medical device**: ShePeak provides training guidance, not diagnosis. Any output
  that crosses into diagnosis or treatment MUST fail closed and escalate to a qualified
  human.
- **Data classification**: athlete health data is the highest sensitivity tier. It MUST NOT
  be sent to third-party model providers unless the consent record explicitly covers that
  processor, and it MUST NOT appear in logs, traces, or error messages in raw form.
- **Secrets**: no secret, token, or key in source, fixtures, or Prompt History Records.
  Environment configuration plus documented variable names only.

## Development Workflow and Quality Gates

- **Constitution Check gate**: `/sp.plan` MUST record a pass or fail against all eight
  principles before Phase 0 research, and re-check after Phase 1 design. Any violation goes
  in Complexity Tracking with the rejected simpler alternative, or the plan does not
  proceed.
- **Smallest viable diff**: no unrelated refactors in a feature change. Code references
  (`start:end:path`) accompany review claims about existing code.
- **Test gates**: a change touching the safety core, consent, or the audit log MUST include
  refusal-path tests and audit-chain integrity assertions. Coverage of the happy path alone
  is a blocking review finding.
- **ADR discipline**: decisions that are long-lived, had viable alternatives, and are
  cross-cutting MUST be captured via `/sp.adr`, with the user's consent, before the affected
  code merges.
- **PHR discipline**: every user prompt is recorded verbatim under `history/prompts/` per
  the routing rules, without truncation.
- **Review**: every change states which principles it touches and how compliance was
  verified.

## Governance

This constitution supersedes all other practices, conventions, and agent instructions. Where
a template, command file, or habit conflicts with it, the constitution wins and the
conflicting artifact MUST be corrected.

**Amendment procedure**: amendments are proposed as a change to this file via
`/sp.constitution`, MUST include an updated Sync Impact Report, MUST state the migration
path for any code or spec made non-compliant by the change, and require explicit approval
from the project owner. Weakening a NON-NEGOTIABLE principle additionally requires a written
rationale recorded as an ADR.

**Versioning policy** (semantic):

- **MAJOR**: a principle is removed, or redefined such that previously compliant work
  becomes non-compliant.
- **MINOR**: a principle or mandatory section is added, or guidance is materially expanded.
- **PATCH**: clarification, wording, or typo fixes with no change in obligation.

**Compliance review**: the Constitution Check in every plan is the per-feature review.
`/sp.analyze` treats any constitution conflict as CRITICAL and blocking, resolved by
changing the spec, plan, or tasks and never by reinterpreting the principle. Agent runtime
guidance lives in `CLAUDE.md`; it implements this constitution and MUST NOT contradict it.

**Version**: 1.0.0 | **Ratified**: 2026-09-06 | **Last Amended**: 2026-09-06
