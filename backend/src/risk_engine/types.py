"""Value types for the deterministic risk engine.

This module — and every module in `risk_engine` — is PURE (Constitution Principle I):
no network, no database, no LLM, no clock reads outside what is passed in. Determinism is
the guarantee, so time must always arrive as an argument, never be read from the environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class MetricKind(str, Enum):
    """Metrics the engine understands. Freshness windows are defined per kind (FR-022)."""

    TRAINING_LOAD = "training_load"
    BOWLING_LOAD = "bowling_load"  # cricket-specific, FR-026
    SLEEP = "sleep"
    SORENESS = "soreness"
    CYCLE_PHASE = "cycle_phase"
    CONTRACEPTION_STATUS = "contraception_status"
    IRON_STATUS = "iron_status"


#: Freshness windows, measured from capture time (FR-022, FR-024).
FRESHNESS_WINDOWS: dict[MetricKind, timedelta] = {
    MetricKind.TRAINING_LOAD: timedelta(hours=48),
    MetricKind.BOWLING_LOAD: timedelta(hours=48),
    MetricKind.SLEEP: timedelta(hours=24),
    MetricKind.SORENESS: timedelta(hours=24),
    MetricKind.CYCLE_PHASE: timedelta(days=7),
    MetricKind.CONTRACEPTION_STATUS: timedelta(days=90),
    MetricKind.IRON_STATUS: timedelta(days=90),
}

#: Confidence below this floor means refuse (FR-023).
CONFIDENCE_FLOOR = 0.7


class CycleState(str, Enum):
    """Three distinct cycle states (FR-016).

    These must never be collapsed into a single "missing" case. Absent menses is a RED-S
    signal, not an absence of signal, and a cycle suppressed by hormonal contraception is a
    modelled physiological state rather than missing data.
    """

    NOT_RECORDED = "not_recorded"
    RECORDED_ABSENT = "recorded_absent"
    SUPPRESSED_BY_CONTRACEPTION = "suppressed_by_contraception"
    MENSTRUAL = "menstrual"
    FOLLICULAR = "follicular"
    OVULATORY = "ovulatory"
    LUTEAL = "luteal"

    @property
    def is_cycling(self) -> bool:
        return self in {
            CycleState.MENSTRUAL,
            CycleState.FOLLICULAR,
            CycleState.OVULATORY,
            CycleState.LUTEAL,
        }


class RiskBand(str, Enum):
    """Risk bands. Boundaries are PROVISIONAL engineering defaults (spec Assumptions).

    The tiering rule in FR-021 is fixed; these numbers require sports-science validation
    before any non-prototype use.
    """

    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"

    @property
    def requires_coach_approval(self) -> bool:
        """FR-021: coach approval is mandatory at elevated and above."""
        return self in {RiskBand.ELEVATED, RiskBand.HIGH}


#: Provisional band boundaries — see spec Assumptions. Upper bound inclusive.
BAND_BOUNDARIES: tuple[tuple[int, RiskBand], ...] = (
    (39, RiskBand.LOW),
    (59, RiskBand.MODERATE),
    (79, RiskBand.ELEVATED),
    (100, RiskBand.HIGH),
)


def band_for_score(score: int) -> RiskBand:
    for upper, band in BAND_BOUNDARIES:
        if score <= upper:
            return band
    return RiskBand.HIGH


class RefusalReason(str, Enum):
    """Machine-readable refusal reasons (FR-006). Every refusal names one."""

    MISSING_REQUIRED_METRIC = "missing_required_metric"
    STALE_METRIC = "stale_metric"
    LOW_CONFIDENCE = "low_confidence"
    NO_BASELINE = "no_baseline"
    OUT_OF_SCOPE_MEDICAL = "out_of_scope_medical"


@dataclass(frozen=True)
class Metric:
    """One captured measurement.

    `captured_at` is when the measurement was taken; ingestion time lives in the persistence
    layer. Staleness is always measured against capture time (FR-024).
    """

    kind: MetricKind
    value: float | str
    captured_at: datetime
    source: str = "manual"

    def age_at(self, now: datetime) -> timedelta:
        return now - self.captured_at

    def is_stale_at(self, now: datetime) -> bool:
        return self.age_at(now) > FRESHNESS_WINDOWS[self.kind]


@dataclass(frozen=True)
class AthleteSnapshot:
    """Everything the engine is allowed to see about one athlete at one moment."""

    athlete_id: str
    metrics: dict[MetricKind, Metric]
    baseline_training_load: float | None = None
    sport: str = "cricket"

    def get(self, kind: MetricKind) -> Metric | None:
        return self.metrics.get(kind)


@dataclass(frozen=True)
class FiredRule:
    """A rule that contributed to a score, with the evidence it used (FR-013, SA-004)."""

    rule_id: str
    rule_version: str
    points: int
    because: str
    inputs: tuple[str, ...]
    is_sex_specific: bool = False


@dataclass(frozen=True)
class EvidenceItem:
    """One input metric as it stood, with its capture time (FR-013)."""

    kind: MetricKind
    value: float | str
    captured_at: datetime
    age_hours: float


@dataclass(frozen=True)
class Assessment:
    """A successful risk assessment.

    Evidence is part of this value, produced by the same computation that produced the score
    (FR-014). It is never reconstructed afterwards.
    """

    athlete_id: str
    score: int
    band: RiskBand
    confidence: float
    rule_set_version: str
    computed_at: datetime
    evidence: tuple[EvidenceItem, ...]
    fired_rules: tuple[FiredRule, ...]
    sex_specific_factors_considered: tuple[str, ...]
    absent_sex_specific_inputs: tuple[str, ...] = field(default=())

    @property
    def requires_coach_approval(self) -> bool:
        return self.band.requires_coach_approval

    @property
    def cites_sex_specific_factor(self) -> bool:
        """SC-001: with data present, a score must cite at least one sex-specific factor."""
        return len(self.sex_specific_factors_considered) > 0


@dataclass(frozen=True)
class Refusal:
    """A withheld assessment (FR-006, FR-007).

    A refusal is a first-class result, not an exception. It carries why, what was at fault,
    and the computed confidence so the athlete and coach can act on it.
    """

    athlete_id: str
    reason: RefusalReason
    detail: str
    offending_inputs: tuple[str, ...]
    computed_confidence: float | None
    rule_set_version: str
    computed_at: datetime

    @property
    def escalates(self) -> bool:
        """SA-001: every refusal escalates to a human."""
        return True


#: The engine returns one or the other. Never a partial or best-guess score (FR-007).
Result = Assessment | Refusal
