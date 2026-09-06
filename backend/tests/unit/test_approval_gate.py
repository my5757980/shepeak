"""Approval gate tests — FR-004, FR-005, FR-021, SC-003, SC-011, US2 scenarios 6-8.

Constitution Principle II. These tests assert the system REFUSES; a suite that only proved
approval works would be a blocking review finding.
"""

from __future__ import annotations

import pytest

from orchestrator.approval import (
    ApprovalContext,
    ApproverRole,
    DenialReason,
    approval_still_valid,
    evaluate,
    plan_content_hash,
)
from risk_engine.types import RiskBand

PLAN = {"week": 1, "sessions": ["easy run", "rest", "nets"]}
HASH = plan_content_hash(PLAN)


def ctx(**overrides) -> ApprovalContext:
    base = dict(
        athlete_id="ath-1",
        assigned_coach_id="coach-1",
        band=RiskBand.LOW,
        plan_state="proposed",
        plan_content_hash=HASH,
        actor_id="ath-1",
        actor_role=ApproverRole.ATHLETE,
    )
    base.update(overrides)
    return ApprovalContext(**base)


class TestTieredApproval:
    """FR-021 — the rule the owner chose: coach mandatory at elevated and high."""

    @pytest.mark.parametrize("band", [RiskBand.LOW, RiskBand.MODERATE])
    def test_athlete_may_self_approve_below_elevated(self, band):
        decision = evaluate(ctx(band=band))
        assert decision.allowed
        assert decision.approver_role is ApproverRole.ATHLETE

    @pytest.mark.parametrize("band", [RiskBand.ELEVATED, RiskBand.HIGH])
    def test_athlete_self_approval_refused_at_elevated_and_high(self, band):
        """SC-011 / US2 scenario 6."""
        decision = evaluate(ctx(band=band))
        assert not decision.allowed
        assert decision.reason is DenialReason.COACH_APPROVAL_REQUIRED
        assert "coach" in decision.detail.lower()

    @pytest.mark.parametrize("band", [RiskBand.ELEVATED, RiskBand.HIGH])
    def test_assigned_coach_may_approve_high_risk(self, band):
        decision = evaluate(
            ctx(band=band, actor_id="coach-1", actor_role=ApproverRole.COACH)
        )
        assert decision.allowed
        assert decision.approver_role is ApproverRole.COACH


class TestUnaffiliatedAthlete:
    """US2 scenario 8 — the edge the tiered rule creates. Fail closed."""

    @pytest.mark.parametrize("band", [RiskBand.ELEVATED, RiskBand.HIGH])
    def test_no_coach_means_high_risk_plan_cannot_activate(self, band):
        decision = evaluate(ctx(band=band, assigned_coach_id=None))
        assert not decision.allowed
        assert decision.reason is DenialReason.NO_AUTHORISED_COACH
        assert "no coach is assigned" in decision.detail

    def test_no_coach_does_not_fall_back_to_self_approval(self):
        """The failure mode this test exists to prevent: 'no coach, so let her approve it'."""
        decision = evaluate(
            ctx(band=RiskBand.HIGH, assigned_coach_id=None, actor_role=ApproverRole.ATHLETE)
        )
        assert not decision.allowed, (
            "an unaffiliated athlete must not become her own approver at high risk — "
            "that would hollow out Principle II"
        )

    def test_unaffiliated_athlete_can_still_self_approve_low_risk(self):
        decision = evaluate(ctx(band=RiskBand.LOW, assigned_coach_id=None))
        assert decision.allowed


class TestWrongActor:
    def test_other_athlete_cannot_approve(self):
        decision = evaluate(ctx(actor_id="ath-2"))
        assert not decision.allowed
        assert decision.reason is DenialReason.NOT_THIS_ATHLETE

    def test_unassigned_coach_cannot_approve(self):
        decision = evaluate(
            ctx(band=RiskBand.HIGH, actor_id="coach-9", actor_role=ApproverRole.COACH)
        )
        assert not decision.allowed
        assert decision.reason is DenialReason.NOT_THIS_ATHLETES_COACH


class TestPlanState:
    """SC-003 — no activation path without a current, valid approval."""

    @pytest.mark.parametrize("state", ["approved", "rejected", "superseded"])
    def test_only_proposed_plans_can_be_approved(self, state):
        decision = evaluate(ctx(plan_state=state))
        assert not decision.allowed
        assert decision.reason is DenialReason.PLAN_NOT_PROPOSED


class TestApprovalInvalidation:
    """FR-005 / US2 scenario 4 — approval must not survive modification."""

    def test_approval_binds_to_content_hash(self):
        decision = evaluate(ctx())
        assert decision.allowed
        assert decision.binds_content_hash == HASH

    def test_modified_plan_invalidates_approval(self):
        modified = {**PLAN, "sessions": ["hard intervals", "hard intervals", "nets"]}
        assert not approval_still_valid(HASH, modified), (
            "an approval that survives a change to the plan is not an approval of the plan"
        )

    def test_unmodified_plan_keeps_approval(self):
        assert approval_still_valid(HASH, dict(PLAN))

    def test_hash_is_order_independent(self):
        assert plan_content_hash({"a": 1, "b": 2}) == plan_content_hash({"b": 2, "a": 1})

    def test_hash_changes_on_any_content_change(self):
        assert plan_content_hash(PLAN) != plan_content_hash({**PLAN, "week": 2})
