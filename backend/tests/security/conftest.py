"""Database fixtures for the security suite.

These tests need a real PostgreSQL because the guarantees under test are enforced by
PostgreSQL — RLS policies and triggers. Testing them against a mock would test the mock.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

MIGRATIONS = sorted((Path(__file__).resolve().parents[2] / "migrations").glob("*.sql"))

OWNER_DSN = os.environ.get(
    "SHEPEAK_OWNER_DSN",
    "postgresql://shepeak_owner:dev_only@localhost:55432/shepeak",
)
APP_DSN = os.environ.get(
    "SHEPEAK_DSN",
    "postgresql://shepeak_app:shepeak_dev_only_change_me@localhost:55432/shepeak",
)


def _db_available() -> bool:
    try:
        with psycopg.connect(OWNER_DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _db_available(), reason="PostgreSQL not reachable; start docker compose"
)


@pytest.fixture(scope="session", autouse=True)
def migrated():
    """Apply migrations once per session, from a clean schema."""
    with psycopg.connect(OWNER_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            cur.execute("GRANT ALL ON SCHEMA public TO shepeak_owner;")
        for path in MIGRATIONS:
            conn.execute(path.read_text(encoding="utf-8"))
    return True


@pytest.fixture
def owner():
    with psycopg.connect(OWNER_DSN, row_factory=dict_row, autocommit=True) as conn:
        yield conn


@pytest.fixture
def app_conn():
    """A connection as the application role — non-owner, NOBYPASSRLS, not superuser."""
    with psycopg.connect(APP_DSN, row_factory=dict_row, autocommit=True) as conn:
        yield conn


@pytest.fixture
def athlete_with_consent(owner):
    """Seed one coached athlete with a live consent and one health metric."""
    coach_id = str(uuid.uuid4())
    athlete_id = str(uuid.uuid4())
    owner.execute(
        "INSERT INTO coach (id, display_name) VALUES (%s, %s)", (coach_id, "Coach Amara")
    )
    owner.execute(
        "INSERT INTO athlete (id, display_name, coach_id) VALUES (%s, %s, %s)",
        (athlete_id, "Test Athlete", coach_id),
    )
    owner.execute(
        "INSERT INTO consent_record (athlete_id, purpose) VALUES (%s, 'injury_risk_scoring')",
        (athlete_id,),
    )
    owner.execute(
        """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
           VALUES (%s, 'sleep', '7.5', now())""",
        (athlete_id,),
    )
    return {"athlete_id": athlete_id, "coach_id": coach_id}
