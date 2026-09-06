"""T2.15, T3.8 — log scrubbing (FR-018) and the LLM boundary (FR-002, FR-003).

The boundary tests are the ones that matter most here. Principle I says the model may
explain but never decide; these assert that a narrative which disagrees with the verdict is
rejected, rather than trusting the model to behave.
"""

from __future__ import annotations

import logging

import pytest

from api.scrub import REDACTED, HealthDataFilter, scrub, scrub_obj
from explanation.narrator import explain, is_consistent


class TestScrubbing:
    """FR-018 — no raw health data in logs, traces, or error messages."""

    @pytest.mark.parametrize(
        "line",
        [
            "processing iron_status=17.0 for athlete",
            'row: {"cycle_phase": "recorded_absent"}',
            "soreness: 8 reported",
            "Metric(kind='sleep', value=5.9)",
            "training_load=155.0, bowling_load=24",
        ],
    )
    def test_values_are_redacted(self, line):
        out = scrub(line)
        assert REDACTED in out
        for leak in ("17.0", "recorded_absent", "8", "5.9", "155.0"):
            if leak in line:
                assert leak not in out.replace(REDACTED, ""), f"leaked {leak!r}: {out}"

    def test_metric_name_is_kept(self):
        """The key stays readable — debugging a stale-data bug needs to know which metric."""
        out = scrub("iron_status=17.0")
        assert "iron_status" in out

    def test_nested_structures_are_scrubbed(self):
        payload = {"athlete": "a-1", "metrics": [{"iron_status": 17.0, "sleep": 5.9}]}
        out = scrub_obj(payload)
        assert out["metrics"][0]["iron_status"] == REDACTED
        assert out["metrics"][0]["sleep"] == REDACTED
        assert out["athlete"] == "a-1", "non-health fields must survive"

    def test_empty_and_none_are_safe(self):
        assert scrub("") == ""
        assert scrub_obj(None) is None

    def test_logging_filter_redacts_a_real_record(self):
        f = HealthDataFilter()
        record = logging.LogRecord(
            "t", logging.ERROR, __file__, 1,
            "failed on iron_status=17.0", None, None,
        )
        f.filter(record)
        assert "17.0" not in str(record.msg)
        assert REDACTED in str(record.msg)

    def test_filter_never_lets_content_through_on_failure(self):
        class Exploding:
            def __str__(self):
                raise RuntimeError("boom")

        f = HealthDataFilter()
        record = logging.LogRecord("t", logging.ERROR, __file__, 1, Exploding(), None, None)
        assert f.filter(record) is True
        assert "withheld" in str(record.msg)


ASSESSED = {
    "outcome": "assessed", "score": 69, "band": "elevated", "confidence": 0.9,
    "requires_coach_approval": True, "rule_set_version": "rs-test",
    "fired_rules": [
        {"rule_id": "load_spike", "points": 15, "because": "Load is high.",
         "inputs": ["training_load"], "is_sex_specific": False, "rule_version": "1.0.0"},
        {"rule_id": "acl_ovulatory_laxity", "points": 15, "because": "Ovulatory phase.",
         "inputs": ["cycle_phase"], "is_sex_specific": True, "rule_version": "1.0.0"},
    ],
    "absent_sex_specific_inputs": [],
}


class TestExplanationIsBuiltFromTheComputation:
    """FR-014 — generated from the same result, not reconstructed from the score."""

    def test_narrative_quotes_the_fired_rules(self):
        out = explain(dict(ASSESSED))
        assert out is not None
        assert "Load is high." in out["text"]
        assert out["consistent"]

    def test_sex_specific_rules_are_called_out(self):
        out = explain(dict(ASSESSED))
        assert "female physiology" in out["text"]

    def test_absences_are_surfaced_to_the_athlete(self):
        data = {**ASSESSED, "absent_sex_specific_inputs": ["iron_status"]}
        out = explain(data)
        assert "No default value was substituted" in out["text"]

    def test_refusal_explains_itself(self):
        out = explain({"outcome": "refused", "reason": "stale_metric",
                       "detail": "soreness is 31.0h old.", "confidence": None})
        assert out is not None
        assert "31.0h" in out["text"]
        assert "escalated" in out["text"]


class TestBoundaryRecheck:
    """FR-003, T3.8 — a narrative that disagrees with the verdict is not returned.

    These simulate what a model could produce. The system must reject them on its own,
    without depending on the model having been well behaved.
    """

    def test_consistent_narrative_passes(self):
        assert is_consistent("Your injury risk is elevated right now.", ASSESSED)

    def test_narrative_claiming_a_different_band_is_rejected(self):
        assert not is_consistent("Your injury risk is low right now. Keep going.", ASSESSED)

    def test_narrative_denying_required_approval_is_rejected(self):
        assert not is_consistent(
            "Your injury risk is elevated. You do not need approval to start this.", ASSESSED
        )

    def test_narrative_inventing_a_different_score_is_rejected(self):
        assert not is_consistent(
            "Your injury risk is elevated, with a score of 20.", ASSESSED
        )

    def test_narrative_quoting_the_correct_score_passes(self):
        assert is_consistent(
            "Your injury risk is elevated, with a score of 69.", ASSESSED
        )

    def test_llm_cannot_change_the_score_through_the_narrative(self):
        """The model has no path to the number: `explain` receives an already-computed
        result and returns text. There is no writable field on the verdict."""
        data = dict(ASSESSED)
        out = explain(data)
        assert data["score"] == 69, "explain() must not mutate the result it explains"
        assert data["band"] == "elevated"
        assert out["source"] in {"deterministic"} or out["source"].startswith("claude") \
            or out["source"].startswith("gpt")
