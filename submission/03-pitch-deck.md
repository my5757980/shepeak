# ShePeak — Pitch Deck (5 slides)

Content for the 5-slide limit. Speaker notes are for the presenter, not the slide.

---

## Slide 1 — The blank that hides a warning

> ### In most athlete systems, "my period stopped" and "I didn't fill in the form" are the same database null.
>
> One is a RED-S warning sign carrying bone-stress injury risk.
> The other is a blank.
>
> **ShePeak keeps them apart. A test fails the build if anyone merges them.**

*Visual:* two identical grey `NULL` cells side by side, then one turning red with the label
"RED-S indicator — bone-stress injury risk".

**Speaker notes:** Women athletes face injury risks that male-calibrated tools do not model —
ACL rupture varying across the menstrual cycle, RED-S, iron deficiency. Most products bolt a
cycle tracker onto a male-default core. That is where this ambiguity comes from. Open on the
concrete failure, not on the market statistics.

---

## Slide 2 — What ShePeak does

> ### Deterministic injury risk for women athletes, with the guarantees in code — not in the model.
>
> - **Scores from a pure rules engine** — no network, no database, no LLM. Same inputs, same score, always.
> - **The LLM only rephrases.** The narrative is re-checked against the verdict; if they disagree we return an error, not the narrative.
> - **Every score cites its evidence** — the metrics, their capture times, the rules and versions that fired.
> - **Cricket-first:** bowling workload is a first-class input. The rules stay sport-agnostic.

*Visual:* the athlete dashboard — 94/100 HIGH, with the "+25 RED-S" rule card and its
FEMALE-SPECIFIC tag visible.

**Speaker notes:** Point at the evidence cards. This is the same computation that produced the
score, not a story written about it afterwards.

---

## Slide 3 — Two guarantees you can test on stage

> ### 1. It refuses.
> Missing, stale, or low-confidence data → **no score.** It names the input, how old it was, and escalates to the coach.
> *A system that knows when to say nothing is worth more than one that always answers.*
>
> ### 2. It will not act without a human.
> Elevated or high risk → **coach approval only.** The athlete cannot self-approve.
> No coach assigned? The plan **cannot activate at all.** We fail closed rather than fall back.

*Visual:* left — the refusal panel for Sana ("soreness is 31.0h old"); right — the denial
message for an athlete with no coach.

**Speaker notes:** The no-coach case is the one to dwell on. It would have been easy to let her
self-approve. A guarantee with a convenient exception is not a guarantee.

---

## Slide 4 — Enforced below the application

> ### Consent and audit are properties of the database, not promises of the code.
>
> - **Row-level security with `FORCE`**, on a role that owns nothing and holds neither `SUPERUSER` nor `BYPASSRLS`. Forget to bind identity → **zero rows**, not everything.
> - **Append-only, hash-chained audit**, written before the response returns. Tampering is detected.
> - **Withdraw consent → processing stops**, enforced at the data layer.
>
> **112 automated tests** — refusal paths, RLS bypass attempts, audit tamper detection, repeatability trials.
>
> *What we don't claim:* tamper-evident, **not** independently verifiable. External anchoring is on the roadmap, not built.

*Visual:* terminal showing the security test run passing, beside the audit trail panel.

**Speaker notes:** The last line is deliberate. Judges hear sweeping audit claims from every
team. Saying precisely what our guarantee does and does not cover is the more credible claim.

---

## Slide 5 — Impact, and what's next

> ### Equity by construction
> - Every score names the female-specific factors behind it — **in English or Urdu, with the reasons translated, not just the menus.**
> - A missing sex-specific input is **stated, never defaulted.** No male baseline substitution — enforced by test.
> - Accessible: keyboard and screen-reader operable, no meaning by colour alone.
>
> ### Next
> External audit anchoring · sports-science validation of thresholds · wearable ingestion
> (the data model already separates capture time from ingestion time) · more sports
>
> **Running prototype. `docker compose up` and one seed script.**

*Visual:* the Urdu RTL dashboard beside the English one.

**Speaker notes:** Close on the roadmap being specific and already specified — thresholds
labelled provisional, anchoring designed, wearable seams already in the schema. Credible
next steps, not aspirations.
