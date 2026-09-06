# ADR-0001: Audit Log Storage Mechanism

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Accepted (2026-09-06, project owner)
- **Date:** 2026-09-06
- **Feature:** 001-athlete-health-core
- **Context:** Constitution Principle V requires an append-only, hash-chained audit log that an
  independent party can verify. Principle VI requires consent enforcement at the data-store layer
  rather than in application code. Spec FR-008, FR-009, FR-010, FR-011 and FR-012 depend on this
  choice, and both the audit chain and consent enforcement constrain the same storage engine, so
  they are decided together as one cluster. Track: Prototype.

## Decision

**PostgreSQL as single source of truth, with database-enforced append-only behaviour and hash
chaining via triggers, and Row-Level Security for consent enforcement.**

- PostgreSQL is the sole system of record for athlete data, consent records, and the audit log.
- Append-only behaviour and hash-chain computation are enforced by database triggers, not by
  application code.
- Consent is enforced by Row-Level Security policies on health-data tables.
- Application code never issues `UPDATE` or `DELETE` against audit rows.

The decision is adopted with the following conditions, which are what make it actually satisfy
Principles V and VI rather than appear to:

1. **`FORCE ROW LEVEL SECURITY` on every health-data table.** PostgreSQL exempts a table's owner
   from its own RLS policies by default; without `FORCE`, RLS protects everyone except the role
   most likely to be connected during development.
2. **The application connects as a role that is neither the table owner nor holds `BYPASSRLS`,
   and is not a superuser.** Superusers and `BYPASSRLS` roles bypass row security entirely, so
   RLS enforcement is only as real as the role separation behind it.
3. **The chain head is anchored outside the database** on a fixed interval — the current head
   hash and entry count written to a store the database role cannot reach. See the honest
   limitation in *Negative* below.
4. **Chain appends are serialised.** Two concurrent inserts that each read the same predecessor
   hash produce a forked chain. Append order must be serialised explicitly (advisory lock on the
   chain, or an equivalent) rather than left to transaction isolation.
5. **Audit durability on rollback is decided explicitly.** FR-008 requires the audit entry to be
   written before the response returns. If that write shares the caller's transaction, a
   subsequent rollback erases the record of a decision that was made — including refusals, which
   are exactly what Principle IV wants evidence of. The plan must state which transaction the
   audit write belongs to and justify it.

## Consequences

### Positive

- One database, one backup, one restore path, one set of credentials to secure. For the Prototype
  track this is decisively simpler than operating a second system.
- Enforcement lives below the application, which is what Principles V and VI actually ask for.
  A new or misconfigured caller cannot write around a trigger or read past an RLS policy.
- Hash chaining makes out-of-band alteration of any single entry detectable, satisfying the
  detection requirement in SC-005.
- Verification requires only read access and the chain rule, so a reviewer can check integrity
  without trusting the application — FR-010's stated requirement.
- RLS defaults to deny when enabled with no policies, so a table added without a policy fails
  closed rather than open. This aligns with Principle IV at the storage layer.
- Reversible. The audit table is an ordered, self-verifying log, which is precisely the shape an
  external ledger would ingest, so extraction later is an export rather than a redesign.

### Negative

- **Trigger logic and RLS policies are real schema complexity**, and they are security-critical
  code in a language (PL/pgSQL) that the team will exercise less than application code. They need
  their own tests — Principle VIII applies to them.
- **This is tamper-evident, not tamper-proof, and it does not defend against the database
  operator.** A superuser can `ALTER TABLE ... DISABLE TRIGGER`, rewrite history, and recompute
  the chain so that it verifies cleanly end to end. Verification detects an *altered entry*; it
  does not detect a *rewritten chain*. This is the gap condition 3 exists to close: an externally
  anchored head hash turns a silent rewrite into a visible mismatch. Without that anchor, the
  honest claim is "protected against the application and its callers", not "independently
  verifiable" — and Principle V asks for the latter.
- Serialising chain appends puts a single ordering point on every audited decision. At prototype
  volumes this is irrelevant; it is a known scaling limit, not a present cost.
- Writing the audit entry before the response places it on the request's critical path.
- Consent logic expressed as RLS policies is harder to read and debug than application code, and
  policy mistakes fail silently by returning fewer rows rather than raising an error.

## Alternatives Considered

**Option 1 — PostgreSQL only, hash chain and consent checks in application code.**
Rejected. It puts both guarantees in exactly the layer Principle VI names as insufficient: any
caller that bypasses the application bypasses the guarantee. It is also the cheapest option to
get wrong invisibly, because nothing fails when the check is simply not called.

**Option 3 — External immutable ledger (separate append-only service or blockchain-style log).**
Rejected for this track, on cost rather than on merit. It gives genuine independence from the
database operator, which is the one thing Option 2 cannot provide on its own. But it introduces a
second system to operate, secure and keep consistent with PostgreSQL, and a two-system write
raises the question of what happens when the ledger write succeeds and the database write does
not. Deferred rather than dismissed: condition 3 above buys most of the independence benefit at a
fraction of the cost, and the migration path stays open.

## Compliance

- **Principle V (Full Auditability)**: satisfied for alteration of individual entries by the hash
  chain and triggers; satisfied for independence from the database operator only once condition 3
  (external anchoring) is implemented. Until then, this principle is partially met and should be
  recorded as such in the plan's Constitution Check.
- **Principle VI (Privacy & Consent First)**: satisfied by RLS, conditional on `FORCE ROW LEVEL
  SECURITY` and on the role separation in condition 2.
- **Principle IV (Fail Closed)**: supported — RLS with no matching policy denies by default.
- **Principle VIII (Spec-Driven Development)**: triggers and policies require their own tests,
  including a test that attempts `UPDATE` and `DELETE` on audit rows as the application role and
  asserts failure, and a test that reads health data as an uncovered role and asserts no rows.

## References

- Feature Spec: [specs/001-athlete-health-core/spec.md](../../specs/001-athlete-health-core/spec.md)
- Implementation Plan: not yet created — this ADR precedes `/sp.plan` deliberately
- Related ADRs: none
- Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) v1.0.0,
  Principles IV, V, VI, VIII
- Evaluator Evidence: [history/prompts/001-athlete-health-core/0004-audit-log-storage-adr.plan.prompt.md](../prompts/001-athlete-health-core/0004-audit-log-storage-adr.plan.prompt.md)
- PostgreSQL documentation, verified 2026-09-06:
  - [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) —
    superusers and `BYPASSRLS` roles bypass row security entirely; table owners bypass by default
    unless `FORCE ROW LEVEL SECURITY` is set.
  - [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) — enabling RLS with
    no policies applies a default-deny.
