# Hackathon Alignment Check — ICC x Ignyte

**Source**: [challenges.ignyte.ae competition page](https://challenges.ignyte.ae/competition/1B9DF5DB-F9A0-F011-B3CD-002248CB5C1B)
(read directly from the logged-in page on 2026-09-06)
**Competition**: ICC x Ignyte Hackathon — *Beyond Boundaries, Empowering Women, Inspiring Sport*
**Our choice**: Problem Statement 3 — Athlete Health, Performance & Inclusivity | **Prototype Track**

## Hard facts from the page

| Item | Value |
|---|---|
| Status | Open for submissions — **29 days left** |
| Start / Entry deadline | 2025-10-04 / **2026-10-05** |
| Demo date | 2026-10-26 |
| Prize pool | USD 10,000 — Overall USD 5,000; Student/Entrepreneur USD 2,500; **All-Female Team USD 2,500** |
| Participants | 5,866 |
| IP | **Finalists retain full ownership of their IP.** No obligation either way. |

> Correction to an earlier note in this project: a web search had suggested a December 2025
> deadline. That is wrong. The live page says **entry deadline 2026-10-05**, 29 days from today.

## Problem Statement 3 — verbatim

> "Technology is revolutionizing sports science, training, and wellness. How can wearables,
> machine learning, automation, and smart analytics be applied to help athletes — especially
> women — train smarter, recover faster, prevent injuries, and access equal opportunities for
> peak performance and inclusivity?"

**Verdict**: ShePeak sits directly on this. "Especially women", "prevent injuries", "recover
faster", "equal opportunities … and inclusivity" — our Principle III and EQ-001/002 are aligned
with the wording of the brief, not merely adjacent to it.

## Prototype Track — required deliverables

> "Prototype track: Working prototype, demo video (3 min max)"

Plus the minimum submission that applies to all tracks:

> "Minimum required submission file shall include a pitch deck, summary, and link to a video
> explaining the solution."
> "Solution Overview (max 2 pages or 5 slides): Problem statement, proposed solution, impact for
> sports/women in sports"
> "Prototype/Demo: Concept note, mockups, or wireframes"

| Requirement | Our task | Status |
|---|---|---|
| Working prototype | Phases 0–4 | On plan |
| Demo video, 3 min max | T4.5 (script only) | **Partial — script ≠ video** |
| Pitch deck, max 5 slides | T4.6 | Covered |
| Written summary (max 2 pages) | — | **MISSING** |
| Impact for women in sport, stated in the submission | EQ-001/002 exist in spec, not in a submission artifact | **MISSING as a deliverable** |

## Judging criteria vs. our artifacts

| # | Criterion | Weight | Our position |
|---|---|---|---|
| 1 | Innovation & Creativity — originality, differentiation | **25%** | **WEAKEST.** Highest-weighted criterion and we have no articulated USP anywhere in spec, plan, or tasks. Our differentiator is real (deterministic safety core + tiered human approval + sex-specific physiology as first-class input) but it is nowhere stated as a claim a judge can grade. |
| 2 | Technical Feasibility & Execution — soundness, scalability, **quality of documentation, architecture, design** | 20% | **STRONGEST.** Constitution v1.0.0, ADR-0001, spec with 26 FR / 13 SC, plan with an honest Constitution Check, tasks with full requirement traceability. Very few of 5,866 entrants will have this. |
| 3 | Impact on Women in Sport — equity, visibility, inclusivity in design | 20% | **STRONG.** Principle III is constitutionally enforced; FR-015 to FR-017 model sex-specific physiology and forbid male-default baselines. This is a design decision, not a marketing line. |
| 4 | Value to Fans, Athletes & Sports Ecosystem — fans, players, **coaches, sponsors**, across **ICC events** | 15% | **PARTIAL.** Athlete and coach are covered. Fans, sponsors, and any ICC-event or cricket connection are entirely absent. |
| 5 | Sustainability & Inclusivity — environmental practices, **accessibility, affordability, multi-language**, team diversity | 10% | **NEARLY ZERO.** Nothing in any artifact addresses accessibility, affordability, multi-language, or environmental impact. A whole category effectively unanswered. |
| 6 | Presentation & Storytelling — pitch clarity, demo quality | 10% | Planned (T4.5, T4.6), not yet built. |

**Bonus recognition**: women-led teams; cross-sport applicability beyond cricket;
pilot-readiness for ICC and partners.

## Eligibility — a blocking rule

> "Team must consist of at least one female contributor"
> "Women-integrated teams must have strong representation of women founders or developers."

This is an **eligibility gate, not a preference**. It appears in no artifact we have written. It
also carries USD 2,500 of the prize pool (All-Female Team category). Confirm the team composition
before any further engineering.

## Gaps requiring a decision

1. **Team composition** — at least one female contributor is mandatory. Blocking.
2. **USP not articulated** — 25% of the score, our weakest area, and cheap to fix in writing.
3. **Sustainability & Inclusivity (10%) unaddressed** — accessibility, affordability,
   multi-language. Partly cheap: a11y in the frontend and one extra language are achievable.
4. **No cricket / ICC connection** — criterion 4 rewards relevance "across ICC events". Women's
   cricket has a well-known injury-load problem (bowling workload) that our Risk Engine's shape
   already fits. Cross-sport applicability is separately a bonus, so a cricket-first model with
   general rules serves both.
5. **Scope vs. 29 days** — see below.

## Scope risk against the deadline

The plan is 62 tasks across 5 phases, including RLS with forced policies, trigger-based hash
chaining, external chain-head anchoring, mutation testing, and a full frontend. The track asks for
a **working prototype plus a 3-minute video**, and criterion 2 rewards architecture quality — but
criterion 6 rewards a demo that actually runs.

Two tasks are specifically at risk:

- **T4.9** — the SC-009 comprehension study needs 90% of real athletes to identify their top risk
  factor unaided. Recruiting and running that inside 29 days, alongside the build, is not
  realistic. Either start recruiting immediately or restate SC-009 as a post-submission
  validation.
- **T3.1 / T3.10** — external chain-head anchoring and rewritten-chain detection. Without them
  Principle V stays PARTIAL, and the submission must not claim independent auditability.

## Decisions taken (2026-09-06)

### 🔴 OPEN AND BLOCKING — team has no female contributor yet

The owner confirmed the team currently has **no female contributor**. The rule is not a
preference:

> "Team must consist of at least one female contributor"

**Consequence if unresolved**: the submission is ineligible, and 29 days of engineering produces
nothing that can be entered. This is the single highest-priority item in the project — higher than
any task in `tasks.md`, because every other task is worthless without it.

It is also the cheapest problem here to fix, and fixing it well serves the product: the brief
rewards "strong representation of women founders or developers", the All-Female Team category
carries USD 2,500, and a product about women athletes benefits from women building it. Recruit for
genuine contribution — a token name on a form is both against the spirit of the rule and useless
to the product.

**Recommended**: resolve this within the first week. Universities, women-in-tech communities,
sports-science students, and cricket clubs are all plausible sources. If it cannot be resolved,
stop and reconsider before investing the build effort.

### Scope: demo-first cut

Phases 0–2 plus the frontend are the submission. Deferred to a stated roadmap, not deleted:

| Deferred | Why it is safe to defer | Cost of deferring |
|---|---|---|
| T3.1 external chain-head anchoring | Nothing in the demo depends on it | **Principle V stays PARTIAL — the submission MUST NOT claim independent auditability** |
| T3.10 rewritten-chain detection | Depends on T3.1 | SC-005a unmet |
| T3.4 concurrent load tests | Prototype volumes make it moot | None at this scale |
| T4.9 comprehension study | Needs real athletes and recruiting lead time | SC-009 becomes post-submission validation |

Everything else in Phase 3 stays: the explanation service (T3.5–T3.8) is needed for the demo, and
the integrity check (T3.2) with altered-entry detection (T3.9) is cheap and demonstrates the audit
guarantee on stage.

### Cricket-first, rules general

Bowling workload is a well-documented injury driver in cricket, and it fits the Risk Engine's
existing shape — a load metric with a freshness window feeding deterministic rules. Model it as a
first-class input while keeping the rule structure sport-agnostic. This serves criterion 4
("across ICC events") and preserves the cross-sport applicability bonus simultaneously.

## What is already correct

- 3-minute video limit — T4.5 already matches.
- 5-slide deck limit — T4.6 already matches.
- IP terms create no conflict with anything in the constitution.
- Problem Statement 3 and Principle III are aligned at the level of wording, not just theme.
- Prototype Track is the right choice: we have a build plan, not only a concept.
