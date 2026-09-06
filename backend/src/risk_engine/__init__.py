"""Deterministic injury-risk engine for ShePeak.

PURE by constitutional requirement (Principle I): this package must not import from
`orchestrator`, `api`, `audit`, `consent`, `explanation`, or any network/LLM library.
The rule is enforced by tests/unit/test_import_boundary.py, not by convention.
"""

from .engine import assess
from .types import Assessment, AthleteSnapshot, Metric, MetricKind, Refusal, RiskBand

__all__ = [
    "assess",
    "Assessment",
    "AthleteSnapshot",
    "Metric",
    "MetricKind",
    "Refusal",
    "RiskBand",
]
