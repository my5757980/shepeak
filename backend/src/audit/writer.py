"""Audit writing and verification (FR-008, FR-009, FR-010).

The hash chain itself lives in the database (ADR-0001) — this module only submits entries
and reads verification results back. Deliberately thin: if the chain were computed here, an
application bug or a caller bypassing the application would break the guarantee, which is
precisely what Principle V forbids.

ADR-0001 condition 5 — durability under rollback — is implemented here as an explicit
decision rather than an accident. See `write_entry`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row

from api.db import DSN


@dataclass(frozen=True)
class AuditEntry:
    actor_id: str
    actor_role: str
    action: str
    subject_id: str | None
    payload: dict[str, Any]
    rule_set_version: str | None = None
    model_version: str | None = None


_INSERT = """
    INSERT INTO audit_entry
        (actor_id, actor_role, action, subject_id, payload, rule_set_version, model_version)
    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
    RETURNING seq, entry_hash, prev_hash, created_at
"""


def write_entry(entry: AuditEntry, dsn: str = DSN) -> dict[str, Any]:
    """Append one entry on its OWN connection and commit it immediately.

    ADR-0001 condition 5, decided: the audit write does NOT share the caller's transaction.

    Rationale — a refusal is a decision. If the audit write joined the request transaction
    and that transaction later aborted, the record of the refusal would vanish with it. The
    refusals are exactly the evidence Principle IV wants to be able to produce afterwards,
    so losing them on rollback is the worse failure.

    The accepted cost: an entry can survive a request that ultimately failed. That is why
    the payload records the outcome, including failures, rather than assuming success. An
    audit log that over-records is recoverable; one that under-records is not.
    """
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                _INSERT,
                (
                    entry.actor_id,
                    entry.actor_role,
                    entry.action,
                    entry.subject_id,
                    json.dumps(entry.payload, sort_keys=True, default=str),
                    entry.rule_set_version,
                    entry.model_version,
                ),
            )
            row = cur.fetchone()
    assert row is not None
    return dict(row)


def verify_chain(dsn: str = DSN) -> list[dict[str, Any]]:
    """Run the independent chain verification. Empty list means the chain is intact.

    Note the honest limit: this proves no entry has been altered in place. It cannot detect
    a chain rewritten wholesale by someone able to disable the triggers — that needs the
    externally published head (FR-010a), which is deferred to the roadmap.
    """
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT seq, problem FROM verify_audit_chain()")
            return [dict(r) for r in cur.fetchall()]


def chain_head(dsn: str = DSN) -> dict[str, Any]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT entry_count, head_hash FROM audit_chain_head()")
            row = cur.fetchone()
    assert row is not None
    return dict(row)
