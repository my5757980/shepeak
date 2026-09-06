"""Assessment confidence (FR-023).

Confidence measures how much of the picture the engine actually had. It is driven by input
coverage and freshness — never by how emphatic a rule was. Below CONFIDENCE_FLOOR the score
is withheld (Principle IV).
"""

from __future__ import annotations

from datetime import datetime

from .types import FRESHNESS_WINDOWS, AthleteSnapshot, MetricKind

#: Each metric's contribution to full confidence. Required metrics carry more weight, but
#: sex-specific inputs carry real weight too: a score computed without them is genuinely
#: less trustworthy for a woman athlete, and Principle III means saying so rather than
#: quietly scoring as if a male-default baseline were adequate.
_WEIGHTS: dict[MetricKind, float] = {
    MetricKind.TRAINING_LOAD: 0.20,
    MetricKind.SLEEP: 0.15,
    MetricKind.SORENESS: 0.15,
    MetricKind.CYCLE_PHASE: 0.20,
    MetricKind.CONTRACEPTION_STATUS: 0.10,
    MetricKind.IRON_STATUS: 0.10,
    MetricKind.BOWLING_LOAD: 0.10,
}


def compute(snapshot: AthleteSnapshot, now: datetime) -> float:
    """Return confidence in [0.0, 1.0], rounded to 3 places for reproducibility.

    A present metric contributes its full weight when freshly captured, decaying linearly to
    half weight at the edge of its freshness window. Absent metrics contribute nothing.
    """
    total = 0.0
    for kind, weight in _WEIGHTS.items():
        metric = snapshot.get(kind)
        if metric is None:
            continue
        window = FRESHNESS_WINDOWS[kind].total_seconds()
        age = max(metric.age_at(now).total_seconds(), 0.0)
        if age > window:
            continue  # stale inputs contribute nothing; required ones already refused
        freshness = 1.0 - 0.5 * (age / window)
        total += weight * freshness
    return round(min(total, 1.0), 3)
