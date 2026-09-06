---
id: 0004
title: Audit Log Storage ADR
stage: plan
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: 001-athlete-health-core
branch: 001-athlete-health-core (no git repo; directory naming only)
user: ms5373268@gmail.com
command: /sp.adr audit-log-storage-mechanism
labels: ["adr", "audit-log", "postgresql", "row-level-security", "tamper-evidence", "principle-v"]
links:
  spec: specs/001-athlete-health-core/spec.md
  ticket: null
  adr: history/adr/0001-audit-log-storage-mechanism.md
  pr: null
files:
  - history/adr/0001-audit-log-storage-mechanism.md
  - specs/001-athlete-health-core/spec.md
  - specs/001-athlete-health-core/checklists/requirements.md
tests:
  - none run (architecture decision record; test obligations added as SC-005a)
---

## Prompt

# ADR: Audit Log Storage Mechanism

**Status**: Proposed  
**Date**: 2026-09-06  
**Deciders**: Project Owner  

## Context
Principle V requires an append-only, hash-chained audit log that is independently verifiable.  
Principle VI requires consent enforcement at the data-store layer (Row-Level Security).  

We need to decide the storage approach for the Prototype track.

## Options Considered

1. **PostgreSQL only** (application-level hash chain + RLS)
2. **PostgreSQL + Triggers** (database enforces append-only + hash)
3. **External immutable ledger** (e.g. separate service or blockchain-style log)

## Decision
**Option 2: PostgreSQL + Database Triggers**

- Use PostgreSQL as the single source of truth.
- Enforce append-only behaviour and hash chaining via database triggers.
- Use Row-Level Security for consent enforcement.
- Application code never updates or deletes audit rows.

## Consequences
- Positive: Single database, strong guarantees, independent verification possible, fits Prototype timeline.
- Negative: Slightly more complex schema and trigger logic.
- Migration path later: Can still extract to external ledger if needed.

## Compliance
- Satisfies Principle V (Full Auditability)
- Satisfies Principle VI (Privacy & Consent First)

## Response snapshot

Recorded the owner's decision as `history/adr/0001-audit-log-storage-mechanism.md` (status
Proposed), following `.specify/templates/adr-template.md`. Option 2 adopted as chosen; the
rejection reasoning for Options 1 and 3 was written out rather than left as a list.

Verified the PostgreSQL semantics this decision rests on via Context7 against the official docs,
rather than asserting them from memory (per CLAUDE.md's authoritative-source mandate):

- Superusers and roles holding `BYPASSRLS` bypass row security entirely.
- A table's owner bypasses that table's own policies **by default**, unless
  `FORCE ROW LEVEL SECURITY` is set.
- Enabling RLS on a table with no policies applies a default-deny.

Those facts turned two assumed guarantees into conditions. The ADR adopts Option 2 subject to five
conditions that are what make it satisfy Principles V and VI rather than appear to:

1. `FORCE ROW LEVEL SECURITY` on every health-data table — otherwise RLS protects everyone except
   the role most likely to be connected during development.
2. The application role is neither table owner, nor `BYPASSRLS`, nor superuser.
3. The chain head is anchored outside the database on a fixed interval.
4. Chain appends are serialised — concurrent inserts reading the same predecessor hash fork the
   chain; transaction isolation alone does not prevent this.
5. Audit durability on rollback is decided explicitly — if the audit write shares the caller's
   transaction, a rollback erases the record of a decision that was made, including refusals,
   which are precisely what Principle IV wants evidence of.

**The correction that mattered**: the submitted ADR claimed Option 2 "satisfies Principle V". It
does not, on its own. A hash chain makes an altered *entry* detectable, but anyone able to write
to the store directly can disable the triggers, rewrite history, and recompute the chain so it
verifies cleanly end to end. That is tamper-evidence against the application and its callers, not
against the database operator — and Principle V asks for independent verifiability. Condition 3
closes it: a previously published head hash turns a silent rewrite into a visible mismatch.

Propagated to the spec rather than leaving the gap in the ADR alone:

- **FR-010a** — publish the chain head (hash + entry count) outside the audit store on a fixed
  interval.
- **SC-005a** — a wholesale rewritten chain that diverges from a published head is detected in
  100% of trials.
- Checklist updated: Principle V is **partially** met until FR-010a ships, and the plan's
  Constitution Check must record it as such rather than ticking it.

Option 3 was recorded as deferred on cost, not dismissed on merit — it is the only option that
gives genuine independence from the database operator, and condition 3 buys most of that benefit
far more cheaply.

## Outcome

- ✅ Impact: Storage architecture decided ahead of `/sp.plan`, so planning gates against a decided
  mechanism instead of inventing one. Spec gained one requirement and one success criterion.
- 🧪 Tests: None run. New obligations: SC-005a (rewritten-chain detection), plus the ADR's
  compliance section requires tests that attempt `UPDATE`/`DELETE` on audit rows as the
  application role and assert failure, and read health data as an uncovered role and assert zero
  rows.
- 📁 Files: `history/adr/0001-audit-log-storage-mechanism.md` (new),
  `specs/001-athlete-health-core/spec.md` (FR-010a, SC-005a),
  `specs/001-athlete-health-core/checklists/requirements.md` (notes).
- 🔁 Next prompts: owner to move ADR-0001 from Proposed to Accepted, then `/sp.plan`.
- 🧠 Reflection: The ADR's compliance section was the part worth challenging. "Satisfies
  Principle V" is the kind of claim that survives review precisely because it appears in a
  document whose purpose is to be reviewed. Checking the threat model — *satisfies it against
  whom?* — is what turned a tick into a condition.

## Evaluation notes (flywheel)

- Failure modes observed: the submitted ADR asserted full compliance with Principles V and VI
  without stating the adversary each guarantee holds against. Both claims were conditional, not
  absolute, and neither condition was written down.
- Graders run and results (PASS/FAIL): PASS — all three ADR significance tests met (long-term
  impact, viable alternatives, cross-cutting); PASS — template sections complete, no unresolved
  placeholders; PASS — every claim about PostgreSQL behaviour traced to the official docs and
  cited with a URL; FAIL then FIXED — Principle V compliance claim was overstated, now conditional
  with FR-010a as the closing requirement.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): when an ADR's compliance section claims a principle is
  satisfied, require it to name the adversary or failure mode the guarantee holds against. "Append-
  only against whom" would have caught this at authoring time.
