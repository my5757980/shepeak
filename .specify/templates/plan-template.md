# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Record PASS / FAIL / N/A with one line of evidence for each. Any FAIL must appear in
Complexity Tracking with the rejected simpler alternative, or the plan does not proceed.

Two rules for filling this table:

- A status describes the **present** state. "PARTIAL → PASS after X" is a forecast, not a status;
  record PARTIAL and put the sequencing in Complexity Tracking.
- Evidence that names a mechanism MUST also name the mechanism's **subject or trigger** — what it
  filters on, what fires it, what it re-checks. "RLS is enabled" is not evidence; "RLS filters on
  the request-scoped athlete identity set from a verified token claim" is.

| # | Principle | Gate question | Status |
|---|-----------|---------------|--------|
| I | Guarantee in code | Are all safety-critical thresholds deterministic and re-checked at the API boundary? Is the LLM confined to explanation? | [ ] |
| II | Human-in-the-loop | Does every irreversible action require an explicit recorded coach/athlete approval? | [ ] |
| III | Women-first | What is the measurable equity/performance claim, and which sex-specific factors are modelled explicitly? | [ ] |
| IV | Fail closed | On missing/stale data, low confidence, or policy violation, does the system withhold and escalate with a reason? | [ ] |
| V | Auditability | Is every recommendation, score, and human decision appended to the hash-chained log before the response returns? | [ ] |
| VI | Privacy & consent | Is health data gated by a purpose-scoped consent record, enforced at the database layer? | [ ] |
| VII | Explainability | Does every score return its input metrics plus rule/model versions, from the same computation? | [ ] |
| VIII | Spec-driven | Do failing tests exist for the acceptance criteria, including the refusal paths? | [ ] |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
