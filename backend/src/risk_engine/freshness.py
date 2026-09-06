"""Freshness and required-input checks (FR-006, FR-022).

Fail closed: a missing or stale required input withholds the score. Nothing here guesses,
substitutes a default, or degrades gracefully.
"""

from __future__ import annotations

from datetime import datetime

from .types import AthleteSnapshot, MetricKind, Refusal, RefusalReason

#: Inputs without which no score may be produced at all.
REQUIRED_METRICS: tuple[MetricKind, ...] = (
    MetricKind.TRAINING_LOAD,
    MetricKind.SLEEP,
    MetricKind.SORENESS,
)


def check_inputs(
    snapshot: AthleteSnapshot, now: datetime, rule_set_version: str
) -> Refusal | None:
    """Return a Refusal if the snapshot cannot support a score, else None.

    Missing inputs are reported before stale ones: an athlete who has recorded nothing needs
    different guidance from one whose data has aged out.
    """
    missing = [k for k in REQUIRED_METRICS if snapshot.get(k) is None]
    if missing:
        return Refusal(
            athlete_id=snapshot.athlete_id,
            reason=RefusalReason.MISSING_REQUIRED_METRIC,
            detail=(
                "Cannot assess injury risk: "
                + ", ".join(k.value for k in missing)
                + " has not been recorded."
            ),
            offending_inputs=tuple(k.value for k in missing),
            computed_confidence=None,
            rule_set_version=rule_set_version,
            computed_at=now,
        )

    stale = []
    for kind in REQUIRED_METRICS:
        metric = snapshot.get(kind)
        assert metric is not None  # guarded by the missing check above
        if metric.is_stale_at(now):
            hours = metric.age_at(now).total_seconds() / 3600
            stale.append((kind, hours))

    if stale:
        detail = "; ".join(f"{k.value} is {h:.1f}h old" for k, h in stale)
        return Refusal(
            athlete_id=snapshot.athlete_id,
            reason=RefusalReason.STALE_METRIC,
            detail=f"Cannot assess injury risk: {detail}.",
            offending_inputs=tuple(k.value for k, _ in stale),
            computed_confidence=None,
            rule_set_version=rule_set_version,
            computed_at=now,
        )

    if snapshot.baseline_training_load is None:
        return Refusal(
            athlete_id=snapshot.athlete_id,
            reason=RefusalReason.NO_BASELINE,
            detail=(
                "Cannot assess injury risk: no training-load baseline exists yet for this "
                "athlete. A load spike cannot be measured without one."
            ),
            offending_inputs=("baseline_training_load",),
            computed_confidence=None,
            rule_set_version=rule_set_version,
            computed_at=now,
        )

    return None
