---
id: 0009
title: Build ShePeak Prototype
stage: green
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: 001-athlete-health-core
branch: 001-athlete-health-core
user: ms5373268@gmail.com
command: (user request — "project ko 100% ready karo, professional responsive UI ke sath")
labels: ["implementation", "risk-engine", "rls", "audit-chain", "frontend", "accessibility", "i18n"]
links:
  spec: specs/001-athlete-health-core/spec.md
  ticket: https://challenges.ignyte.ae/competition/1B9DF5DB-F9A0-F011-B3CD-002248CB5C1B
  adr: history/adr/0001-audit-log-storage-mechanism.md
  pr: null
files:
  - backend/src/risk_engine/ (types, version, freshness, factors, rules, confidence, engine)
  - backend/src/orchestrator/ (approval, assess, propose)
  - backend/src/api/ (main, auth, db, scrub)
  - backend/src/audit/writer.py
  - backend/src/explanation/narrator.py
  - backend/migrations/ (001 schema, 002 audit, 003 rls, 004 app role)
  - backend/tests/ (unit, refusal, security — 181 tests)
  - frontend/ (index.html, assets/styles.css, app.js, i18n.js)
  - submission/ (usp, solution overview, pitch deck, video script)
  - README.md, .env.example, docker-compose.yml, backend/seed.py
tests:
  - 181 passing — unit, refusal paths, mutation guard, live PostgreSQL security, end-to-end
---

## Prompt

haaa shuruuu karoo project 1oo% readyy karooo profesiional ui responsive uiux kayy sath

(preceded by: "achaaa mayy female member dhoond loo ga tum project ko to 1oo% ready karooo")

## Response snapshot

Built the working prototype end to end across three commits. 181 tests pass. One task remains
open — T4.14, recording the video — which belongs to the user.

**Risk engine (pure).** No network, database, LLM, or clock reads — enforced by
`test_import_boundary.py` rather than convention, because Principle I erodes by import creep.
Rule set identifies itself by content hash. Three distinct cycle states, with recorded
amenorrhoea firing RED-S at 25 points while absent *data* fires nothing. Absent sex-specific
inputs are reported, never defaulted. Cricket bowling workload as a first-class input with
sport-agnostic rules.

**Database enforcement.** Append-only hash-chained audit with advisory-lock serialisation;
`FORCE ROW LEVEL SECURITY` on every health table; a non-owner `NOBYPASSRLS` application role;
request-scoped identity via `SET LOCAL` from a verified JWT claim. Verified against a live
PostgreSQL 16 container, not mocks.

**Frontend.** Responsive, WCAG-minded, English + Urdu with RTL — including translated rule
explanations and refusal reasons, not only chrome. A refusal renders as a calm designed panel,
never an error toast, because withholding a score is the product working.

**Six bugs found by actually running things, each a real defect:**

1. Approval gate told an athlete with no coach to "ask your coach" — inaccurate and
   unactionable. Reordered so the absent-approver case is checked first.
2. RTL layout blew the document to 11,350px wide. Cause: `left:-9999px` on the skip link.
   Replaced with clip-path hiding plus an overflow guard.
3. Log scrubber missed the dataclass repr form `kind='sleep', value=5.9` — exactly the shape
   an exception handler including the offending row would produce.
4. Approval-denial regex missed "do not need approval" (only "does not need" matched). The
   single most damaging thing a model could emit, so the pattern was deliberately widened.
5. A security test asserted the wrong layer: the app role's UPDATE is denied by the GRANT
   before the trigger fires. Split into two tests so defence in depth does not read as failure.
6. An end-to-end test inserted a stale metric alongside a fresh one and expected a refusal —
   the engine correctly reads the latest capture. Test bug, not product bug; fixed by
   removing the fresh row, with a comment explaining why.

**Two guards written to protect intent rather than behaviour.** A mutation guard removes each
safety rule in turn and asserts the score changes — a rule deletable without a test failing is
uncovered, and the female-specific rules get their own pass so EQ-002 cannot become decorative.
And an automated submission-accuracy test fails the build if any audience-facing artifact
claims independent verifiability while FR-010a is unbuilt. It caught a line in the pitch deck
on its first run.

**Deliberate deviation from plan.md:** frontend built as a single-page app (vanilla JS +
hand-written CSS) rather than Next.js. With 29 days and a video to record, a zero-build-step
frontend removes a class of failure during recording. Recorded here rather than silently.

## Outcome

- ✅ Impact: Working prototype — deterministic engine, live database enforcement, API,
  bilingual accessible UI, seed data, and all submission documents except the video itself.
- 🧪 Tests: 181 passing — unit, refusal paths, mutation guard, live PostgreSQL security
  (RLS bypass, audit tamper), end-to-end through the real stack.
- 📁 Files: three commits — `8b90727` engine + approval + migrations, `e088928` API +
  frontend, `219751e` remaining safety gaps + submission docs.
- 🔁 Next prompts: user records the video (T4.14) and resolves the female-contributor
  eligibility gate; optionally enable a pinned LLM for narrative rephrasing.
- 🧠 Reflection: the highest-value tests were the ones asserting the system *refuses*. Four of
  the six real bugs surfaced in refusal, denial, or scrubbing paths — the code that only runs
  when something has gone wrong, and therefore the code least exercised by demoing.

## Evaluation notes (flywheel)

- Failure modes observed: writing UI polish before running it (the RTL overflow was invisible
  in code review and obvious in a screenshot); asserting on error *messages* rather than error
  *outcomes*, which made a correct defence-in-depth result look like a failure; and building a
  test fixture from the engine's mental model rather than the real query's behaviour.
- Graders run and results (PASS/FAIL): PASS — 181 tests including every SA-001 refusal
  condition; PASS — live database security tests, not mocked; PASS — mutation guard proves
  every safety rule is observable; PASS — automated honesty guard over audience-facing
  artifacts; PASS — screenshots verified at desktop, mobile 390px, and RTL.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): screenshot every UI state at three viewports and
  both directions as part of the test run, not by hand. The RTL overflow would have been
  caught by a `scrollWidth === clientWidth` assertion costing one line.
