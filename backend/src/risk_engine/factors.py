"""Sex-specific physiological factors (FR-015, FR-016, FR-017).

These are first-class inputs, not adjustments layered onto a male-default baseline. Where a
factor is absent, this module reports the absence — it never substitutes a default value
(FR-017). That distinction is the whole point: a male-default baseline applied silently is
exactly the failure ShePeak exists to correct.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import AthleteSnapshot, CycleState, MetricKind


@dataclass(frozen=True)
class SexSpecificProfile:
    """What the engine could establish about sex-specific physiology for this athlete."""

    cycle_state: CycleState
    on_contraception: bool | None
    iron_status: float | None  # serum ferritin, ng/mL
    considered: tuple[str, ...]
    absent: tuple[str, ...]

    @property
    def red_s_indicated(self) -> bool:
        """RED-S risk indicator.

        Recorded absence of menses in an athlete NOT on hormonal contraception is a
        recognised Relative Energy Deficiency in Sport signal. This is precisely why
        FR-016 forbids collapsing "recorded absent" into "not recorded" — the same
        database null would hide a clinically meaningful finding.
        """
        return (
            self.cycle_state is CycleState.RECORDED_ABSENT
            and self.on_contraception is not True
        )

    @property
    def iron_deficient(self) -> bool:
        """Ferritin below 30 ng/mL — a commonly used threshold for athletes."""
        return self.iron_status is not None and self.iron_status < 30.0


def _resolve_cycle_state(snapshot: AthleteSnapshot, on_contraception: bool | None) -> CycleState:
    """Resolve the cycle state, keeping the three non-cycling cases distinct (FR-016)."""
    metric = snapshot.get(MetricKind.CYCLE_PHASE)
    if metric is None:
        # Not recorded is not the same as absent. If contraception is known to suppress the
        # cycle, say so rather than reporting a silent gap.
        if on_contraception is True:
            return CycleState.SUPPRESSED_BY_CONTRACEPTION
        return CycleState.NOT_RECORDED

    raw = str(metric.value)
    try:
        state = CycleState(raw)
    except ValueError:
        return CycleState.NOT_RECORDED

    if state is CycleState.RECORDED_ABSENT and on_contraception is True:
        # Absence explained by contraception is a modelled state, not a RED-S signal.
        return CycleState.SUPPRESSED_BY_CONTRACEPTION
    return state


def build_profile(snapshot: AthleteSnapshot) -> SexSpecificProfile:
    """Build the sex-specific profile, recording what was considered and what was absent."""
    considered: list[str] = []
    absent: list[str] = []

    contraception_metric = snapshot.get(MetricKind.CONTRACEPTION_STATUS)
    if contraception_metric is None:
        on_contraception = None
        absent.append("hormonal_contraception_status")
    else:
        on_contraception = str(contraception_metric.value).lower() in {"true", "yes", "1"}
        considered.append("hormonal_contraception_status")

    cycle_state = _resolve_cycle_state(snapshot, on_contraception)
    if cycle_state is CycleState.NOT_RECORDED:
        absent.append("menstrual_cycle_phase")
    else:
        considered.append("menstrual_cycle_phase")

    iron_metric = snapshot.get(MetricKind.IRON_STATUS)
    if iron_metric is None:
        iron_status = None
        absent.append("iron_status")
    else:
        iron_status = float(iron_metric.value)
        considered.append("iron_status")

    profile = SexSpecificProfile(
        cycle_state=cycle_state,
        on_contraception=on_contraception,
        iron_status=iron_status,
        considered=tuple(considered),
        absent=tuple(absent),
    )

    # RED-S is derived, so it is only "considered" once the inputs support deriving it.
    if cycle_state is not CycleState.NOT_RECORDED:
        profile = SexSpecificProfile(
            cycle_state=profile.cycle_state,
            on_contraception=profile.on_contraception,
            iron_status=profile.iron_status,
            considered=profile.considered + ("red_s_risk_indicators",),
            absent=profile.absent,
        )
    return profile
