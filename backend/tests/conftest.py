"""Shared fixtures. Every test pins `now` explicitly — the engine is pure and never reads a clock."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from risk_engine.types import AthleteSnapshot, Metric, MetricKind  # noqa: E402

NOW = datetime(2026, 9, 6, 12, 0, 0, tzinfo=timezone.utc)


def metric(kind: MetricKind, value, age: timedelta = timedelta(hours=1)) -> Metric:
    return Metric(kind=kind, value=value, captured_at=NOW - age)


def snapshot(
    *,
    athlete_id: str = "ath-001",
    baseline: float | None = 100.0,
    **overrides,
) -> AthleteSnapshot:
    """A healthy, fully-recorded athlete. Tests override only what they are exercising."""
    metrics = {
        MetricKind.TRAINING_LOAD: metric(MetricKind.TRAINING_LOAD, 100.0),
        MetricKind.SLEEP: metric(MetricKind.SLEEP, 8.0),
        MetricKind.SORENESS: metric(MetricKind.SORENESS, 2.0),
        MetricKind.CYCLE_PHASE: metric(MetricKind.CYCLE_PHASE, "follicular"),
        MetricKind.CONTRACEPTION_STATUS: metric(MetricKind.CONTRACEPTION_STATUS, "false"),
        MetricKind.IRON_STATUS: metric(MetricKind.IRON_STATUS, 55.0),
    }
    for kind, value in overrides.items():
        mk = MetricKind[kind.upper()]
        if value is None:
            metrics.pop(mk, None)
        elif isinstance(value, Metric):
            metrics[mk] = value
        else:
            metrics[mk] = metric(mk, value)
    return AthleteSnapshot(
        athlete_id=athlete_id, metrics=metrics, baseline_training_load=baseline
    )


@pytest.fixture
def now() -> datetime:
    return NOW
