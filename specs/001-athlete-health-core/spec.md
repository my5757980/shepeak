# Feature Specification: Core Athlete Health & Performance System

**Feature Branch**: `001-athlete-health-core`
**Created**: 2026-09-06
**Status**: Draft — clarifications resolved, ready for Constitution Check
**Input**: User description: "ShePeak Core Athlete Health & Performance System — a system that monitors training load and recovery markers for women athletes, produces deterministic injury-risk scores, generates personalised training/recovery plans, and keeps a human coach in final control of every irreversible action."

## Problem Statement

Women athletes face higher rates of certain injuries — ACL rupture most prominently — alongside
inconsistent access to specialised coaching. The recovery and load-management tools available to
them are largely calibrated on male physiological defaults, and rarely model menstrual cycle
phase, hormonal contraception, iron status, or RED-S risk at all. The result is guidance that is
either generic or silently wrong for the athlete receiving it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Athlete receives an evidenced injury risk score (Priority: P1)

A woman athlete opens her dashboard and sees a current injury risk score. Beside the score she
sees exactly which of her metrics produced it — her recent training load trend, her sleep and
soreness markers, and at least one sex-specific factor such as her current menstrual cycle phase
— each with its recorded value and when it was captured. She can see which rule fired and adjust
her next session before an injury occurs. When her data is incomplete or out of date, she sees a
clear statement that no score can be produced and what is missing, never a guessed number.

**Why this priority**: This is the smallest slice that delivers the product's core value. It
proves the deterministic scoring engine, the evidence trail, and the refusal path — the three
things everything else depends on. Shipped alone, an athlete gains early warning she does not
have today.

**Independent Test**: Load an athlete with a complete metric history, request a risk score, and
verify the returned score cites its input metrics with timestamps, its rule version, and at
least one sex-specific factor. Then remove or age one required metric and verify the system
refuses with a named reason instead of scoring.

**Acceptance Scenarios**:

1. **Given** an athlete with complete, fresh metrics including cycle phase, **When** a risk score
   is requested, **Then** the system returns a score, the contributing metrics with values and
   capture timestamps, the identifier and version of each rule that fired, and at least one
   sex-specific factor.
2. **Given** an athlete whose soreness data is older than its freshness window, **When** a risk
   score is requested, **Then** the system returns no score, states which input was stale and how
   stale, and escalates to the athlete's coach.
3. **Given** an athlete who has not recorded cycle-phase data, **When** a risk score is requested,
   **Then** the system either produces a score explicitly flagged as excluding sex-specific
   factors, or refuses — and never substitutes a male-default baseline.
4. **Given** any risk score request, **When** it completes or refuses, **Then** an audit entry
   recording the inputs, outcome, and rule versions exists before the response reaches the caller.

---

### User Story 2 - Coach approves a proposed plan before it becomes active (Priority: P2)

A coach reviews a weekly training and recovery plan the system has proposed for an athlete. The
proposal is visibly marked as inactive. The coach can see the reasoning, the physiological
factors it accounts for, and the risk assessment it was derived from. Nothing takes effect until
the coach explicitly approves it. The coach may reject it, or approve it, and either way the
decision is recorded against their identity and the exact version of the plan they saw.

**Why this priority**: This is the guarantee that makes the product safe to put in front of real
athletes. It depends on Story 1's risk assessment existing, so it follows it.

**Independent Test**: Generate a plan proposal, attempt to activate it through every available
path without an approval record, and verify all attempts are refused. Then approve it and verify
it activates and that the approval record names the approver, the timestamp, and the plan version.
Separately, attempt athlete self-approval on an elevated-risk plan and verify it is refused.

**Acceptance Scenarios**:

1. **Given** a newly generated plan proposal, **When** it is created, **Then** its state is
   "proposed" and it has no effect on the athlete's active plan.
2. **Given** a proposed plan with no approval record, **When** activation is attempted by any
   caller, **Then** the system refuses and records the refused attempt.
3. **Given** an authorised approver, **When** they approve a specific plan version, **Then** the
   plan activates and an approval record captures approver identity, timestamp, and plan version.
4. **Given** an approved plan, **When** the underlying proposal is subsequently modified, **Then**
   the approval does not carry over to the modified version and re-approval is required.
5. **Given** a plan proposal, **When** its narrative explanation contradicts the deterministic
   risk verdict it cites, **Then** the system returns an error and does not present the proposal.
6. **Given** a plan derived from an elevated or high risk assessment, **When** the athlete
   attempts to approve it herself, **Then** the system refuses, records the refused attempt, and
   states that coach approval is required.
7. **Given** a plan derived from a low or moderate risk assessment, **When** the athlete approves
   it, **Then** it activates and the approval record names her as the approver.
8. **Given** an athlete with no assigned coach and a plan derived from an elevated risk
   assessment, **When** activation is attempted by any party, **Then** the plan remains inactive
   and the reason given is the absence of an authorised coach approver.

---

### User Story 3 - Any decision can be reconstructed after the fact (Priority: P3)

A coach and athlete disagree about why a session was flagged as high risk three weeks ago. Either
of them can retrieve the decision, see the exact inputs as they stood at the time, the rule
versions in force, the output produced, and every human decision taken on it. An independent
reviewer can verify that the record has not been altered since it was written.

**Why this priority**: Required by the constitution and essential for coach accountability, but
the system delivers athlete value before this is queryable by end users.

**Independent Test**: Produce a series of decisions, run an independent integrity check over the
audit chain, and confirm it passes. Then attempt to alter or delete a historical entry through
every application path and confirm all attempts fail and the integrity check would detect a
direct alteration.

**Acceptance Scenarios**:

1. **Given** a completed risk assessment, **When** it is retrieved from the audit record, **Then**
   the inputs as they stood, rule versions, output, and actor are all present.
2. **Given** any audit entry, **When** modification or deletion is attempted through the
   application, **Then** the attempt fails and is itself recorded.
3. **Given** a stored audit chain, **When** an independent integrity check runs, **Then** it
   confirms the chain is unbroken, and detects any entry altered out of band.

---

### User Story 4 - Health data is only reachable with consent (Priority: P3)

An organisation administrator can demonstrate that every access to athlete health data was
covered by a consent record scoped to that purpose. An athlete can withdraw consent for a given
purpose and see processing for that purpose stop. Access controls are enforced by the data store
itself, so a new or misconfigured caller cannot read data the consent record does not cover.

**Why this priority**: Non-negotiable for production, but the guarantee can be demonstrated on
the prototype's data set once the earlier stories exist to exercise it.

**Independent Test**: Attempt to read an athlete's health data as a caller with no covering
consent record, directly against the data store rather than through the application, and confirm
the read returns nothing. Withdraw a consent and confirm the corresponding processing stops.

**Acceptance Scenarios**:

1. **Given** a caller with no consent record covering a purpose, **When** they attempt to read
   health data for that purpose — including by bypassing application code — **Then** no data is
   returned.
2. **Given** an athlete who withdraws consent for a purpose, **When** processing for that purpose
   is next attempted, **Then** it is refused and the athlete's data is not read.
3. **Given** any access to health data, **When** it occurs, **Then** the consent record relied
   upon is identifiable from the audit trail.

---

### Edge Cases

- **Partial sex-specific data**: athlete tracks cycle phase but uses hormonal contraception that
  suppresses it. The system must treat this as a distinct modelled state, not as missing data and
  not as a normal cycling athlete.
- **Irregular or absent cycle**: absence may itself be a RED-S risk indicator rather than missing
  data. The system must distinguish "not recorded" from "recorded as absent".
- **Metric arrives late**: a wearable syncs yesterday's data today. Does a score computed in the
  interim get superseded, and is the superseded score retained in the audit trail? It must be.
- **Conflicting metrics**: self-reported soreness contradicts load data. Deterministic rules must
  resolve this explicitly rather than averaging.
- **Athlete withdraws consent mid-plan**: an active approved plan exists. Processing stops, but
  the historical audit record is retained — audit retention and consent withdrawal must not
  conflict.
- **Coach loses authorisation** while a proposal awaits their approval.
- **Explanation service unavailable**: the deterministic score exists but no narrative can be
  generated. The score and its evidence must still be deliverable.
- **Clock skew / backdated entries** in the audit chain.
- **First-time athlete** with no history at all — no baseline to compare load against.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute every injury risk score from deterministic, version-pinned
  rules. The same inputs and rule version MUST always yield the same score.
- **FR-002**: System MUST confine language-model output to explanation and narrative. A language
  model MUST NOT set, adjust, or override any threshold, limit, score, or final prescription.
- **FR-003**: System MUST re-verify the deterministic verdict at the response boundary and MUST
  return an error rather than the response if narrative and verdict disagree.
- **FR-004**: System MUST hold every generated plan in a proposed, inactive state until an
  explicit approval record exists naming an authorised approver, a timestamp, and the exact plan
  version approved. Who counts as authorised is determined by FR-021.
- **FR-005**: System MUST invalidate an existing approval when the approved artifact changes, and
  MUST require re-approval.
- **FR-006**: System MUST withhold output and escalate, with a machine-readable reason, when a
  required input is missing, is older than its freshness window as declared in FR-022, or when
  confidence is below the threshold declared in FR-023.
- **FR-007**: System MUST NOT emit partial, degraded, or best-guess safety output. Every fallback
  path MUST be explicit and recorded.
- **FR-008**: System MUST write an entry to an append-only, hash-chained audit record — covering
  the input snapshot reference, rule and model versions, output, and actor — before returning any
  recommendation, score, refusal, or approval outcome to the caller.
- **FR-009**: System MUST prevent modification and deletion of audit entries through application
  paths, and MUST record attempts.
- **FR-010**: System MUST allow an independent party to verify audit chain integrity without
  trusting the application.
- **FR-010a**: System MUST publish the audit chain head — its current hash and entry count — to a
  location outside the audit data store, on a fixed interval, so that a wholesale rewrite of the
  chain is detectable and not merely an alteration of one entry. (Added by ADR-0001; without this,
  a party who can write to the store directly can rewrite history into a chain that verifies
  cleanly.)
- **FR-011**: System MUST gate all health data access on a purpose-scoped, revocable consent
  record, enforced at the data-store layer so that enforcement does not depend on application
  code being correct.
- **FR-012**: System MUST stop processing for a purpose once consent for that purpose is withdrawn,
  within the declared window, while retaining prior audit entries.
- **FR-013**: System MUST return, with every risk score, the contributing input metrics with their
  values and capture timestamps, and the identifier and version of each rule that fired.
- **FR-014**: System MUST generate explanations from the same computation that produced the score,
  never reconstructed after the fact.
- **FR-015**: System MUST model menstrual cycle phase, hormonal contraception status, iron status,
  RED-S risk indicators, and ACL-specific injury mechanics as explicit, distinguishable inputs.
- **FR-016**: System MUST distinguish "not recorded", "recorded as absent", and "suppressed by
  contraception" as separate states for cycle data, and MUST NOT collapse them into one.
- **FR-017**: System MUST NOT substitute a male-default baseline for a missing sex-specific input;
  the input is either present, or its absence is stated in the output.
- **FR-018**: System MUST exclude raw health data from logs, traces, and error messages.
- **FR-019**: System MUST retain a superseded score in the audit record when late-arriving data
  causes recomputation.
- **FR-020**: System MUST refuse and escalate any request whose output would constitute a medical
  diagnosis or treatment recommendation.
- **FR-021**: System MUST require approval from the athlete's assigned coach for any plan derived
  from a risk assessment in the **elevated** or **high** band. Below that, the athlete MAY approve
  her own plan. An athlete's self-approval of an elevated or high-risk plan MUST be refused and
  recorded as a refused attempt.
- **FR-022**: System MUST treat each metric as stale past its freshness window, measured from
  capture time, and MUST apply these declared windows:

  | Metric | Freshness window |
  |---|---|
  | Training load | 48 hours |
  | Sleep | 24 hours |
  | Soreness / subjective wellness | 24 hours |
  | Menstrual cycle phase | 7 days |
  | Hormonal contraception status | 90 days |
  | Iron status | 90 days |

- **FR-023**: System MUST withhold a risk score when assessment confidence is below **0.7**, and
  MUST state the computed confidence in the refusal.
- **FR-024**: System MUST record, for every metric, the source it came from and its capture
  timestamp as distinct from its ingestion timestamp, so that a metric ingested later than it was
  captured is evaluated for staleness against capture time.
- **FR-025**: System MUST accept metrics only from manual athlete or coach entry in this release,
  while modelling source and capture/ingestion times generally enough that an automated source can
  be added without changing the risk, refusal, or consent rules.

- **FR-026**: System MUST model cricket bowling workload — overs bowled, spell density, and
  consecutive playing days — as a first-class training-load input, while keeping the rule
  structure sport-agnostic so a further sport can be added without changing the risk, refusal, or
  consent rules.
- **FR-027**: Athlete- and coach-facing surfaces MUST meet WCAG 2.2 Level AA. A refusal, its
  stated reason, and the evidence behind a score MUST all be reachable and comprehensible by
  screen reader and keyboard alone.
- **FR-028**: Athlete-facing content MUST be available in at least two languages, and the
  translation MUST cover refusal reasons and score evidence — not only navigation and labels. A
  reason an athlete cannot read is a refusal without an explanation, which fails Principle VII.

### Equity Claim *(mandatory — Constitution Principle III)*

- **EQ-001**: This feature improves injury-prevention and performance equity for women athletes by
  modelling sex-specific physiology explicitly rather than inheriting a male-default baseline,
  measured by SC-001 and SC-002.
- **EQ-002**: Sex-specific physiological factors modelled explicitly: menstrual cycle phase,
  hormonal contraception status, iron status, RED-S risk indicators, and ACL injury mechanics.
  Male-default baselines are forbidden (FR-017).

### Safety and Consent Requirements *(mandatory)*

- **SA-001**: Refusal path — when a required input is missing, stale beyond the windows in FR-022,
  or confidence is below 0.7, the system MUST withhold the output and escalate to the athlete's
  coach with a machine-readable reason. (Principle IV → FR-006, FR-007, FR-022, FR-023)
- **SA-002**: Approval — no training or recovery plan applies without an explicit recorded
  approval from an authorised approver. Coach approval is mandatory at elevated and high risk;
  athlete self-approval is permitted only below that band. (Principle II → FR-004, FR-005, FR-021)
- **SA-003**: Consent — processing any athlete health metric requires a purpose-scoped consent
  record covering that purpose, enforced at the data-store layer. (Principle VI → FR-011, FR-012)
- **SA-004**: Evidence — every score cites its input metrics with values and timestamps plus rule
  identifiers and versions. (Principle VII → FR-013, FR-014)
- **SA-005**: Scope boundary — output that would constitute diagnosis or treatment is refused and
  escalated to a qualified human. (Constitution: Safety and Compliance Constraints → FR-020)

### Key Entities

- **Athlete**: the person being monitored. Holds identity, sport, and the consent records that
  govern her data. Related to all metrics, assessments, and plans.
- **Consent Record**: an athlete's grant for a named purpose, with grant and withdrawal
  timestamps. Revocable. Governs whether any read of health data may occur.
- **Health Metric**: a single captured measurement — training load, sleep, soreness, cycle phase,
  contraception status, iron marker — with its value, capture timestamp, and source. Carries a
  freshness window defining when it becomes stale.
- **Rule Set Version**: the pinned set of deterministic rules and thresholds in force. Every
  assessment names the version that produced it.
- **Risk Assessment**: a score, or a refusal, produced at a point in time. Holds the contributing
  metric snapshot, the rules that fired, the sex-specific factors considered, and a confidence
  level. Immutable once written; may be superseded but never replaced.
- **Plan Proposal**: a generated training and recovery plan, versioned, in state proposed,
  approved, rejected, or superseded. References the risk assessment it derives from.
- **Approval Record**: an authorised approver's explicit decision on a specific plan version,
  with actor identity and timestamp. Cannot be inferred or defaulted.
- **Audit Entry**: an append-only, hash-chained record of one decision — input snapshot reference,
  rule and model versions, output, actor, and prior-entry hash.
- **Escalation**: a raised refusal, naming the reason, the missing or stale input, and the human
  it was routed to.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of risk scores produced for athletes with sex-specific data present cite at
  least one sex-specific factor in their evidence.
- **SC-002**: 0% of risk scores substitute a default value for a missing sex-specific input;
  every such absence is stated in the output.
- **SC-003**: 0 plans can be made active without a matching approval record, demonstrated by
  automated tests covering every activation path.
- **SC-004**: 100% of refusal conditions named in SA-001 are covered by automated tests that
  assert the refusal, the stated reason, and the escalation.
- **SC-005**: An independent integrity check over the full audit chain passes, and detects a
  deliberately altered entry in 100% of tamper trials.
- **SC-005a**: A chain rewritten wholesale — internally consistent, but diverging from a
  previously published chain head — is detected in 100% of trials.
- **SC-006**: 0 successful reads of athlete health data by a caller without a covering consent
  record, including attempts that bypass application code.
- **SC-007**: 100% of risk scores return their contributing metrics with capture timestamps and
  the versions of the rules that fired.
- **SC-008**: Identical inputs and rule version reproduce an identical score in 100% of
  repeatability trials.
- **SC-009**: An athlete can understand why she was flagged — 90% of athletes shown a score and
  its evidence can correctly identify the top contributing factor without assistance.
- **SC-010**: Withdrawal of consent stops processing for that purpose within the declared window
  in 100% of trials.
- **SC-011**: 0 plans derived from an elevated or high risk assessment are activated on athlete
  self-approval, demonstrated by automated tests attempting exactly that.
- **SC-012**: 100% of the freshness windows in FR-022 have an automated test asserting refusal one
  interval past the window and a score one interval inside it.
- **SC-013**: An automated accessibility audit of athlete- and coach-facing surfaces reports 0
  WCAG 2.2 AA violations, and a score, its evidence, and a refusal reason are each completable by
  keyboard and screen reader alone.
- **SC-014**: 100% of refusal reasons and evidence labels render in both supported languages, with
  no untranslated fallback text.

## Assumptions

- **Prototype scope**: this is the Prototype track. Volume, concurrency, and latency targets are
  not yet constrained; the guarantees above are correctness guarantees, not throughput ones.
- **Escalation target**: refusals escalate to the athlete's assigned coach by default. Where no
  coach is assigned, the refusal surfaces to the athlete herself with the same stated reason.
- **Unaffiliated athlete at elevated risk**: FR-021 requires a coach for elevated and high-risk
  plans. An athlete with no assigned coach therefore cannot activate such a plan at all — the
  proposal stays inactive and she is told why. This is the fail-closed outcome (Principle IV);
  it is not treated as grounds to fall back to self-approval.
- **Risk bands**: score is expressed 0–100 — low 0–39, moderate 40–59, elevated 60–79, high
  80–100. The *tiering rule* in FR-021 is fixed; these boundary values are provisional engineering
  defaults and require sports-science validation before any non-prototype use. They are stated
  here so the rule is testable now.
- **Self-reported freshness**: with manual entry only (FR-025), capture time is asserted by the
  person entering the metric. FR-022's windows are therefore enforced against a claimed capture
  time in this release; an automated source would make that claim verifiable.
- **Explanation is optional to the guarantee**: if narrative generation is unavailable, the score
  and its structured evidence are still delivered (FR-014 constrains how an explanation is made,
  not whether one must exist).
- **Consent granularity**: consent is scoped by purpose (e.g. "injury risk scoring", "plan
  generation"), not per individual metric, unless clarification below says otherwise.
- **Audit retention outlives consent withdrawal**: withdrawal stops future processing; it does not
  erase historical audit entries, which are required for accountability. Any erasure right is
  handled as a separate, out-of-scope process.
- **Data-store-layer enforcement**: FR-011's "data-store layer" and FR-008's "hash-chained" are
  stated in the requirements because Constitution Principles V and VI mandate the mechanism, not
  merely the outcome. This is a deliberate, constitution-sourced exception to keeping mechanism
  out of the spec.
- **Not a medical device**: ShePeak provides training guidance. Diagnosis and treatment are out of
  scope and are refused (FR-020).

## Out of Scope

- Diagnosis, treatment, or medication guidance of any kind.
- Nutrition planning beyond iron-status risk flagging.
- Team-wide or squad-level aggregate analytics.
- Competition scheduling and periodisation across a full season.
- Athlete-to-athlete social or comparison features.
- Any automatic application of a plan without human approval — permanently out of scope by
  Constitution Principle II.

## Resolved Clarifications

Answered by the project owner on 2026-09-06.

- **Data ingestion scope** → Manual athlete and coach entry only for this release, with the data
  model shaped so an automated source can be added without changing the risk, refusal, or consent
  rules. Encoded as FR-024 and FR-025. Third-party processor consent coverage is therefore not
  exercised in this release, but the consent record's purpose scoping already accommodates it.
- **Approval authority** → Tiered. Coach approval is mandatory for plans derived from elevated or
  high risk; the athlete may self-approve below that band. Encoded as FR-021 and SC-011.
- **Freshness windows and confidence threshold** → Per-metric windows as tabulated in FR-022;
  refuse below 0.7 confidence per FR-023. Encoded with test obligations in SC-012.
