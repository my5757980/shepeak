# ShePeak

**Injury risk, built for women athletes.** ICC × Ignyte Hackathon — Problem Statement 3
(Athlete Health, Performance & Inclusivity), Prototype Track.

Deterministic injury-risk scoring where the safety guarantees live in code and in the database
— not in a language model. Every score cites its evidence, missing data produces a refusal
rather than a guess, and no training plan reaches an athlete without a human approving it.

---

## Run it

Requires Docker and Python 3.12.

```bash
docker compose up -d                 # PostgreSQL on :55432

cd backend
pip install fastapi uvicorn psycopg[binary] pytest
for f in migrations/*.sql; do
  docker exec -i shepeak-db psql -U shepeak_owner -d shepeak -v ON_ERROR_STOP=1 -q < "$f"
done
python seed.py                       # 5 demo athletes + tokens
python -m uvicorn api.main:app --app-dir src --port 8000
```

Open **http://localhost:8000** and pick a demo profile.

```bash
python -m pytest                     # 181 tests
python -m pytest tests/security -q   # RLS bypass + audit tamper attempts
```

## The five demo profiles

Each one exercises a different guarantee. Three of them are cases where the system declines to
behave conveniently.

| Profile | What it shows |
|---|---|
| **Priya Raman** | Low risk, everything recorded — the baseline |
| **Aisha Khan** | Elevated: ovulatory-phase ACL risk + heavy bowling spell |
| **Fatima Noor** | High: RED-S indicator + iron deficiency — invisible to a male-default model |
| **Sana Iqbal** | **Refused.** Soreness is 31h old, past its 24h window. Fail closed. |
| **Zainab Ali** | Elevated with **no coach**. Her plan cannot activate at all. |
| **Coach Meera Devi** | Approves or rejects across the squad |

## How the guarantees are enforced

| Guarantee | Mechanism | Where |
|---|---|---|
| Scores are deterministic | Pure engine — no network, DB, LLM, or clock reads | `backend/src/risk_engine/` |
| …and stays pure | Automated import-boundary test, not convention | `tests/unit/test_import_boundary.py` |
| Rules are version-pinned | Rule set identified by content hash | `risk_engine/version.py` |
| The LLM cannot decide | Rephrases only; narrative re-checked against the verdict, discarded on conflict | `explanation/narrator.py`, `api/main.py` |
| Missing/stale/low-confidence → no answer | Per-metric freshness windows, 0.7 confidence floor | `risk_engine/freshness.py`, `confidence.py` |
| Cycle states stay distinct | not recorded / recorded absent / suppressed — enforced by test | `risk_engine/factors.py` |
| No male-default substitution | Absences are reported, never filled | `risk_engine/engine.py` |
| Human approval required | Tiered gate; approval bound to a content hash | `orchestrator/approval.py` |
| Consent enforced below the app | RLS + `FORCE`, non-owner `NOBYPASSRLS` role, request-scoped identity | `migrations/003`, `004`, `api/db.py` |
| Every decision recorded | Append-only hash-chained audit, written before the response | `migrations/002_audit.sql` |

## What we do not claim

- **The audit log is tamper-evident, not independently verifiable.** It detects an altered
  entry. It does not defend against a database operator who disables the triggers and rewrites
  the chain. External anchoring of the chain head is specified (FR-010a) and on the roadmap —
  it is not built, so nothing here describes the log as independently verifiable.
- **Risk band boundaries are provisional engineering defaults** requiring sports-science
  validation before any non-prototype use. They are labelled as provisional in the product.
- **Not a medical device.** Training guidance only; anything crossing into diagnosis or
  treatment is refused and escalated.

## Repository

```
backend/src/risk_engine/    Pure deterministic core
backend/src/orchestrator/   Assessment flow, plan proposal, approval gate
backend/src/audit/          Chain append and verification
backend/src/api/            FastAPI, JWT, request-scoped RLS identity
backend/migrations/         Schema, audit triggers, RLS policies, app role
backend/tests/              181 tests — unit, refusal, security, integration
frontend/                   Responsive bilingual UI (English + Urdu, RTL)
specs/001-athlete-health-core/   Spec, plan, tasks, hackathon alignment
history/adr/                Architecture decision records
submission/                 USP, solution overview, deck, video script
.specify/memory/            Project constitution v1.0.0
```

## Accessibility and language

Keyboard and screen-reader operable, visible focus, 44px touch targets, and no meaning conveyed
by colour alone — every risk band carries a text label. English and Urdu with full RTL support,
including **translated refusal reasons and score evidence**, not only interface labels: a reason
an athlete cannot read is no explanation at all.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `SHEPEAK_DSN` | Application role connection (non-owner) | local Docker |
| `SHEPEAK_OWNER_DSN` | Migrations and tests only | local Docker |
| `SHEPEAK_JWT_SECRET` | Token signing | dev placeholder |
| `SHEPEAK_LLM_MODEL` | Pinned model id for narrative rephrasing. Unset = deterministic explanations only | unset |

No secrets are committed. Development credentials are placeholders and must be replaced outside
a local demo.
