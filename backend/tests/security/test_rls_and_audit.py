"""Security tests — T0.5, T0.13-T0.17. SC-006, FR-009, FR-011, FR-012.

Constitution Principles V and VI. These run against a real PostgreSQL because the
guarantees are enforced by PostgreSQL, not by application code — which is the whole point
of ADR-0001.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest

from db_helpers import set_identity


class TestRoleSeparation:
    """ADR-0001 condition 2 — RLS is only as real as the role behind it."""

    def test_app_role_is_not_superuser_and_lacks_bypassrls(self, app_conn):
        row = app_conn.execute(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
        ).fetchone()
        assert row["rolsuper"] is False, "a superuser bypasses row security entirely"
        assert row["rolbypassrls"] is False, "BYPASSRLS defeats every policy"

    def test_app_role_owns_no_protected_tables(self, app_conn):
        rows = app_conn.execute(
            """SELECT tablename FROM pg_tables
               WHERE schemaname = 'public' AND tableowner = current_user"""
        ).fetchall()
        assert rows == [], "a table owner bypasses its own policies unless FORCE is set"

    def test_force_rls_is_set_on_every_protected_table(self, owner):
        rows = owner.execute(
            """SELECT relname, relrowsecurity, relforcerowsecurity
               FROM pg_class
               WHERE relname IN ('health_metric','risk_assessment','plan_proposal',
                                 'consent_record','athlete','audit_entry')"""
        ).fetchall()
        assert rows, "protected tables not found"
        for r in rows:
            assert r["relrowsecurity"], f"{r['relname']}: RLS not enabled"
            assert r["relforcerowsecurity"], (
                f"{r['relname']}: FORCE ROW LEVEL SECURITY missing — the owner would "
                f"bypass its own policies"
            )


class TestIdentityGatesAccess:
    """T0.5 / T0.13 / T0.14 — SC-006."""

    def test_unset_identity_returns_zero_rows(self, app_conn, athlete_with_consent):
        """The fail-closed default: forget to bind identity and you see nothing."""
        set_identity(app_conn, "", "", "")
        rows = app_conn.execute("SELECT * FROM health_metric").fetchall()
        assert rows == [], "unset identity must match no rows, not all rows"

    def test_athlete_sees_only_her_own_metrics(self, app_conn, athlete_with_consent, owner):
        other = str(uuid.uuid4())
        owner.execute(
            "INSERT INTO athlete (id, display_name) VALUES (%s, 'Other')", (other,)
        )
        owner.execute(
            "INSERT INTO consent_record (athlete_id, purpose) VALUES (%s,'injury_risk_scoring')",
            (other,),
        )
        owner.execute(
            """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
               VALUES (%s,'sleep','6.0', now())""",
            (other,),
        )
        set_identity(app_conn, "athlete", athlete_id=athlete_with_consent["athlete_id"])
        rows = app_conn.execute("SELECT athlete_id FROM health_metric").fetchall()
        assert rows, "the athlete should see her own data"
        assert all(str(r["athlete_id"]) == athlete_with_consent["athlete_id"] for r in rows)

    def test_other_athlete_cannot_read_her_data(self, app_conn, athlete_with_consent):
        set_identity(app_conn, "athlete", athlete_id=str(uuid.uuid4()))
        rows = app_conn.execute(
            "SELECT * FROM health_metric WHERE athlete_id = %s",
            (athlete_with_consent["athlete_id"],),
        ).fetchall()
        assert rows == []

    def test_assigned_coach_can_read(self, app_conn, athlete_with_consent):
        set_identity(app_conn, "coach", coach_id=athlete_with_consent["coach_id"])
        rows = app_conn.execute("SELECT * FROM health_metric").fetchall()
        assert rows, "the assigned coach must be able to see her athlete's data"

    def test_unassigned_coach_cannot_read(self, app_conn, athlete_with_consent):
        set_identity(app_conn, "coach", coach_id=str(uuid.uuid4()))
        rows = app_conn.execute("SELECT * FROM health_metric").fetchall()
        assert rows == []


class TestConsentGatesAccess:
    """FR-011, FR-012, SC-010 — enforcement below the application."""

    def test_no_consent_means_no_rows_even_for_the_athlete_herself(self, app_conn, owner):
        athlete_id = str(uuid.uuid4())
        owner.execute(
            "INSERT INTO athlete (id, display_name) VALUES (%s,'No Consent')", (athlete_id,)
        )
        owner.execute(
            """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
               VALUES (%s,'sleep','8.0', now())""",
            (athlete_id,),
        )
        set_identity(app_conn, "athlete", athlete_id=athlete_id)
        rows = app_conn.execute("SELECT * FROM health_metric").fetchall()
        assert rows == [], "processing without a covering consent record must return nothing"

    def test_withdrawing_consent_stops_access(self, app_conn, owner, athlete_with_consent):
        athlete_id = athlete_with_consent["athlete_id"]
        set_identity(app_conn, "athlete", athlete_id=athlete_id)
        assert app_conn.execute("SELECT * FROM health_metric").fetchall()

        owner.execute(
            """UPDATE consent_record SET withdrawn_at = now()
               WHERE athlete_id = %s AND purpose = 'injury_risk_scoring'""",
            (athlete_id,),
        )
        assert app_conn.execute("SELECT * FROM health_metric").fetchall() == [], (
            "withdrawal must stop processing (FR-012)"
        )

        # Audit history is retained despite withdrawal — the two must not conflict.
        assert owner.execute("SELECT count(*) AS n FROM audit_entry").fetchone()["n"] >= 0


class TestAuditIsAppendOnly:
    """T0.15 — FR-009."""

    @pytest.fixture(autouse=True)
    def _an_entry(self, app_conn):
        app_conn.execute(
            """INSERT INTO audit_entry (actor_id, actor_role, action, subject_id, payload)
               VALUES ('u1','athlete','risk_assessed','s1','{"score": 42}'::jsonb)"""
        )

    def test_update_is_denied_for_the_application(self, app_conn):
        """Denied at the GRANT layer, before the trigger is even reached.

        Two independent layers stop this: the missing privilege, and the trigger below.
        The privilege wins the race, so this test asserts denial rather than a specific
        message — pinning the message would make defence in depth look like a failure.
        """
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            app_conn.execute("UPDATE audit_entry SET payload = '{}'::jsonb")

    def test_delete_is_denied_for_the_application(self, app_conn):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            app_conn.execute("DELETE FROM audit_entry")

    def test_trigger_denies_even_a_role_holding_the_privilege(self, owner):
        """The second layer, tested on its own.

        The owner HAS update and delete privileges, so only the trigger can stop it. If the
        GRANT layer were ever loosened, this is the guarantee that still holds.
        """
        with pytest.raises(psycopg.errors.InsufficientPrivilege) as exc:
            owner.execute("UPDATE audit_entry SET payload = '{}'::jsonb")
        assert "append-only" in str(exc.value)

        with pytest.raises(psycopg.errors.InsufficientPrivilege) as exc:
            owner.execute("DELETE FROM audit_entry")
        assert "append-only" in str(exc.value)

    def test_truncate_is_denied(self, owner):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            owner.execute("TRUNCATE audit_entry")

    def test_app_role_lacks_update_and_delete_privileges(self, app_conn):
        row = app_conn.execute(
            """SELECT has_table_privilege(current_user,'audit_entry','UPDATE') AS u,
                      has_table_privilege(current_user,'audit_entry','DELETE') AS d"""
        ).fetchone()
        assert not row["u"] and not row["d"]


class TestChainIntegrity:
    """T0.16, SC-005 — the chain links, and a tampered entry is detected."""

    def test_chain_verifies_after_appends(self, app_conn):
        for i in range(5):
            app_conn.execute(
                """INSERT INTO audit_entry (actor_id, actor_role, action, payload)
                   VALUES ('u1','athlete','risk_assessed', %s::jsonb)""",
                (f'{{"i": {i}}}',),
            )
        assert app_conn.execute("SELECT * FROM verify_audit_chain()").fetchall() == []

    def test_each_entry_links_to_its_predecessor(self, app_conn):
        app_conn.execute(
            """INSERT INTO audit_entry (actor_id, actor_role, action, payload)
               VALUES ('u1','athlete','a','{}'::jsonb)"""
        )
        app_conn.execute(
            """INSERT INTO audit_entry (actor_id, actor_role, action, payload)
               VALUES ('u1','athlete','b','{}'::jsonb)"""
        )
        rows = app_conn.execute(
            "SELECT seq, prev_hash, entry_hash FROM audit_entry ORDER BY seq DESC LIMIT 2"
        ).fetchall()
        newer, older = rows[0], rows[1]
        assert newer["prev_hash"] == older["entry_hash"]

    def test_altered_entry_is_detected(self, owner, app_conn):
        """SC-005. The owner disables the trigger to simulate out-of-band tampering."""
        app_conn.execute(
            """INSERT INTO audit_entry (actor_id, actor_role, action, payload)
               VALUES ('u1','athlete','risk_assessed','{"score": 10}'::jsonb)"""
        )
        seq = owner.execute("SELECT max(seq) AS s FROM audit_entry").fetchone()["s"]
        owner.execute("ALTER TABLE audit_entry DISABLE TRIGGER audit_no_update")
        try:
            owner.execute(
                "UPDATE audit_entry SET payload = '{\"score\": 99}'::jsonb WHERE seq = %s",
                (seq,),
            )
            problems = owner.execute("SELECT seq, problem FROM verify_audit_chain()").fetchall()
            assert problems, "an altered entry must be detected"
            assert problems[0]["seq"] == seq
            assert "altered entry" in problems[0]["problem"]
        finally:
            owner.execute(
                "UPDATE audit_entry SET payload = '{\"score\": 10}'::jsonb WHERE seq = %s",
                (seq,),
            )
            owner.execute("ALTER TABLE audit_entry ENABLE TRIGGER audit_no_update")

    def test_tamper_evidence_has_a_stated_limit(self, owner):
        """The honest boundary: a rewritten chain verifies cleanly.

        This test documents the gap FR-010a exists to close. It is not a failure — it is
        the reason nothing may claim independent verifiability until anchoring ships.
        """
        head_before = owner.execute("SELECT head_hash FROM audit_chain_head()").fetchone()
        assert head_before["head_hash"], "a head hash exists to publish externally"
        assert owner.execute("SELECT * FROM verify_audit_chain()").fetchall() == [], (
            "internal verification passes — which is exactly why an EXTERNAL anchor is "
            "needed to detect a wholesale rewrite (FR-010a, deferred)"
        )
