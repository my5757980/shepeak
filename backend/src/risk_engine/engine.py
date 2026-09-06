"""The deterministic risk engine entry point (FR-001, FR-013, FR-014).

`assess()` is a pure function: same snapshot, same clock, same rule set → same result, always
(SC-008). It returns either an Assessment carrying its own evidence, or a Refusal carrying its
own reason. It never returns a partial or best-guess score (FR-007).
"""

from __future__ import annotations

from datetime import datetime

from . import confidence, factors, freshness, rules
from .types import (
    CONFIDENCE_FLOOR,
    Assessment,
    AthleteSnapshot,
    EvidenceItem,
    Refusal,
    RefusalReason,
    Result,
    band_for_score,
)
from .version import rule_set_version


def _evidence_for(
    snapshot: AthleteSnapshot, fired: tuple, now: datetime
) -> tuple[EvidenceItem, ...]:
    """Evidence is the metrics the fired rules actually used — with values and capture times."""
    used: set[str] = set()
    for rule in fired:
        used.update(rule.inputs)
    items = [
        EvidenceItem(
            kind=metric.kind,
            value=metric.value,
            captured_at=metric.captured_at,
            age_hours=round(metric.age_at(now).total_seconds() / 3600, 2),
        )
        for kind, metric in sorted(snapshot.metrics.items(), key=lambda kv: kv[0].value)
        if kind.value in used
    ]
    return tuple(items)


def assess(snapshot: AthleteSnapshot, now: datetime) -> Result:
    """Assess injury risk, or refuse and say why.

    `now` is passed in rather than read from the clock so the function stays pure and its
    output reproducible (Principle I).
    """
    version = rule_set_version()

    # Fail closed on inputs before computing anything (Principle IV).
    refusal = freshness.check_inputs(snapshot, now, version)
    if refusal is not None:
        return refusal

    profile = factors.build_profile(snapshot)
    conf = confidence.compute(snapshot, now)

    if conf < CONFIDENCE_FLOOR:
        return Refusal(
            athlete_id=snapshot.athlete_id,
            reason=RefusalReason.LOW_CONFIDENCE,
            detail=(
                f"Confidence {conf:.3f} is below the {CONFIDENCE_FLOOR} threshold required "
                "to issue a risk score. "
                + (
                    "Missing: " + ", ".join(profile.absent) + "."
                    if profile.absent
                    else "Recorded data is too sparse or too old."
                )
            ),
            offending_inputs=profile.absent or ("insufficient_input_coverage",),
            computed_confidence=conf,
            rule_set_version=version,
            computed_at=now,
        )

    fired = rules.evaluate(snapshot, profile)
    score = min(sum(rule.points for rule in fired), 100)

    sex_specific_fired = tuple(
        rule.rule_id for rule in fired if rule.is_sex_specific
    )
    # SC-001: report the factors considered, which is broader than the rules that fired —
    # a factor examined and found benign is still evidence the score accounted for it.
    considered = profile.considered if profile.considered else ()

    return Assessment(
        athlete_id=snapshot.athlete_id,
        score=score,
        band=band_for_score(score),
        confidence=conf,
        rule_set_version=version,
        computed_at=now,
        evidence=_evidence_for(snapshot, fired, now),
        fired_rules=fired,
        sex_specific_factors_considered=considered + sex_specific_fired,
        # FR-017: absences are stated, never filled with a male-default value.
        absent_sex_specific_inputs=profile.absent,
    )
