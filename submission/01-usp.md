# ShePeak — What makes it different

**Problem Statement 3: Athlete Health, Performance & Inclusivity | Prototype Track**

## In one sentence

ShePeak is an injury-risk system for women athletes where the safety guarantees are enforced
by code and the database — not promised by a model — so a coach can interrogate every number
and no plan can reach an athlete without a human saying yes.

## The gap we are attacking

Sports science defaults to male physiology. Most athlete-monitoring tools carry that default
forward and then add "female-friendly" features on top: a cycle tracker beside the dashboard,
a wellness questionnaire, a colour change.

That layering hides a specific, costly failure. **Absent menstruation is a clinical signal —
RED-S, carrying bone-stress injury risk. In almost every system it is stored as the same
database null as "she didn't fill the form in."** One is a warning; the other is a gap. Collapse
them and the athlete most at risk looks identical to the athlete who was simply busy.

ShePeak treats those as three distinct states — *not recorded*, *recorded absent*, *suppressed
by contraception* — and it is a test that fails the build if anyone merges them.

## Three things we do that we have not seen shipped together

### 1. The guarantee is in the code, not in the model

Every risk score comes from a pure, deterministic rules module with **no network access, no
database, and no LLM** — enforced by an automated import test, not a code-review convention.
The rule set identifies itself by a content hash, so "version-pinned" is a fact rather than a
label: change a threshold, and the version changes with it.

The language model may only rephrase an explanation that has already been computed. Before any
response is serialised, the narrative is re-checked against the deterministic verdict. **If they
disagree, we return an error rather than the narrative.** Most AI health products cannot make
that statement, because the model is the decision.

*Why it matters:* identical inputs produce an identical score, every time — proven by
repeatability trials in the test suite. A coach can be told why, and the answer will be the
same tomorrow.

### 2. Refusal is a product feature, not an error state

When data is missing, stale beyond its declared window, or confidence falls below 0.7,
ShePeak **withholds the score, states exactly which input was at fault and how old it was, and
escalates to the coach.** No partial answer. No best guess.

Our demo deliberately includes an athlete who gets no score at all. The screen for her is not
an error toast — it is a calm, designed panel explaining what is missing. We think a system
that knows when to say nothing is worth more to an athlete than one that always has an answer.

### 3. Consent and audit are enforced below the application

Consent is enforced by PostgreSQL row-level security with `FORCE ROW LEVEL SECURITY`, on a
connection whose role owns no tables and holds neither `SUPERUSER` nor `BYPASSRLS`. Forget to
bind the caller's identity and the query returns **zero rows** — the failure mode is silence,
not exposure. Every decision, including every refusal and every denied approval attempt, is
appended to a hash-chained audit log before the response reaches the caller.

*Why it matters:* an application-layer check protects you until the first caller that skips the
application. This one holds even then.

## Human-in-the-loop that is real, not nominal

Plans following **elevated or high** risk require the coach — the athlete cannot self-approve.
Below that band she can.

The interesting part is the edge that rule creates. An athlete with **no assigned coach** and an
elevated risk score has no authorised approver, so her plan cannot activate at all. It would
have been easy to fall back to self-approval there. We fail closed instead, and tell her why,
because a guarantee with a convenient exception is not a guarantee.

An approval is bound to a hash of the exact plan content, so it cannot survive a change to the
plan it approved.

## Built for cricket, useful beyond it

Bowling workload — overs, spell density, consecutive playing days — is a first-class input,
matching a well-documented injury driver in cricket. The rule structure stays sport-agnostic:
the engine runs unchanged for an athletics sprinter in our demo. Cricket-first, not cricket-only.

## What we will not claim

We think this matters as much as the claims.

- **The audit log is tamper-evident, not tamper-proof.** It detects an altered entry. It does
  not defend against a database operator who disables the triggers and rewrites the chain —
  that needs external anchoring of the chain head, which is specified, scheduled, and *not
  built yet*. We do not describe this as independently verifiable.
- **Risk band boundaries are provisional engineering defaults** and are labelled as such in the
  product, the code, and the specification. They need sports-science validation before any
  non-prototype use.
- **ShePeak is not a medical device.** It gives training guidance. Anything that would
  constitute diagnosis or treatment is refused and escalated to a qualified human.

## Evidence this is real

- **181 automated tests**, including refusal-path tests for every fail-closed condition, live
  PostgreSQL tests that attempt RLS bypass and audit tampering, and repeatability trials.
- A ratified project constitution, an architecture decision record, and a specification whose
  29 requirements each trace to a task and a test.
- The whole thing runs from `docker compose up` and one seed script.
