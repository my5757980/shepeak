"""Assessment flow: load → score → audit → respond.

The orchestrator is deliberately thin. It moves data between the database and the pure
engine, and it writes the audit entry BEFORE the caller can observe the result (FR-008).
It never adjusts a score, and it never turns a refusal into a partial answer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.db import Identity, request_transaction
from audit.writer import AuditEntry, write_entry
from risk_engine.engine import assess as engine_assess
from risk_engine.types import Assessment, AthleteSnapshot, Metric, MetricKind, Refusal

_LATEST_METRICS = """
    SELECT DISTINCT ON (kind) kind, value, captured_at, source
    FROM health_metric
    WHERE athlete_id = %s
    ORDER BY kind, captured_at DESC
"""

_BASELINE = """
    SELECT avg(value::numeric)::float AS baseline
    FROM health_metric
    WHERE athlete_id = %s
      AND kind = 'training_load'
      AND captured_at < now() - interval '7 days'
      AND captured_at > now() - interval '35 days'
"""


def load_snapshot(conn, athlete_id: str) -> AthleteSnapshot:
    """Read the athlete's current picture. RLS decides what is visible, not this query."""
    metrics: dict[MetricKind, Metric] = {}
    with conn.cursor() as cur:
        cur.execute(_LATEST_METRICS, (athlete_id,))
        for row in cur.fetchall():
            kind = MetricKind(row["kind"])
            raw = row["value"]
            value: float | str
            try:
                value = float(raw)
            except (TypeError, ValueError):
                value = str(raw)
            metrics[kind] = Metric(
                kind=kind,
                value=value,
                captured_at=row["captured_at"],
                source=row["source"],
            )

        cur.execute(_BASELINE, (athlete_id,))
        row = cur.fetchone()
        baseline = row["baseline"] if row else None

    return AthleteSnapshot(
        athlete_id=athlete_id, metrics=metrics, baseline_training_load=baseline
    )


def _persist(conn, result: Assessment | Refusal) -> str:
    """Store the assessment or the refusal. Both are records; neither is discarded."""
    with conn.cursor() as cur:
        if isinstance(result, Assessment):
            cur.execute(
                """INSERT INTO risk_assessment
                     (athlete_id, score, band, confidence, rule_set_version,
                      evidence, fired_rules, computed_at)
                   VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s) RETURNING id""",
                (
                    result.athlete_id, result.score, result.band.value, result.confidence,
                    result.rule_set_version,
                    _json(result.evidence), _json(result.fired_rules), result.computed_at,
                ),
            )
        else:
            cur.execute(
                """INSERT INTO risk_assessment
                     (athlete_id, refusal_reason, refusal_detail, confidence,
                      rule_set_version, computed_at)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    result.athlete_id, result.reason.value, result.detail,
                    result.computed_confidence, result.rule_set_version, result.computed_at,
                ),
            )
        return str(cur.fetchone()["id"])


def _escalate(conn, refusal: Refusal, routed_to: str) -> None:
    """SA-001: every refusal escalates to a human."""
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO escalation (athlete_id, reason, detail, routed_to)
               VALUES (%s,%s,%s,%s)""",
            (refusal.athlete_id, refusal.reason.value, refusal.detail, routed_to),
        )


def _json(obj: Any) -> str:
    import json
    from dataclasses import asdict, is_dataclass

    def default(o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)

    if isinstance(obj, tuple):
        obj = [default(o) if is_dataclass(o) else o for o in obj]
    return json.dumps(obj, default=default, sort_keys=True)


def run(identity: Identity, athlete_id: str) -> dict[str, Any]:
    """Assess one athlete. Returns a serialisable result, refusal included."""
    now = datetime.now(timezone.utc)

    with request_transaction(identity) as conn:
        snapshot = load_snapshot(conn, athlete_id)

        if not snapshot.metrics:
            # Either no data, or consent/RLS filtered everything. Both fail closed, and we
            # deliberately do NOT distinguish them to the caller — saying "this athlete
            # exists but you may not see her" is itself a disclosure.
            refusal = Refusal(
                athlete_id=athlete_id,
                reason=__import__(
                    "risk_engine.types", fromlist=["RefusalReason"]
                ).RefusalReason.MISSING_REQUIRED_METRIC,
                detail="No accessible health data for this athlete.",
                offending_inputs=("all",),
                computed_confidence=None,
                rule_set_version="n/a",
                computed_at=now,
            )
            result: Assessment | Refusal = refusal
            assessment_id = None
        else:
            result = engine_assess(snapshot, now)
            assessment_id = _persist(conn, result)
            if isinstance(result, Refusal):
                _escalate(conn, result, routed_to="coach")

    # FR-008: the audit entry is committed on its own connection before the caller sees
    # anything (ADR-0001 condition 5 — a refusal must survive a rolled-back request).
    write_entry(
        AuditEntry(
            actor_id=identity.athlete_id or identity.coach_id or "unknown",
            actor_role=identity.role,
            action="risk_assessed" if isinstance(result, Assessment) else "risk_refused",
            subject_id=athlete_id,
            payload=_payload(result, assessment_id),
            rule_set_version=result.rule_set_version,
        )
    )
    return serialise(result, assessment_id)


def _payload(result: Assessment | Refusal, assessment_id: str | None) -> dict[str, Any]:
    if isinstance(result, Assessment):
        return {
            "assessment_id": assessment_id,
            "score": result.score,
            "band": result.band.value,
            "confidence": result.confidence,
            "rules": [r.rule_id for r in result.fired_rules],
        }
    return {
        "assessment_id": assessment_id,
        "refused": True,
        "reason": result.reason.value,
        "confidence": result.computed_confidence,
    }


def serialise(result: Assessment | Refusal, assessment_id: str | None = None) -> dict[str, Any]:
    if isinstance(result, Refusal):
        return {
            "outcome": "refused",
            "assessment_id": assessment_id,
            "reason": result.reason.value,
            "detail": result.detail,
            "offending_inputs": list(result.offending_inputs),
            "confidence": result.computed_confidence,
            "rule_set_version": result.rule_set_version,
            "escalated": result.escalates,
            "computed_at": result.computed_at.isoformat(),
        }
    return {
        "outcome": "assessed",
        "assessment_id": assessment_id,
        "score": result.score,
        "band": result.band.value,
        "requires_coach_approval": result.requires_coach_approval,
        "confidence": result.confidence,
        "rule_set_version": result.rule_set_version,
        "computed_at": result.computed_at.isoformat(),
        "evidence": [
            {
                "kind": e.kind.value,
                "value": e.value,
                "captured_at": e.captured_at.isoformat(),
                "age_hours": e.age_hours,
            }
            for e in result.evidence
        ],
        "fired_rules": [
            {
                "rule_id": r.rule_id,
                "rule_version": r.rule_version,
                "points": r.points,
                "because": r.because,
                "inputs": list(r.inputs),
                "is_sex_specific": r.is_sex_specific,
            }
            for r in result.fired_rules
        ],
        "sex_specific_factors_considered": list(result.sex_specific_factors_considered),
        "absent_sex_specific_inputs": list(result.absent_sex_specific_inputs),
    }
