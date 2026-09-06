---
id: 0001
title: ShePeak Constitution Ratification
stage: constitution
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: none
branch: none
user: ms5373268@gmail.com
command: /sp.constitution
labels: ["constitution", "governance", "safety", "athlete-health", "spec-driven-development"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - .specify/templates/plan-template.md
  - .specify/templates/spec-template.md
  - .specify/templates/tasks-template.md
tests:
  - none (documentation and template change; no executable tests in repo yet)
---

## Prompt

# ShePeak Constitution

## Core Principles (Non-Negotiable)

1. **Guarantee lives in code, never in the model**  
   All safety-critical decisions (injury risk thresholds, recovery prescriptions, load limits) must be deterministic and re-checked at the API boundary. The LLM may only explain or suggest.

2. **Human-in-the-loop is mandatory for irreversible actions**  
   No training plan, recovery protocol, or medical recommendation can be auto-applied without explicit coach/athlete approval.

3. **Women-first by design**  
   Every feature must demonstrably improve equity, visibility, or performance outcomes for women athletes. Gender-specific physiological differences must be explicitly modelled.

4. **Fail closed**  
   Missing data, low confidence, or policy violation → system refuses to act and escalates.

5. **Full auditability**  
   Every recommendation, risk score, and human decision must be recorded in an append-only, hash-chained audit log.

6. **Privacy & consent first**  
   Athlete health data is never used without explicit consent. Data residency and access controls are enforced at the database level.

7. **Explainability over black-box**  
   Every risk score and recommendation must cite the exact evidence (metrics + rules) that produced it.

8. **Spec-Driven Development**  
   No feature is implemented without corresponding constitution check, acceptance criteria, and tests.

## Response snapshot

Ratified `.specify/memory/constitution.md` at **v1.0.0** (first ratification; the file was an
unfilled SpecKit template). The user's eight principles were expanded from prose into
declarative MUST/MUST NOT rules, each with a rationale, and the template's six principle
slots were extended to eight.

Additions beyond verbatim transcription:

- **Safety and Compliance Constraints** section — deterministic safety core as a single
  versioned module, API-boundary re-check with error-on-mismatch, explicit
  "not a medical device" boundary, health data as highest sensitivity tier (no third-party
  model processing without covering consent; never raw in logs), secrets in environment
  config only.
- **Development Workflow and Quality Gates** section — Constitution Check gate, smallest
  viable diff, refusal-path test gate, ADR and PHR discipline.
- **Governance** section — amendment procedure (Sync Impact Report + migration path + owner
  approval; ADR required to weaken a NON-NEGOTIABLE), MAJOR/MINOR/PATCH policy, and
  compliance review naming `/sp.analyze` conflicts as CRITICAL and blocking.

Consistency propagation (three template edits, one of which resolved a real conflict):

1. `plan-template.md` — replaced the `[Gates determined based on constitution file]`
   placeholder with a concrete eight-row Constitution Check table, one gate question per
   principle.
2. `tasks-template.md` — **conflict resolved**: the template declared tests
   "OPTIONAL - only include them if explicitly requested", directly contradicting
   Principle VIII. Changed to MANDATORY across the policy line and all three user-story
   test sections, and added the refusal-path requirement for Principles I, II, IV, VII.
3. `spec-template.md` — added a mandatory **Equity Claim** section (EQ-001/EQ-002) for
   Principle III with an explicit list of sex-specific physiological factors, and a
   **Safety and Consent Requirements** section (SA-001..SA-004) for Principles II, IV, VI,
   VII.

Validated: no unresolved bracket tokens, eight `###` principle headings, ISO dates, version
line matches the Sync Impact Report.

## Outcome

- ✅ Impact: Project constitution ratified at v1.0.0; three SpecKit templates brought into
  alignment, including one direct contradiction removed.
- 🧪 Tests: None run — no test harness exists in the repo yet. Principle VIII now makes
  tests mandatory for the first feature.
- 📁 Files: `.specify/memory/constitution.md` (rewritten), `plan-template.md`,
  `spec-template.md`, `tasks-template.md` (amended).
- 🔁 Next prompts: `/sp.specify` for the first ShePeak feature; author `README.md` restating
  Principles I, II, IV and the consent model.
- 🧠 Reflection: The principles are stated at a level a reviewer can fail a PR against.
  The weakest link is Principle V — a hash-chained append-only log needs a concrete storage
  decision (DB-native vs. external ledger) before any feature depends on it.

## Evaluation notes (flywheel)

- Failure modes observed: A `cat` heredoc write of the constitution failed under the Bash
  tool with a quoting error; fell back to the Write tool, which succeeded.
- Graders run and results (PASS/FAIL): PASS — no unresolved placeholders; PASS — version
  line matches Sync Impact Report; PASS — ISO-8601 dates; PASS — all principles use
  MUST/MUST NOT rather than "should".
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Write an ADR for the audit-log storage mechanism
  (Principle V) before the first feature spec, so the first `/sp.plan` Constitution Check has
  a concrete gate to point at.
