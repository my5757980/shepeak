---
id: 0008
title: Apply Hackathon Scope Decisions
stage: tasks
date: 2026-09-06
surface: agent
model: claude-opus-5
feature: 001-athlete-health-core
branch: 001-athlete-health-core (no git repo; directory naming only)
user: ms5373268@gmail.com
command: (user decisions on hackathon alignment)
labels: ["hackathon", "scope-cut", "eligibility", "accessibility", "cricket", "deliverables"]
links:
  spec: specs/001-athlete-health-core/spec.md
  ticket: https://challenges.ignyte.ae/competition/1B9DF5DB-F9A0-F011-B3CD-002248CB5C1B
  adr: history/adr/0001-audit-log-storage-mechanism.md
  pr: null
files:
  - specs/001-athlete-health-core/hackathon-alignment.md
  - specs/001-athlete-health-core/spec.md
  - specs/001-athlete-health-core/tasks.md
tests:
  - none run (planning artifacts)
---

## Prompt

Answers to the three decision questions:

- Team mein female contributor hai? → **"Nahi / abhi tak nahi"** (no female contributor yet)
- 29 din hain. Scope ka kya karein? → **"Demo-first cut"**
- Cricket / ICC angle add karein? → **"Cricket-first, rules general rakhein"**

## Response snapshot

Applied all three decisions across the alignment doc, spec, and task list.

**Eligibility recorded as the top open risk.** The team has no female contributor, and the
competition rule is a gate, not a preference — without it, 29 days of engineering produces
something that cannot be entered. Recorded in `hackathon-alignment.md` with a red-flag section and
in `tasks.md` as a blocking item outside the task list, deliberately placed above every
engineering task. Noted that recruiting should be for genuine contribution: a token name is
against the rule's intent and useless to a product about women athletes. Recommended resolving it
within week one, and reconsidering the investment if it cannot be.

**Demo-first cut applied.** Deferred to a stated roadmap rather than deleted: T3.1 (chain-head
anchoring), T3.10 (rewritten-chain detection), T3.4 (concurrent load tests), T4.9 (comprehension
study). Kept the explanation service and the integrity check with altered-entry detection — both
are cheap and both demonstrate the audit guarantee on stage.

The important consequence, written into the task list in bold: **deferring T3.1 leaves Principle V
PARTIAL**, so the submission, deck, and video must not describe the audit log as "independently
verifiable" or "tamper-proof". Accurate wording supplied: "append-only and tamper-evident against
the application; independent anchoring is on the roadmap." Added T4.15 as a submission accuracy
review to enforce it.

**Cricket-first with general rules.** FR-026 models bowling workload — overs bowled, spell
density, consecutive playing days — as a first-class load input while keeping the rule structure
sport-agnostic. Serves judging criterion 4 ("across ICC events") and preserves the cross-sport
bonus at the same time. Task T1.16.

**Closed the near-empty 10% category.** FR-027 (WCAG 2.2 AA, with refusal reasons and evidence
reachable by keyboard and screen reader) and FR-028 (second language covering refusal reasons and
evidence, not only navigation chrome), with SC-013 and SC-014, tasks T4.10 and T4.11. FR-028
carries a Principle VII argument: a reason an athlete cannot read is a refusal without an
explanation.

**Added the missing submission deliverables**, which were absent entirely: T4.12 USP statement
(judging criterion 1, 25%, our weakest — written first because it shapes the deck and video),
T4.13 written summary max 2 pages, T4.14 record and edit the actual video (T4.5 was only a
script), T4.15 accuracy review.

Coverage now 29/29 FR, 5/5 SA, 15/15 SC, with SC-005a and SC-009 explicitly deferred rather than
silently dropped.

## Outcome

- ✅ Impact: Artifacts now reflect the real competition constraints and a 29-day scope. The
  10% sustainability/inclusivity category went from unaddressed to specified. Submission
  deliverables that did not exist as tasks now exist.
- 🧪 Tests: None run. Two new test obligations: SC-013 (accessibility audit, 0 violations) and
  SC-014 (both languages, no untranslated fallback).
- 📁 Files: `hackathon-alignment.md` (decisions section), `spec.md` (FR-026–FR-028, SC-013,
  SC-014), `tasks.md` (T1.16, T4.10–T4.15, deferrals, coverage table, blocking notice).
- 🔁 Next prompts: resolve team eligibility; write T4.12 (USP) before any further build; `git init`;
  then begin Phase 0.
- 🧠 Reflection: The scope cut was easy; the honesty constraint it creates was the part worth
  writing down. Deferring T3.1 is fine — quietly keeping the "independently auditable" language in
  the pitch afterwards would not be. A constitution that permits partial compliance only when
  stated is worth nothing if the submission then overstates it, so the guardrail went into the
  task list as a checkable task rather than a note.

## Evaluation notes (flywheel)

- Failure modes observed: none new this round. The pre-existing failure being corrected is that
  five artifacts were built without the source brief, leaving a 10% judging category and a
  blocking eligibility rule unaddressed.
- Graders run and results (PASS/FAIL): PASS — all three decisions applied to every affected
  artifact; PASS — coverage table updated and deferred criteria marked deferred rather than
  dropped; PASS — the compliance consequence of deferring T3.1 recorded as an enforceable task
  (T4.15), not a comment; PASS — eligibility placed above engineering tasks in priority.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): when a task is deferred and it was the evidence for a
  constitution principle, automatically emit a paired "do not claim X" review task. That linkage
  was made by hand here and is the kind of thing that gets forgotten under deadline pressure.
