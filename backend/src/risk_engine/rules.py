"""Deterministic injury-risk rules (FR-001).

Every rule is a pure function of the snapshot and the sex-specific profile. Each returns a
FiredRule carrying the points it contributed, the evidence it used, and why — so the score's
explanation is produced by the same computation that produced the score (FR-014).

Thresholds here are PROVISIONAL engineering defaults requiring sports-science validation
before any non-prototype use. They are deliberately in code, reviewed and tested, rather
than in runtime configuration (Constitution: Safety and Compliance Constraints).
"""

from __future__ import annotations

from collections.abc import Callable

from .factors import SexSpecificProfile
from .types import AthleteSnapshot, CycleState, FiredRule, MetricKind

RULE_VERSION = "1.0.0"

# --- Load rules -------------------------------------------------------------------------

#: Acute:chronic workload ratio above this is the classic injury-risk spike.
ACWR_SPIKE = 1.5
ACWR_HIGH = 1.3


def rule_load_spike(snapshot: AthleteSnapshot, profile: SexSpecificProfile) -> FiredRule | None:
    metric = snapshot.get(MetricKind.TRAINING_LOAD)
    baseline = snapshot.baseline_training_load
    if metric is None or not baseline:
        return None
    ratio = float(metric.value) / baseline
    if ratio >= ACWR_SPIKE:
        points = 30
        because = f"Training load is {ratio:.2f}x baseline (spike threshold {ACWR_SPIKE})."
    elif ratio >= ACWR_HIGH:
        points = 15
        because = f"Training load is {ratio:.2f}x baseline (elevated above {ACWR_HIGH})."
    else:
        return None
    return FiredRule(
        rule_id="load_spike",
        rule_version=RULE_VERSION,
        points=points,
        because=because,
        inputs=("training_load", "baseline_training_load"),
    )


#: Cricket bowling workload (FR-026). Consecutive high-volume spells drive bowling injuries.
BOWLING_OVERS_HIGH = 20.0


def rule_bowling_workload(
    snapshot: AthleteSnapshot, profile: SexSpecificProfile
) -> FiredRule | None:
    metric = snapshot.get(MetricKind.BOWLING_LOAD)
    if metric is None:
        return None
    overs = float(metric.value)
    if overs < BOWLING_OVERS_HIGH:
        return None
    points = 20 if overs >= BOWLING_OVERS_HIGH * 1.5 else 12
    return FiredRule(
        rule_id="bowling_workload",
        rule_version=RULE_VERSION,
        points=points,
        because=(
            f"{overs:.0f} overs bowled in the current window "
            f"(high-volume threshold {BOWLING_OVERS_HIGH:.0f})."
        ),
        inputs=("bowling_load",),
    )


# --- Recovery rules ---------------------------------------------------------------------

SLEEP_LOW_HOURS = 6.5
SORENESS_HIGH = 7.0  # 0-10 self-reported


def rule_sleep_debt(snapshot: AthleteSnapshot, profile: SexSpecificProfile) -> FiredRule | None:
    metric = snapshot.get(MetricKind.SLEEP)
    if metric is None:
        return None
    hours = float(metric.value)
    if hours >= SLEEP_LOW_HOURS:
        return None
    return FiredRule(
        rule_id="sleep_debt",
        rule_version=RULE_VERSION,
        points=15,
        because=f"Sleep {hours:.1f}h is below the {SLEEP_LOW_HOURS}h recovery threshold.",
        inputs=("sleep",),
    )


def rule_high_soreness(
    snapshot: AthleteSnapshot, profile: SexSpecificProfile
) -> FiredRule | None:
    metric = snapshot.get(MetricKind.SORENESS)
    if metric is None:
        return None
    soreness = float(metric.value)
    if soreness < SORENESS_HIGH:
        return None
    return FiredRule(
        rule_id="high_soreness",
        rule_version=RULE_VERSION,
        points=12,
        because=f"Self-reported soreness {soreness:.0f}/10 at or above {SORENESS_HIGH:.0f}.",
        inputs=("soreness",),
    )


# --- Sex-specific rules (FR-015) --------------------------------------------------------


def rule_acl_cycle_phase(
    snapshot: AthleteSnapshot, profile: SexSpecificProfile
) -> FiredRule | None:
    """ACL injury mechanics vary across the cycle.

    Ligament laxity rises around the ovulatory phase under oestrogen, and the literature
    associates that window with elevated ACL injury incidence in women athletes. A
    male-default model has no equivalent of this rule at all — which is the point.
    """
    if profile.cycle_state is not CycleState.OVULATORY:
        return None
    return FiredRule(
        rule_id="acl_ovulatory_laxity",
        rule_version=RULE_VERSION,
        points=15,
        because=(
            "Ovulatory phase: raised oestrogen is associated with increased ligament "
            "laxity and elevated ACL injury risk."
        ),
        inputs=("cycle_phase",),
        is_sex_specific=True,
    )


def rule_luteal_recovery(
    snapshot: AthleteSnapshot, profile: SexSpecificProfile
) -> FiredRule | None:
    if profile.cycle_state is not CycleState.LUTEAL:
        return None
    return FiredRule(
        rule_id="luteal_recovery_cost",
        rule_version=RULE_VERSION,
        points=8,
        because=(
            "Late luteal phase: raised core temperature and cardiovascular strain increase "
            "the recovery cost of the same training load."
        ),
        inputs=("cycle_phase",),
        is_sex_specific=True,
    )


def rule_red_s(snapshot: AthleteSnapshot, profile: SexSpecificProfile) -> FiredRule | None:
    """Recorded absence of menses without contraception — a RED-S signal (FR-016)."""
    if not profile.red_s_indicated:
        return None
    return FiredRule(
        rule_id="red_s_amenorrhoea",
        rule_version=RULE_VERSION,
        points=25,
        because=(
            "Menstruation recorded as absent while not on hormonal contraception — a "
            "Relative Energy Deficiency in Sport (RED-S) indicator carrying bone-stress "
            "injury risk."
        ),
        inputs=("cycle_phase", "contraception_status"),
        is_sex_specific=True,
    )


def rule_iron_deficiency(
    snapshot: AthleteSnapshot, profile: SexSpecificProfile
) -> FiredRule | None:
    if not profile.iron_deficient:
        return None
    assert profile.iron_status is not None
    return FiredRule(
        rule_id="iron_deficiency",
        rule_version=RULE_VERSION,
        points=12,
        because=(
            f"Serum ferritin {profile.iron_status:.0f} ng/mL is below the 30 ng/mL athlete "
            "threshold, impairing oxygen transport and recovery."
        ),
        inputs=("iron_status",),
        is_sex_specific=True,
    )


#: Evaluation order is fixed so the fired-rule sequence is deterministic (FR-001).
ALL_RULES: tuple[Callable[[AthleteSnapshot, SexSpecificProfile], FiredRule | None], ...] = (
    rule_load_spike,
    rule_bowling_workload,
    rule_sleep_debt,
    rule_high_soreness,
    rule_acl_cycle_phase,
    rule_luteal_recovery,
    rule_red_s,
    rule_iron_deficiency,
)


def evaluate(
    snapshot: AthleteSnapshot, profile: SexSpecificProfile
) -> tuple[FiredRule, ...]:
    """Run every rule in fixed order and return those that fired."""
    return tuple(fired for rule in ALL_RULES if (fired := rule(snapshot, profile)) is not None)
