"""T1.7 — mutation guard over the safety rules (Constitution Principle VIII).

An ordinary test suite proves the code does what it does. This proves the suite would
*notice* if a safety rule were silently removed or weakened — which is the failure mode that
actually happens: a rule deleted during a refactor, a threshold nudged to make a demo pass.

Rather than run a full mutation framework (slow, and it mutates code we do not care about),
this mutates the specific things the constitution protects and asserts the behaviour changes.
A mutation that produces identical behaviour means that rule is untested, and this fails.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest

from helpers import snapshot
from risk_engine import confidence, engine, rules
from risk_engine.types import CONFIDENCE_FLOOR, Assessment, Refusal


@contextmanager
def rule_removed(rule_id: str):
    """Temporarily delete one rule from the evaluation set."""
    original = rules.ALL_RULES
    rules.ALL_RULES = tuple(r for r in original if r.__name__ != f"rule_{rule_id}")
    assert len(rules.ALL_RULES) == len(original) - 1, f"rule_{rule_id} not found"
    try:
        yield
    finally:
        rules.ALL_RULES = original


#: (rule id, snapshot kwargs that should trigger it)
SAFETY_RULES = [
    ("load_spike", {"training_load": 160.0}),
    ("bowling_workload", {"bowling_load": 30.0}),
    ("sleep_debt", {"sleep": 5.0}),
    ("high_soreness", {"soreness": 9.0}),
    ("acl_cycle_phase", {"cycle_phase": "ovulatory"}),
    ("luteal_recovery", {"cycle_phase": "luteal"}),
    ("red_s", {"cycle_phase": "recorded_absent", "contraception_status": "false"}),
    ("iron_deficiency", {"iron_status": 15.0}),
]


class TestEveryRuleIsObservable:
    @pytest.mark.parametrize(("rule_id", "trigger"), SAFETY_RULES, ids=[r[0] for r in SAFETY_RULES])
    def test_removing_a_rule_changes_the_score(self, now, rule_id, trigger):
        """If deleting a rule leaves the score identical, nothing was testing that rule."""
        baseline = engine.assess(snapshot(**trigger), now)
        assert isinstance(baseline, Assessment)

        with rule_removed(rule_id):
            mutated = engine.assess(snapshot(**trigger), now)

        assert isinstance(mutated, Assessment)
        assert mutated.score < baseline.score, (
            f"removing rule_{rule_id} did not lower the score — it is not covered by any "
            f"assertion, so it could be deleted in a refactor without a test failing"
        )

    @pytest.mark.parametrize(("rule_id", "trigger"), SAFETY_RULES, ids=[r[0] for r in SAFETY_RULES])
    def test_removing_a_rule_removes_its_evidence(self, now, rule_id, trigger):
        """Principle VII: the rule's reasoning must disappear with the rule."""
        with rule_removed(rule_id):
            mutated = engine.assess(snapshot(**trigger), now)
        assert isinstance(mutated, Assessment)
        assert not any(r.rule_id.startswith(rule_id.split("_")[0]) for r in mutated.fired_rules
                       if r.rule_id in {"load_spike", "bowling_workload", "sleep_debt",
                                        "high_soreness", "acl_ovulatory_laxity",
                                        "luteal_recovery_cost", "red_s_amenorrhoea",
                                        "iron_deficiency"} and rule_id in r.rule_id)


class TestThresholdsAreLoadBearing:
    """Weakening a threshold must change behaviour. A threshold nothing depends on is decoration."""

    def test_raising_the_confidence_floor_causes_refusals(self, now):
        """The 0.7 floor must actually gate. If it does not, FR-023 is not enforced."""
        healthy = snapshot()
        assert isinstance(engine.assess(healthy, now), Assessment)

        original = engine.CONFIDENCE_FLOOR
        try:
            engine.CONFIDENCE_FLOOR = 0.999
            mutated = engine.assess(healthy, now)
        finally:
            engine.CONFIDENCE_FLOOR = original

        assert isinstance(mutated, Refusal), (
            "raising the confidence floor produced no refusal — the floor is not being applied"
        )
        assert mutated.reason.value == "low_confidence"

    def test_confidence_actually_varies_with_input_coverage(self, now):
        """A confidence value that never moves cannot gate anything."""
        full = confidence.compute(snapshot(), now)
        sparse = confidence.compute(
            snapshot(cycle_phase=None, iron_status=None, contraception_status=None), now
        )
        assert full > sparse, "confidence must fall when sex-specific inputs are missing"
        assert sparse < CONFIDENCE_FLOOR <= full

    def test_widening_a_freshness_window_stops_the_refusal(self, now):
        """Proves the window value drives the refusal, not some incidental check."""
        from datetime import timedelta

        from helpers import metric
        from risk_engine.types import FRESHNESS_WINDOWS, MetricKind

        stale = metric(MetricKind.SORENESS, 8.0, age=timedelta(hours=30))
        assert isinstance(engine.assess(snapshot(soreness=stale), now), Refusal)

        original = FRESHNESS_WINDOWS[MetricKind.SORENESS]
        try:
            FRESHNESS_WINDOWS[MetricKind.SORENESS] = timedelta(hours=72)
            widened = engine.assess(snapshot(soreness=stale), now)
        finally:
            FRESHNESS_WINDOWS[MetricKind.SORENESS] = original

        assert isinstance(widened, Assessment), (
            "widening the window did not stop the refusal — the window is not what gates it"
        )


class TestSexSpecificRulesCannotBeQuietlyDropped:
    """Principle III — the equity claim must be load-bearing, not decorative."""

    SEX_SPECIFIC = ["acl_cycle_phase", "luteal_recovery", "red_s", "iron_deficiency"]

    @pytest.mark.parametrize("rule_id", SEX_SPECIFIC)
    def test_dropping_a_female_specific_rule_is_detectable(self, now, rule_id):
        trigger = dict(next(t for r, t in SAFETY_RULES if r == rule_id))
        baseline = engine.assess(snapshot(**trigger), now)
        with rule_removed(rule_id):
            mutated = engine.assess(snapshot(**trigger), now)
        assert isinstance(baseline, Assessment) and isinstance(mutated, Assessment)
        assert baseline.score != mutated.score, (
            f"rule_{rule_id} models female physiology and contributes nothing measurable — "
            f"it could be removed without any test noticing, which would hollow out EQ-002"
        )
