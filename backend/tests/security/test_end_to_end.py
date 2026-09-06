"""T3.3, T2.18, T2.8 — end-to-end through the real stack.

Integration only: the per-path refusal tests live in tests/refusal/ and tests/unit/ and must
already pass. What these add is proof the guarantees survive the trip through the database,
the orchestrator, and the approval gate together.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from api.db import Identity
from orchestrator import assess as flow
from orchestrator import propose

NOW = datetime.now(timezone.utc)


def ago(**kw):
    return NOW - timedelta(**kw)


def _make_soreness_stale(owner, athlete_id: str) -> None:
    """Leave one soreness reading, 31h old — past its 24h window.

    The fresh reading has to go: the engine reads the LATEST capture per metric, so simply
    adding an old row changes nothing. That is correct behaviour, and getting this wrong the
    first time is exactly why the test exercises the real query rather than the engine alone.
    """
    owner.execute("DELETE FROM health_metric WHERE athlete_id = %s AND kind = 'soreness'",
                  (athlete_id,))
    owner.execute(
        """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
           VALUES (%s,'soreness','8',%s)""",
        (athlete_id, ago(hours=31)),
    )


@pytest.fixture
def athlete(owner):
    """A coached athlete with consent and a full, fresh, elevated-risk picture."""
    coach_id, athlete_id = str(uuid.uuid4()), str(uuid.uuid4())
    owner.execute("INSERT INTO coach (id, display_name) VALUES (%s,'E2E Coach')", (coach_id,))
    owner.execute(
        "INSERT INTO athlete (id, display_name, coach_id) VALUES (%s,'E2E Athlete',%s)",
        (athlete_id, coach_id),
    )
    for purpose in ("injury_risk_scoring", "plan_generation", "explanation_generation"):
        owner.execute(
            "INSERT INTO consent_record (athlete_id, purpose) VALUES (%s,%s)",
            (athlete_id, purpose),
        )
    for day in range(10, 32):
        owner.execute(
            """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
               VALUES (%s,'training_load','100',%s)""",
            (athlete_id, ago(days=day)),
        )
    for kind, value, captured in [
        ("training_load", "150", ago(hours=3)),
        ("sleep", "6.0", ago(hours=6)),
        ("soreness", "8", ago(hours=5)),
        ("cycle_phase", "ovulatory", ago(days=1)),
        ("contraception_status", "false", ago(days=12)),
        ("iron_status", "40", ago(days=28)),
    ]:
        owner.execute(
            """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
               VALUES (%s,%s,%s,%s)""",
            (athlete_id, kind, value, captured),
        )
    return {"athlete_id": athlete_id, "coach_id": coach_id}


@pytest.fixture
def as_athlete(athlete):
    return Identity(role="athlete", athlete_id=athlete["athlete_id"])


@pytest.fixture
def as_coach(athlete):
    return Identity(role="coach", coach_id=athlete["coach_id"])


class TestAssessmentEndToEnd:
    def test_elevated_athlete_scores_and_requires_coach(self, as_athlete, athlete):
        result = flow.run(as_athlete, athlete["athlete_id"])
        assert result["outcome"] == "assessed"
        assert result["requires_coach_approval"] is True
        assert result["evidence"], "evidence must survive the round trip (FR-013)"
        assert any(r["is_sex_specific"] for r in result["fired_rules"]), (
            "an athlete with cycle data must get a sex-specific factor cited (SC-001)"
        )

    def test_audit_entry_exists_before_the_caller_sees_the_result(
        self, as_athlete, athlete, owner
    ):
        """T2.18 / FR-008 — the write is committed on its own connection before returning."""
        before = owner.execute("SELECT count(*) AS n FROM audit_entry").fetchone()["n"]
        result = flow.run(as_athlete, athlete["athlete_id"])
        after = owner.execute("SELECT count(*) AS n FROM audit_entry").fetchone()["n"]
        assert after > before, "no audit entry was written for a returned assessment"

        row = owner.execute(
            "SELECT action, subject_id FROM audit_entry ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        assert row["action"] == "risk_assessed"
        assert row["subject_id"] == athlete["athlete_id"]
        assert result["outcome"] == "assessed"

    def test_stale_data_refuses_through_the_full_stack(self, as_athlete, athlete, owner):
        """T3.3 — the refusal survives the database and orchestrator, not just the engine."""
        _make_soreness_stale(owner, athlete["athlete_id"])
        result = flow.run(as_athlete, athlete["athlete_id"])
        assert result["outcome"] == "refused"
        assert result["reason"] == "stale_metric"
        assert "soreness" in result["offending_inputs"]
        assert result["escalated"] is True

        escalations = owner.execute(
            "SELECT count(*) AS n FROM escalation WHERE athlete_id = %s",
            (athlete["athlete_id"],),
        ).fetchone()["n"]
        assert escalations >= 1, "SA-001 requires the refusal to reach a human"

    def test_refusal_is_audited_too(self, as_athlete, athlete, owner):
        _make_soreness_stale(owner, athlete["athlete_id"])
        flow.run(as_athlete, athlete["athlete_id"])
        row = owner.execute(
            "SELECT action FROM audit_entry ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        assert row["action"] == "risk_refused", (
            "a withheld score is a decision and must be recorded (Principle V)"
        )


class TestSupersededScores:
    """T2.8 / FR-019 — recomputation retains the earlier score."""

    def test_earlier_assessment_is_retained_and_linked(self, as_athlete, athlete, owner):
        first = flow.run(as_athlete, athlete["athlete_id"])
        assert first["outcome"] == "assessed"

        owner.execute(
            """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
               VALUES (%s,'sleep','8.5',%s)""",
            (athlete["athlete_id"], ago(hours=1)),
        )
        second = flow.run(as_athlete, athlete["athlete_id"])
        assert second["outcome"] == "assessed"
        assert second["assessment_id"] != first["assessment_id"]

        rows = owner.execute(
            """SELECT id, score, superseded_by FROM risk_assessment
               WHERE athlete_id = %s AND score IS NOT NULL ORDER BY computed_at""",
            (athlete["athlete_id"],),
        ).fetchall()
        assert len(rows) >= 2, "the earlier score must still exist, not be overwritten"
        assert str(rows[0]["superseded_by"]) == second["assessment_id"]
        assert rows[-1]["superseded_by"] is None, "the current score supersedes nothing"


class TestApprovalEndToEnd:
    """Principle II through the real gate, database, and audit."""

    def test_athlete_cannot_self_approve_elevated_plan(self, as_athlete, athlete):
        plan = propose.current_or_new(as_athlete, athlete["athlete_id"])
        assert plan["outcome"] == "proposed"
        assert plan["requires_coach_approval"] is True

        outcome = propose.decide(as_athlete, plan["plan_id"], "approved")
        assert outcome["allowed"] is False
        assert outcome["reason"] == "coach_approval_required"

    def test_plan_stays_proposed_after_a_denied_attempt(self, as_athlete, athlete, owner):
        plan = propose.current_or_new(as_athlete, athlete["athlete_id"])
        propose.decide(as_athlete, plan["plan_id"], "approved")
        state = owner.execute(
            "SELECT state FROM plan_proposal WHERE id = %s", (plan["plan_id"],)
        ).fetchone()["state"]
        assert state == "proposed", "a denied attempt must not change the plan's state"

    def test_denied_attempt_is_audited(self, as_athlete, athlete, owner):
        plan = propose.current_or_new(as_athlete, athlete["athlete_id"])
        propose.decide(as_athlete, plan["plan_id"], "approved")
        row = owner.execute(
            "SELECT action, payload FROM audit_entry ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        assert row["action"] == "plan_decision_denied"
        assert row["payload"]["denied_reason"] == "coach_approval_required"

    def test_coach_can_approve_and_it_is_recorded(self, as_athlete, as_coach, athlete, owner):
        plan = propose.current_or_new(as_athlete, athlete["athlete_id"])
        outcome = propose.decide(as_coach, plan["plan_id"], "approved")
        assert outcome["allowed"] is True
        assert outcome["approver_role"] == "coach"

        record = owner.execute(
            """SELECT approver_role, decision, approved_content_hash
               FROM approval_record WHERE plan_id = %s""",
            (plan["plan_id"],),
        ).fetchone()
        assert record["approver_role"] == "coach"
        assert record["decision"] == "approved"
        assert record["approved_content_hash"] == plan["content_hash"], (
            "the approval must bind to the exact content approved (FR-005)"
        )

    def test_no_plan_without_a_score(self, as_athlete, athlete, owner):
        """Fail closed: a refused assessment yields no plan at all."""
        _make_soreness_stale(owner, athlete["athlete_id"])
        plan = propose.current_or_new(as_athlete, athlete["athlete_id"])
        assert plan["outcome"] == "no_plan"
        assert plan["reason"] == "stale_metric"
