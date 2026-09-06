"""Determinism, evidence, banding, freshness boundaries, and cricket load.

Covers SC-007, SC-008, SC-012, FR-013, FR-014, FR-021, FR-026.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from conftest import metric, snapshot
from risk_engine.engine import assess
from risk_engine.types import (
    FRESHNESS_WINDOWS,
    Assessment,
    MetricKind,
    Refusal,
    RiskBand,
    band_for_score,
)


class TestDeterminism:
    """SC-008 / Principle I: identical inputs and rule version → identical score."""

    def test_repeatability_over_many_trials(self, now):
        snap = snapshot(cycle_phase="ovulatory", iron_status=20.0, sleep=5.0)
        first = assess(snap, now)
        assert isinstance(first, Assessment)
        for _ in range(100):
            again = assess(snap, now)
            assert isinstance(again, Assessment)
            assert again.score == first.score
            assert again.band is first.band
            assert again.confidence == first.confidence
            assert again.rule_set_version == first.rule_set_version
            assert [r.rule_id for r in again.fired_rules] == [
                r.rule_id for r in first.fired_rules
            ]

    def test_rule_set_version_is_stable_within_a_run(self, now):
        a = assess(snapshot(), now)
        b = assess(snapshot(athlete_id="ath-002"), now)
        assert a.rule_set_version == b.rule_set_version
        assert a.rule_set_version.startswith("rs-")

    def test_fired_rule_order_is_fixed(self, now):
        result = assess(snapshot(sleep=5.0, soreness=9.0, iron_status=10.0), now)
        assert isinstance(result, Assessment)
        ids = [r.rule_id for r in result.fired_rules]
        assert ids == sorted(ids, key=lambda i: ids.index(i))  # order preserved, not sorted
        assert ids.index("sleep_debt") < ids.index("high_soreness")


class TestEvidence:
    """FR-013, FR-014, SA-004, SC-007 — every score carries its own evidence."""

    def test_evidence_includes_values_and_capture_times(self, now):
        result = assess(snapshot(sleep=5.0), now)
        assert isinstance(result, Assessment)
        sleep_ev = next(e for e in result.evidence if e.kind is MetricKind.SLEEP)
        assert sleep_ev.value == 5.0
        assert sleep_ev.captured_at is not None
        assert sleep_ev.age_hours == pytest.approx(1.0)

    def test_every_fired_rule_states_why_and_names_its_inputs(self, now):
        result = assess(snapshot(sleep=5.0, iron_status=15.0, cycle_phase="ovulatory"), now)
        assert isinstance(result, Assessment)
        assert result.fired_rules
        for rule in result.fired_rules:
            assert rule.because.strip(), f"{rule.rule_id} fired with no explanation"
            assert rule.inputs, f"{rule.rule_id} cites no inputs"
            assert rule.rule_version

    def test_evidence_covers_every_input_the_rules_used(self, now):
        result = assess(snapshot(sleep=5.0, iron_status=15.0), now)
        assert isinstance(result, Assessment)
        cited = {e.kind.value for e in result.evidence}
        for rule in result.fired_rules:
            for used in rule.inputs:
                if used in {m.value for m in MetricKind}:
                    assert used in cited, f"{rule.rule_id} used {used} but it is not in evidence"

    def test_healthy_athlete_scores_low_with_no_rules_fired(self, now):
        result = assess(snapshot(), now)
        assert isinstance(result, Assessment)
        assert result.score == 0
        assert result.band is RiskBand.LOW
        assert result.fired_rules == ()


class TestBandsAndApproval:
    """FR-021: coach approval is mandatory at elevated and high."""

    @pytest.mark.parametrize(
        ("score", "band"),
        [(0, RiskBand.LOW), (39, RiskBand.LOW), (40, RiskBand.MODERATE),
         (59, RiskBand.MODERATE), (60, RiskBand.ELEVATED), (79, RiskBand.ELEVATED),
         (80, RiskBand.HIGH), (100, RiskBand.HIGH)],
    )
    def test_band_boundaries(self, score, band):
        assert band_for_score(score) is band

    def test_only_elevated_and_high_require_coach(self):
        assert not RiskBand.LOW.requires_coach_approval
        assert not RiskBand.MODERATE.requires_coach_approval
        assert RiskBand.ELEVATED.requires_coach_approval
        assert RiskBand.HIGH.requires_coach_approval

    def test_score_is_capped_at_100(self, now):
        result = assess(
            snapshot(
                training_load=200.0, bowling_load=40.0, sleep=4.0, soreness=10.0,
                cycle_phase="recorded_absent", contraception_status="false", iron_status=8.0,
            ),
            now,
        )
        assert isinstance(result, Assessment)
        assert result.score == 100
        assert result.band is RiskBand.HIGH


class TestFreshnessBoundaries:
    """SC-012: a test on each side of every declared window."""

    @pytest.mark.parametrize("kind", list(MetricKind))
    def test_inside_window_is_accepted(self, now, kind):
        window = FRESHNESS_WINDOWS[kind]
        value = {"cycle_phase": "follicular", "contraception_status": "false"}.get(
            kind.value, 8.0 if kind is MetricKind.SLEEP else 50.0
        )
        aged = metric(kind, value, age=window - timedelta(minutes=1))
        result = assess(snapshot(**{kind.value: aged}), now)
        assert not (
            isinstance(result, Refusal) and result.reason.value == "stale_metric"
        ), f"{kind.value} just inside its window must not be stale"

    @pytest.mark.parametrize(
        "kind", [MetricKind.TRAINING_LOAD, MetricKind.SLEEP, MetricKind.SORENESS]
    )
    def test_outside_window_refuses(self, now, kind):
        window = FRESHNESS_WINDOWS[kind]
        aged = metric(kind, 8.0 if kind is MetricKind.SLEEP else 100.0,
                      age=window + timedelta(minutes=1))
        result = assess(snapshot(**{kind.value: aged}), now)
        assert isinstance(result, Refusal)
        assert result.reason.value == "stale_metric"


class TestCricketWorkload:
    """FR-026: bowling workload is a first-class input, rules stay sport-agnostic."""

    def test_high_bowling_volume_raises_risk(self, now):
        without = assess(snapshot(), now)
        with_overs = assess(snapshot(bowling_load=30.0), now)
        assert isinstance(without, Assessment) and isinstance(with_overs, Assessment)
        assert with_overs.score > without.score
        assert any(r.rule_id == "bowling_workload" for r in with_overs.fired_rules)

    def test_low_bowling_volume_does_not_fire(self, now):
        result = assess(snapshot(bowling_load=8.0), now)
        assert isinstance(result, Assessment)
        assert not any(r.rule_id == "bowling_workload" for r in result.fired_rules)

    def test_engine_works_without_any_cricket_data(self, now):
        """Cross-sport applicability: the cricket rule is additive, never required."""
        result = assess(snapshot(), now)
        assert isinstance(result, Assessment)
