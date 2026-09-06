"""Plan proposal and the approval decision (FR-004, FR-005, FR-021, Principle II).

Plans are generated deterministically from the risk band. The language model is not
involved: a training prescription is a safety-critical decision, and Principle I keeps
those in code.
"""

from __future__ import annotations

import json
from typing import Any

from api.db import Identity, request_transaction
from audit.writer import AuditEntry, write_entry
from orchestrator import assess as flow
from orchestrator.approval import (
    ApprovalContext,
    ApproverRole,
    evaluate,
    plan_content_hash,
)
from risk_engine.types import Assessment, RiskBand

#: Deterministic plan templates keyed by band. Load reduction is a prescription, so the
#: numbers live in reviewed code rather than in a model's output.
_TEMPLATES: dict[RiskBand, dict[str, Any]] = {
    RiskBand.LOW: {
        "load_change_pct": 0,
        "headline": "Continue as planned",
        "sessions": ["Normal training week", "Maintain current load", "Keep logging daily"],
    },
    RiskBand.MODERATE: {
        "load_change_pct": -10,
        "headline": "Small reduction and closer monitoring",
        "sessions": ["Reduce volume ~10%", "Add one full rest day", "Prioritise sleep"],
    },
    RiskBand.ELEVATED: {
        "load_change_pct": -25,
        "headline": "Meaningful deload — coach approval required",
        "sessions": [
            "Reduce volume ~25%",
            "Replace one high-intensity session with technical work",
            "Two consecutive nights of 8h+ sleep",
        ],
    },
    RiskBand.HIGH: {
        "load_change_pct": -40,
        "headline": "Substantial deload — coach approval required",
        "sessions": [
            "Reduce volume ~40%",
            "No high-intensity or high-impact work this week",
            "Review with coach before returning to full training",
        ],
    },
}


def _build_content(assessment: dict[str, Any]) -> dict[str, Any]:
    band = RiskBand(assessment["band"])
    template = dict(_TEMPLATES[band])
    template["derived_from_band"] = band.value
    template["derived_from_score"] = assessment["score"]
    template["rule_set_version"] = assessment["rule_set_version"]
    # The plan cites the same evidence as the score — a coach approving it sees why.
    template["because"] = [r["because"] for r in assessment.get("fired_rules", [])]
    return template


def current_or_new(identity: Identity, athlete_id: str) -> dict[str, Any]:
    """Return the athlete's live proposal, creating one from the current assessment.

    A proposal is always created inactive (FR-004). Nothing here can activate a plan.
    """
    assessment = flow.run(identity, athlete_id)
    if assessment["outcome"] != "assessed":
        # Fail closed: no score, no plan. A plan built on withheld data is exactly the
        # best-guess output Principle IV forbids.
        return {"outcome": "no_plan", "reason": assessment["reason"],
                "detail": assessment["detail"]}

    content = _build_content(assessment)
    content_hash = plan_content_hash(content)

    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, version, content, content_hash, state
                   FROM plan_proposal
                   WHERE athlete_id = %s AND state = 'proposed'
                   ORDER BY created_at DESC LIMIT 1""",
                (athlete_id,),
            )
            existing = cur.fetchone()

            if existing and existing["content_hash"] == content_hash:
                plan = existing
            else:
                if existing:
                    # FR-005: the underlying assessment changed, so the old proposal — and
                    # any approval bound to it — no longer applies.
                    cur.execute(
                        "UPDATE plan_proposal SET state='superseded' WHERE id=%s",
                        (existing["id"],),
                    )
                cur.execute(
                    """INSERT INTO plan_proposal
                         (athlete_id, assessment_id, version, content, content_hash)
                       VALUES (%s,%s,%s,%s::jsonb,%s)
                       RETURNING id, version, content, content_hash, state""",
                    (
                        athlete_id,
                        assessment["assessment_id"],
                        (existing["version"] + 1) if existing else 1,
                        json.dumps(content, sort_keys=True),
                        content_hash,
                    ),
                )
                plan = cur.fetchone()

    return {
        "outcome": "proposed",
        "plan_id": str(plan["id"]),
        "version": plan["version"],
        "state": plan["state"],
        "content": plan["content"],
        "content_hash": plan["content_hash"],
        "band": assessment["band"],
        "requires_coach_approval": assessment["requires_coach_approval"],
        "assessment": assessment,
    }


def decide(identity: Identity, plan_id: str, decision: str) -> dict[str, Any]:
    """Approve or reject. Every outcome — including a denial — is audited."""
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.id, p.athlete_id, p.state, p.content, p.content_hash,
                          a.coach_id, r.band
                   FROM plan_proposal p
                   JOIN athlete a ON a.id = p.athlete_id
                   JOIN risk_assessment r ON r.id = p.assessment_id
                   WHERE p.id = %s""",
                (plan_id,),
            )
            plan = cur.fetchone()

            if plan is None:
                return {"allowed": False, "reason": "not_found",
                        "detail": "No such plan, or it is not visible to you."}

            ctx = ApprovalContext(
                athlete_id=str(plan["athlete_id"]),
                assigned_coach_id=str(plan["coach_id"]) if plan["coach_id"] else None,
                band=RiskBand(plan["band"]),
                plan_state=plan["state"],
                plan_content_hash=plan["content_hash"],
                actor_id=identity.athlete_id or identity.coach_id or "",
                actor_role=ApproverRole(identity.role),
            )
            outcome = evaluate(ctx)

            if outcome.allowed:
                cur.execute(
                    """INSERT INTO approval_record
                         (plan_id, approved_content_hash, approver_id, approver_role, decision)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (plan_id, outcome.binds_content_hash, outcome.approver_id,
                     outcome.approver_role.value, decision),
                )
                cur.execute(
                    "UPDATE plan_proposal SET state = %s WHERE id = %s",
                    ("approved" if decision == "approved" else "rejected", plan_id),
                )

    # Audited whether allowed or denied — a refused activation attempt is exactly the
    # kind of event Principle V exists to record (FR-009 in spirit, SC-003 in evidence).
    write_entry(
        AuditEntry(
            actor_id=identity.athlete_id or identity.coach_id or "unknown",
            actor_role=identity.role,
            action="plan_decision" if outcome.allowed else "plan_decision_denied",
            subject_id=plan_id,
            payload=(
                {"decision": decision, "approver_role": outcome.approver_role.value,
                 "content_hash": outcome.binds_content_hash}
                if outcome.allowed
                else {"denied_reason": outcome.reason.value, "detail": outcome.detail}
            ),
        )
    )

    if outcome.allowed:
        return {"allowed": True, "decision": decision,
                "approver_role": outcome.approver_role.value,
                "bound_content_hash": outcome.binds_content_hash}
    return {"allowed": False, "reason": outcome.reason.value, "detail": outcome.detail}


def assessment_is_current(assessment: Assessment, stored_hash: str) -> bool:
    """Helper for callers that need FR-005's binding check without re-reading the plan."""
    return plan_content_hash(_build_content(flow.serialise(assessment))) == stored_hash
