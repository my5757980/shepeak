"""ShePeak API.

Two things this layer is responsible for, both constitutional:

1. Binding the verified caller identity to the database transaction, so RLS has a subject
   (Principle VI). Identity comes from a token claim — never from a request body or header
   the client controls.
2. Re-checking the deterministic verdict before serialisation (FR-003, Principle I). If a
   narrative disagrees with the verdict it explains, the response is an error, not the
   narrative.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Body, Depends, FastAPI, HTTPException, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api import auth
from api.db import Identity, request_transaction
from audit.writer import chain_head, verify_chain
from explanation.narrator import explain
from orchestrator import approval as gate
from orchestrator import assess as flow

FRONTEND = Path(__file__).resolve().parents[3] / "frontend"

app = FastAPI(
    title="ShePeak API",
    version="0.1.0",
    description=(
        "Injury risk and training guidance for women athletes. Safety-critical decisions "
        "are deterministic and re-checked at this boundary; the language model explains "
        "but never decides."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Requests ----------------------------------------------------------------------------


class MetricIn(BaseModel):
    kind: str
    value: str
    captured_at: str | None = Field(
        default=None,
        description="When the measurement was taken. Distinct from ingestion time (FR-024).",
    )


class ApproveIn(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


# --- Endpoints ---------------------------------------------------------------------------


@app.get("/api/me")
def me(identity: Identity = Depends(auth.current_identity)) -> dict[str, Any]:
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            if identity.role == "athlete":
                cur.execute(
                    """SELECT a.id, a.display_name, a.sport, a.coach_id, c.display_name AS coach_name
                       FROM athlete a LEFT JOIN coach c ON c.id = a.coach_id
                       WHERE a.id = %s""",
                    (identity.athlete_id,),
                )
            else:
                cur.execute(
                    """SELECT a.id, a.display_name, a.sport, a.coach_id, NULL AS coach_name
                       FROM athlete a WHERE a.coach_id = %s ORDER BY a.display_name""",
                    (identity.coach_id,),
                )
            rows = [dict(r) for r in cur.fetchall()]
    return {"role": identity.role, "athletes": [_stringify(r) for r in rows]}


@app.get("/api/athletes/{athlete_id}/assessment")
def get_assessment(
    athlete_id: str = PathParam(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    """Assess, or refuse and say why. A refusal is a 200 with an outcome, not an error —
    withholding a score is the system working correctly (Principle IV)."""
    result = flow.run(identity, athlete_id)

    narrative = explain(result)
    # FR-003: the boundary re-check. The narrative is discarded rather than trusted if it
    # contradicts the deterministic verdict it claims to explain.
    if narrative is not None and not narrative["consistent"]:
        raise HTTPException(
            status_code=500,
            detail=(
                "Explanation contradicted the deterministic verdict and was discarded. "
                "No guidance is returned rather than guidance we cannot stand behind."
            ),
        )
    result["narrative"] = narrative["text"] if narrative else None
    result["narrative_source"] = narrative["source"] if narrative else None
    return result


@app.get("/api/athletes/{athlete_id}/metrics")
def list_metrics(
    athlete_id: str = PathParam(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT DISTINCT ON (kind) kind, value, captured_at, ingested_at, source
                   FROM health_metric WHERE athlete_id = %s
                   ORDER BY kind, captured_at DESC""",
                (athlete_id,),
            )
            rows = [_stringify(dict(r)) for r in cur.fetchall()]
    return {"metrics": rows}


@app.post("/api/athletes/{athlete_id}/metrics", status_code=201)
def add_metric(
    athlete_id: str = PathParam(...),
    body: MetricIn = Body(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    """Manual entry only in this release (FR-025). Capture time is recorded separately from
    ingestion time (FR-024) so staleness is always measured against when it happened."""
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO health_metric (athlete_id, kind, value, captured_at, source)
                   VALUES (%s, %s, %s, coalesce(%s::timestamptz, now()), 'manual')
                   RETURNING id, kind, value, captured_at, ingested_at""",
                (athlete_id, body.kind, body.value, body.captured_at),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(403, "Not permitted, or no covering consent for this athlete.")
    return _stringify(dict(row))


@app.get("/api/athletes/{athlete_id}/plan")
def get_plan(
    athlete_id: str = PathParam(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    from orchestrator.propose import current_or_new

    return current_or_new(identity, athlete_id)


@app.post("/api/plans/{plan_id}/decision")
def decide_plan(
    plan_id: str = PathParam(...),
    body: ApproveIn = Body(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    """Principle II. A denial here is the guarantee working, so it returns a structured
    reason rather than a bare 403 the UI cannot explain."""
    from orchestrator.propose import decide

    outcome = decide(identity, plan_id, body.decision)
    if not outcome["allowed"]:
        return {**outcome, "status": "denied"}
    return {**outcome, "status": "recorded"}


@app.get("/api/consent/{athlete_id}")
def list_consent(
    athlete_id: str = PathParam(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT purpose, granted_at, withdrawn_at FROM consent_record
                   WHERE athlete_id = %s ORDER BY purpose""",
                (athlete_id,),
            )
            rows = [_stringify(dict(r)) for r in cur.fetchall()]
    return {"consents": rows}


@app.post("/api/consent/{athlete_id}/{purpose}/withdraw")
def withdraw_consent(
    athlete_id: str = PathParam(...),
    purpose: str = PathParam(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    """FR-012. Withdrawal stops future processing; prior audit entries are retained."""
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE consent_record SET withdrawn_at = now()
                   WHERE athlete_id = %s AND purpose = %s::consent_purpose
                     AND withdrawn_at IS NULL
                   RETURNING purpose, withdrawn_at""",
                (athlete_id, purpose),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(404, "No live consent for that purpose.")
    return _stringify(dict(row))


@app.post("/api/consent/{athlete_id}/{purpose}/grant")
def grant_consent(
    athlete_id: str = PathParam(...),
    purpose: str = PathParam(...),
    identity: Identity = Depends(auth.current_identity),
) -> dict[str, Any]:
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO consent_record (athlete_id, purpose)
                   VALUES (%s, %s::consent_purpose)
                   ON CONFLICT DO NOTHING RETURNING purpose, granted_at""",
                (athlete_id, purpose),
            )
            row = cur.fetchone()
    return _stringify(dict(row)) if row else {"purpose": purpose, "already_granted": True}


@app.get("/api/audit/verify")
def audit_verify() -> dict[str, Any]:
    """FR-010. Needs only read access and the chain rule — it does not trust this API.

    The honest scope is returned with the result: this detects an altered entry, not a
    chain rewritten wholesale. That needs the externally published head (FR-010a), which
    is on the roadmap and is why nothing here claims independent verifiability.
    """
    problems = verify_chain()
    head = chain_head()
    return {
        "intact": not problems,
        "problems": problems,
        "entry_count": head["entry_count"],
        "head_hash": head["head_hash"],
        "guarantee": "tamper-evident against the application",
        "not_yet": "independent verification requires external anchoring (FR-010a, roadmap)",
    }


@app.get("/api/audit/entries")
def audit_entries(
    limit: int = 25, identity: Identity = Depends(auth.current_identity)
) -> dict[str, Any]:
    with request_transaction(identity) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT seq, actor_id, actor_role, action, subject_id, payload,
                          rule_set_version, prev_hash, entry_hash, created_at
                   FROM audit_entry ORDER BY seq DESC LIMIT %s""",
                (min(limit, 200),),
            )
            rows = [_stringify(dict(r)) for r in cur.fetchall()]
    return {"entries": rows}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Static frontend ----------------------------------------------------------------------

if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(FRONTEND / "index.html")


def _stringify(row: dict[str, Any]) -> dict[str, Any]:
    """UUIDs and timestamps to strings, so the payload is JSON-safe without a custom encoder."""
    import datetime as _dt
    import uuid as _uuid

    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, _uuid.UUID):
            out[key] = str(value)
        elif isinstance(value, (_dt.datetime, _dt.date)):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out
