"""Tiered approval gate (FR-004, FR-005, FR-021, SA-002, Principle II).

Pure decision logic, deliberately separated from persistence so it can be exhaustively
tested without a database. The rule it enforces:

    elevated / high risk  → coach approval only
    low / moderate risk   → athlete may self-approve
    no coach assigned     → elevated/high plans cannot be activated at all (fail closed)

That last case is the one that matters. The tiered rule assumes a coach exists; an
unaffiliated athlete at elevated risk has no authorised approver, and Principle IV says the
answer is to withhold — not to quietly fall back to self-approval, which would hollow out
the guarantee.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from risk_engine.types import RiskBand


class ApproverRole(str, Enum):
    ATHLETE = "athlete"
    COACH = "coach"


class DenialReason(str, Enum):
    COACH_APPROVAL_REQUIRED = "coach_approval_required"
    NO_AUTHORISED_COACH = "no_authorised_coach"
    NOT_THIS_ATHLETES_COACH = "not_this_athletes_coach"
    NOT_THIS_ATHLETE = "not_this_athlete"
    PLAN_MODIFIED_SINCE_APPROVAL = "plan_modified_since_approval"
    PLAN_NOT_PROPOSED = "plan_not_proposed"


@dataclass(frozen=True)
class ApprovalContext:
    """Everything the gate needs. No I/O happens here."""

    athlete_id: str
    assigned_coach_id: str | None
    band: RiskBand
    plan_state: str
    plan_content_hash: str
    actor_id: str
    actor_role: ApproverRole


@dataclass(frozen=True)
class Denied:
    reason: DenialReason
    detail: str

    allowed: bool = False


@dataclass(frozen=True)
class Allowed:
    approver_role: ApproverRole
    approver_id: str
    binds_content_hash: str

    allowed: bool = True


Decision = Allowed | Denied


def plan_content_hash(content: dict[str, Any]) -> str:
    """Stable hash of plan content — an approval binds to this exact value (FR-005)."""
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evaluate(ctx: ApprovalContext) -> Decision:
    """Decide whether this actor may activate this plan. Denials say exactly why."""
    if ctx.plan_state != "proposed":
        return Denied(
            reason=DenialReason.PLAN_NOT_PROPOSED,
            detail=f"Plan is '{ctx.plan_state}', so it is not awaiting approval.",
        )

    if ctx.band.requires_coach_approval:
        # The absence of any authorised approver is checked FIRST, whoever is asking.
        # Telling an athlete with no coach to "ask your coach" is both inaccurate and
        # unactionable; a refusal she cannot act on is a worse refusal (Principle IV asks
        # for a stated reason, and the reason has to be the real one).
        if ctx.assigned_coach_id is None:
            # US2 scenario 8 — fail closed, do NOT degrade to self-approval.
            return Denied(
                reason=DenialReason.NO_AUTHORISED_COACH,
                detail=(
                    f"This plan follows a {ctx.band.value} risk assessment and requires "
                    "coach approval, but no coach is assigned to this athlete. The plan "
                    "stays inactive until a coach is assigned."
                ),
            )
        if ctx.actor_role is ApproverRole.ATHLETE:
            # SC-011 — the refusal that makes human-in-the-loop real rather than nominal.
            return Denied(
                reason=DenialReason.COACH_APPROVAL_REQUIRED,
                detail=(
                    f"This plan follows a {ctx.band.value} risk assessment. "
                    "It requires approval from your coach and cannot be self-approved."
                ),
            )
        if ctx.actor_id != ctx.assigned_coach_id:
            return Denied(
                reason=DenialReason.NOT_THIS_ATHLETES_COACH,
                detail="You are not the coach assigned to this athlete.",
            )
        return Allowed(
            approver_role=ApproverRole.COACH,
            approver_id=ctx.actor_id,
            binds_content_hash=ctx.plan_content_hash,
        )

    # Low / moderate band — the athlete herself, or her assigned coach, may approve.
    if ctx.actor_role is ApproverRole.ATHLETE:
        if ctx.actor_id != ctx.athlete_id:
            return Denied(
                reason=DenialReason.NOT_THIS_ATHLETE,
                detail="You may only approve your own plan.",
            )
        return Allowed(
            approver_role=ApproverRole.ATHLETE,
            approver_id=ctx.actor_id,
            binds_content_hash=ctx.plan_content_hash,
        )

    if ctx.assigned_coach_id is None or ctx.actor_id != ctx.assigned_coach_id:
        return Denied(
            reason=DenialReason.NOT_THIS_ATHLETES_COACH,
            detail="You are not the coach assigned to this athlete.",
        )
    return Allowed(
        approver_role=ApproverRole.COACH,
        approver_id=ctx.actor_id,
        binds_content_hash=ctx.plan_content_hash,
    )


def approval_still_valid(approved_hash: str, current_content: dict[str, Any]) -> bool:
    """FR-005: an approval does not survive modification of what was approved."""
    return approved_hash == plan_content_hash(current_content)
