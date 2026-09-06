"""Demo seed — T0.9, T4.4.

Five athletes chosen so the demo exercises the guarantees, not just the happy path:

  1. Priya    — low risk, everything recorded. The baseline.
  2. Aisha    — ELEVATED via ovulatory ACL + bowling load. Coach approval required.
  3. Fatima   — HIGH via RED-S (recorded amenorrhoea, no contraception) + low ferritin.
                The case a male-default model cannot see at all.
  4. Sana     — REFUSED: soreness is stale. Demonstrates fail-closed.
  5. Zainab   — ELEVATED with NO ASSIGNED COACH. Cannot activate any plan (US2 scenario 8).

Run: python seed.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).parent / "src"))

from api.auth import issue  # noqa: E402

OWNER_DSN = os.environ.get(
    "SHEPEAK_OWNER_DSN", "postgresql://shepeak_owner:dev_only@localhost:55432/shepeak"
)

NOW = datetime.now(timezone.utc)


def ago(**kw) -> datetime:
    return NOW - timedelta(**kw)


KEYS = ["priya", "aisha", "fatima", "sana", "zainab"]

ATHLETES = [
    {
        "name": "Priya Raman", "sport": "cricket", "coached": True,
        "note": "Low risk — the baseline case",
        "baseline": 100, "metrics": [
            ("training_load", "98", ago(hours=3)),
            ("sleep", "8.1", ago(hours=6)),
            ("soreness", "2", ago(hours=6)),
            ("cycle_phase", "follicular", ago(days=1)),
            ("contraception_status", "false", ago(days=10)),
            ("iron_status", "62", ago(days=20)),
            ("bowling_load", "9", ago(hours=12)),
        ],
    },
    {
        "name": "Aisha Khan", "sport": "cricket", "coached": True,
        "note": "Elevated — ovulatory ACL risk plus heavy bowling spell",
        "baseline": 100, "metrics": [
            ("training_load", "142", ago(hours=4)),
            ("sleep", "6.1", ago(hours=7)),
            ("soreness", "7", ago(hours=5)),
            ("cycle_phase", "ovulatory", ago(days=1)),
            ("contraception_status", "false", ago(days=15)),
            ("iron_status", "45", ago(days=30)),
            ("bowling_load", "24", ago(hours=10)),
        ],
    },
    {
        "name": "Fatima Noor", "sport": "athletics", "coached": True,
        "note": "High — RED-S indicator plus iron deficiency. Invisible to a male-default model.",
        "baseline": 100, "metrics": [
            ("training_load", "155", ago(hours=5)),
            ("sleep", "5.9", ago(hours=8)),
            ("soreness", "8", ago(hours=4)),
            ("cycle_phase", "recorded_absent", ago(days=2)),
            ("contraception_status", "false", ago(days=40)),
            ("iron_status", "17", ago(days=25)),
        ],
    },
    {
        "name": "Sana Iqbal", "sport": "cricket", "coached": True,
        "note": "REFUSED — soreness is 31h old, past its 24h window",
        "baseline": 100, "metrics": [
            ("training_load", "120", ago(hours=6)),
            ("sleep", "7.0", ago(hours=9)),
            ("soreness", "5", ago(hours=31)),          # stale
            ("cycle_phase", "luteal", ago(days=2)),
            ("contraception_status", "false", ago(days=20)),
            ("iron_status", "50", ago(days=30)),
        ],
    },
    {
        "name": "Zainab Ali", "sport": "cricket", "coached": False,
        "note": "Elevated with NO COACH — plan cannot activate at all (fail closed)",
        "baseline": 100, "metrics": [
            ("training_load", "150", ago(hours=3)),
            ("sleep", "6.0", ago(hours=6)),
            ("soreness", "8", ago(hours=5)),
            ("cycle_phase", "ovulatory", ago(days=1)),
            ("contraception_status", "false", ago(days=12)),
            ("iron_status", "40", ago(days=28)),
            ("bowling_load", "22", ago(hours=8)),
        ],
    },
]


def main() -> None:
    with psycopg.connect(OWNER_DSN, autocommit=True) as conn:
        cur = conn.cursor()

        cur.execute("DELETE FROM approval_record")
        cur.execute("DELETE FROM plan_proposal")
        cur.execute("DELETE FROM risk_assessment")
        cur.execute("DELETE FROM escalation")
        cur.execute("DELETE FROM health_metric")
        cur.execute("DELETE FROM consent_record")
        cur.execute("DELETE FROM athlete")
        cur.execute("DELETE FROM coach")

        cur.execute(
            "INSERT INTO coach (display_name) VALUES ('Coach Meera Devi') RETURNING id"
        )
        coach_id = cur.fetchone()[0]
        tokens = {"coach": issue("coach", str(coach_id))}

        print(f"\n  Coach token (Meera Devi):\n    {issue('coach', str(coach_id))}\n")
        print("  " + "-" * 70)

        for key, spec in zip(KEYS, ATHLETES):
            cur.execute(
                "INSERT INTO athlete (display_name, sport, coach_id) VALUES (%s,%s,%s) "
                "RETURNING id",
                (spec["name"], spec["sport"], coach_id if spec["coached"] else None),
            )
            athlete_id = cur.fetchone()[0]

            for purpose in ("injury_risk_scoring", "plan_generation", "explanation_generation"):
                cur.execute(
                    "INSERT INTO consent_record (athlete_id, purpose) VALUES (%s,%s)",
                    (athlete_id, purpose),
                )

            # Baseline history so a load spike is measurable (otherwise: NO_BASELINE refusal).
            for day in range(10, 32):
                cur.execute(
                    """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
                       VALUES (%s,'training_load',%s,%s)""",
                    (athlete_id, str(spec["baseline"]), ago(days=day)),
                )

            for kind, value, captured in spec["metrics"]:
                cur.execute(
                    """INSERT INTO health_metric (athlete_id, kind, value, captured_at)
                       VALUES (%s,%s,%s,%s)""",
                    (athlete_id, kind, value, captured),
                )

            print(f"\n  {spec['name']}  ({'coached' if spec['coached'] else 'NO COACH'})")
            print(f"    {spec['note']}")
            tokens[key] = issue("athlete", str(athlete_id))
            print(f"    token: {tokens[key][:40]}...")

        import json

        out = Path(__file__).resolve().parents[1] / "frontend" / "assets" / "demo-tokens.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(tokens, indent=2), encoding="utf-8")

        print("\n  " + "-" * 70)
        print(f"  Demo tokens -> {out}")
        print("  Seeded 5 athletes. Start the API:  uvicorn api.main:app --app-dir src\n")


if __name__ == "__main__":
    main()
