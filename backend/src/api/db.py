"""Database access with request-scoped identity propagation.

This module carries the load-bearing half of Principle VI. RLS policies filter on a subject,
and a pooled connection has none of its own — so every request transaction sets
`app.athlete_id` / `app.coach_id` / `app.role` with SET LOCAL, taken from a VERIFIED token
claim and never from a client-supplied header.

`SET LOCAL` is transaction-scoped, so the identity cannot leak to the next request that
borrows the same pooled connection. If it is never set, `current_setting(..., true)` returns
NULL, the policies match no rows, and the caller sees nothing — the fail-closed default.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row

#: The application connects as a non-owner role holding neither SUPERUSER nor BYPASSRLS
#: (ADR-0001 condition 2). Connecting as the owner would silently defeat every policy.
DSN = os.environ.get(
    "SHEPEAK_DSN",
    "postgresql://shepeak_app:shepeak_dev_only_change_me@localhost:55432/shepeak",
)

#: Owner DSN — migrations and tests only. Never used to serve a request.
OWNER_DSN = os.environ.get(
    "SHEPEAK_OWNER_DSN",
    "postgresql://shepeak_owner:dev_only@localhost:55432/shepeak",
)


@dataclass(frozen=True)
class Identity:
    """The verified caller. Built from token claims, never from request input."""

    role: str  # 'athlete' | 'coach'
    athlete_id: str | None = None
    coach_id: str | None = None

    def __post_init__(self) -> None:
        if self.role not in {"athlete", "coach"}:
            raise ValueError(f"unknown role: {self.role!r}")
        if self.role == "athlete" and not self.athlete_id:
            raise ValueError("athlete identity requires athlete_id")
        if self.role == "coach" and not self.coach_id:
            raise ValueError("coach identity requires coach_id")


@contextmanager
def connect(dsn: str = DSN) -> Iterator[psycopg.Connection]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        yield conn


@contextmanager
def request_transaction(
    identity: Identity | None, dsn: str = DSN
) -> Iterator[psycopg.Connection]:
    """Open a transaction with the caller's identity bound to it.

    Passing `identity=None` is legitimate and deliberate: it models an unauthenticated
    caller, and the policies must return zero rows for it. Tests rely on that (SC-006).
    """
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        with conn.transaction():
            if identity is not None:
                _bind_identity(conn, identity)
            yield conn


def _bind_identity(conn: psycopg.Connection, identity: Identity) -> None:
    """SET LOCAL the verified claims. Parameterised — these values reach a SET statement."""
    with conn.cursor() as cur:
        # set_config(..., is_local => true) is the parameterisable form of SET LOCAL.
        cur.execute("SELECT set_config('app.role', %s, true)", (identity.role,))
        cur.execute(
            "SELECT set_config('app.athlete_id', %s, true)", (identity.athlete_id or "",)
        )
        cur.execute(
            "SELECT set_config('app.coach_id', %s, true)", (identity.coach_id or "",)
        )
