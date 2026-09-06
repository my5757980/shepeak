"""Principle III tests — the equity claim, made checkable.

These are the tests that distinguish ShePeak from a generic load monitor. If they pass on a
male-default model, they are not testing anything.
"""

from __future__ import annotations

import pytest

from conftest import snapshot
from risk_engine.engine import assess
from risk_engine.factors import build_profile
from risk_engine.types import Assessment, CycleState


class TestThreeCycleStates:
    """FR-016: not recorded / recorded absent / suppressed by contraception are distinct."""

    def test_not_recorded_is_not_absent(self):
        profile = build_profile(snapshot(cycle_phase=None, contraception_status="false"))
        assert profile.cycle_state is CycleState.NOT_RECORDED
        assert not profile.red_s_indicated, "absence of data must not imply absence of menses"

    def test_recorded_absent_flags_red_s(self):
        profile = build_profile(
            snapshot(cycle_phase="recorded_absent", contraception_status="false")
        )
        assert profile.cycle_state is CycleState.RECORDED_ABSENT
        assert profile.red_s_indicated, "recorded amenorrhoea is a RED-S signal"

    def test_contraception_suppression_is_not_red_s(self):
        """Absence explained by contraception is a modelled state, not a warning sign."""
        profile = build_profile(
            snapshot(cycle_phase="recorded_absent", contraception_status="true")
        )
        assert profile.cycle_state is CycleState.SUPPRESSED_BY_CONTRACEPTION
        assert not profile.red_s_indicated

    def test_the_three_states_are_never_equal(self):
        states = {
            build_profile(snapshot(cycle_phase=None, contraception_status="false")).cycle_state,
            build_profile(
                snapshot(cycle_phase="recorded_absent", contraception_status="false")
            ).cycle_state,
            build_profile(
                snapshot(cycle_phase="recorded_absent", contraception_status="true")
            ).cycle_state,
        }
        assert len(states) == 3, "collapsing these states is a clinical error (FR-016)"


class TestNoMaleDefaultSubstitution:
    """FR-017 / SC-002: an absent sex-specific input is stated, never defaulted."""

    def test_absent_input_is_reported_not_filled(self, now):
        result = assess(snapshot(iron_status=None), now)
        assert isinstance(result, Assessment)
        assert "iron_status" in result.absent_sex_specific_inputs
        assert not any(r.rule_id == "iron_deficiency" for r in result.fired_rules), (
            "a missing iron value must not be substituted with a default that fires a rule"
        )

    def test_missing_cycle_data_does_not_invent_a_phase(self, now):
        result = assess(snapshot(cycle_phase=None), now)
        if isinstance(result, Assessment):
            assert "menstrual_cycle_phase" in result.absent_sex_specific_inputs
            assert not any(
                r.rule_id in {"acl_ovulatory_laxity", "luteal_recovery_cost"}
                for r in result.fired_rules
            )


class TestSexSpecificCitation:
    """SC-001 / EQ-001: with data present, every score cites a sex-specific factor."""

    def test_score_cites_sex_specific_factor(self, now):
        result = assess(snapshot(), now)
        assert isinstance(result, Assessment)
        assert result.cites_sex_specific_factor
        assert "menstrual_cycle_phase" in result.sex_specific_factors_considered

    @pytest.mark.parametrize("phase", ["menstrual", "follicular", "ovulatory", "luteal"])
    def test_every_cycle_phase_is_considered(self, now, phase):
        result = assess(snapshot(cycle_phase=phase), now)
        assert isinstance(result, Assessment)
        assert result.cites_sex_specific_factor


class TestSexSpecificRulesActuallyFire:
    def test_ovulatory_phase_raises_acl_risk(self, now):
        baseline = assess(snapshot(cycle_phase="follicular"), now)
        ovulatory = assess(snapshot(cycle_phase="ovulatory"), now)
        assert isinstance(baseline, Assessment) and isinstance(ovulatory, Assessment)
        assert ovulatory.score > baseline.score
        assert any(r.rule_id == "acl_ovulatory_laxity" for r in ovulatory.fired_rules)

    def test_red_s_is_the_heaviest_single_sex_specific_rule(self, now):
        result = assess(
            snapshot(cycle_phase="recorded_absent", contraception_status="false"), now
        )
        assert isinstance(result, Assessment)
        red_s = next(r for r in result.fired_rules if r.rule_id == "red_s_amenorrhoea")
        assert red_s.points == 25
        assert "RED-S" in red_s.because

    def test_low_ferritin_fires_iron_rule(self, now):
        result = assess(snapshot(iron_status=18.0), now)
        assert isinstance(result, Assessment)
        assert any(r.rule_id == "iron_deficiency" for r in result.fired_rules)
