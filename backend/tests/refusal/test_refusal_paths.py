"""Refusal-path tests — SA-001, SC-004, FR-006, FR-007.

Constitution Principle IV: missing data, stale data, or low confidence must withhold the
score and escalate with a stated reason. These tests assert the system refuses; the happy
path alone would be a blocking review finding.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from helpers import snapshot
from risk_engine.engine import assess
from risk_engine.types import Assessment, MetricKind, Refusal, RefusalReason


class TestMissingInputs:
    @pytest.mark.parametrize(
        "missing", ["training_load", "sleep", "soreness"]
    )
    def test_missing_required_metric_refuses(self, now, missing):
        result = assess(snapshot(**{missing: None}), now)
        assert isinstance(result, Refusal)
        assert result.reason is RefusalReason.MISSING_REQUIRED_METRIC
        assert missing in result.offending_inputs
        assert missing in result.detail
        assert result.escalates

    def test_no_baseline_refuses(self, now):
        """First-time athlete with no history — a load spike cannot be measured."""
        result = assess(snapshot(baseline=None), now)
        assert isinstance(result, Refusal)
        assert result.reason is RefusalReason.NO_BASELINE

    def test_refusal_names_the_reason_in_plain_language(self, now):
        result = assess(snapshot(sleep=None), now)
        assert isinstance(result, Refusal)
        assert result.detail.strip().endswith(".")
        assert "sleep" in result.detail


class TestStaleInputs:
    """FR-022 windows: training load 48h, sleep 24h, soreness 24h."""

    @pytest.mark.parametrize(
        ("kind", "window_hours"),
        [("training_load", 48), ("sleep", 24), ("soreness", 24)],
    )
    def test_stale_beyond_window_refuses(self, now, kind, window_hours):
        from helpers import metric

        mk = MetricKind[kind.upper()]
        aged = metric(mk, 100.0 if kind == "training_load" else 8.0,
                      age=timedelta(hours=window_hours + 1))
        result = assess(snapshot(**{kind: aged}), now)
        assert isinstance(result, Refusal)
        assert result.reason is RefusalReason.STALE_METRIC
        assert kind in result.offending_inputs

    def test_stale_refusal_states_how_stale(self, now):
        from helpers import metric

        aged = metric(MetricKind.SLEEP, 8.0, age=timedelta(hours=30))
        result = assess(snapshot(sleep=aged), now)
        assert isinstance(result, Refusal)
        assert "30.0h" in result.detail


class TestLowConfidence:
    def test_below_floor_refuses_and_reports_confidence(self, now):
        """FR-023: refuse below 0.7 and state the computed confidence."""
        result = assess(
            snapshot(cycle_phase=None, contraception_status=None, iron_status=None), now
        )
        assert isinstance(result, Refusal)
        assert result.reason is RefusalReason.LOW_CONFIDENCE
        assert result.computed_confidence is not None
        assert result.computed_confidence < 0.7
        assert "0.7" in result.detail

    def test_refusal_names_what_was_missing(self, now):
        result = assess(
            snapshot(cycle_phase=None, contraception_status=None, iron_status=None), now
        )
        assert isinstance(result, Refusal)
        assert "menstrual_cycle_phase" in result.offending_inputs


class TestNoDegradedOutput:
    """FR-007: never a partial or best-guess score."""

    def test_result_is_either_assessment_or_refusal_never_both(self, now):
        for snap in [snapshot(), snapshot(sleep=None), snapshot(baseline=None)]:
            result = assess(snap, now)
            assert isinstance(result, (Assessment, Refusal))
            if isinstance(result, Refusal):
                assert not hasattr(result, "score")
