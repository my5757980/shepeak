# ShePeak — Solution Overview

**ICC × Ignyte Hackathon** · Problem Statement 3: Athlete Health, Performance & Inclusivity
**Track:** Prototype · **Date:** September 2026

---

## Problem

Women athletes carry injury risks that mainstream monitoring tools do not model. ACL rupture
occurs at markedly higher rates in women than men, and its likelihood shifts across the
menstrual cycle. Relative Energy Deficiency in Sport (RED-S) presents through absent
menstruation and drives bone-stress injury. Iron deficiency is far more common and degrades
recovery. None of these exist in a model calibrated on male physiology.

The tools that do exist tend to add female features on top of a male-default core. That
produces a specific, dangerous ambiguity: **an athlete who records that her period has stopped
looks identical, in the database, to an athlete who simply did not fill in the form.** One is a
clinical warning sign. The other is a blank. Systems that cannot tell them apart will miss the
athlete who most needs attention.

Meanwhile, AI-driven training tools increasingly let a model decide what an athlete should do —
an unreproducible authority over a human body, usually with no audit trail and no human
required to agree.

## Solution

ShePeak monitors training load and recovery markers for women athletes, produces a
deterministic injury-risk score with full evidence, proposes a training and recovery plan, and
requires a human to approve it before it can take effect.

**How it works.** Metrics are entered by the athlete or coach, each with the time it was
*captured* recorded separately from when it was entered. A pure rules engine — no network, no
database, no language model — evaluates them and returns either a score with its complete
evidence, or a refusal with a stated reason. A plan is generated deterministically from the
resulting risk band and held inactive until approved. Every outcome is written to a
hash-chained audit log before the response is returned.

**What is modelled specifically for women.** Menstrual cycle phase (including ACL risk in the
ovulatory phase and the raised recovery cost of the luteal phase), hormonal contraception
status, RED-S indicators, iron status, and — for cricket — bowling workload. Cycle data is
stored in three distinct states, never collapsed, so *recorded absent* triggers a RED-S
assessment while *not recorded* does not.

**Where the guarantees live.** In code and in the database, never in the model:

| Guarantee | Enforced by |
|---|---|
| Scores are deterministic and reproducible | Pure engine; import-boundary test; content-hashed rule set |
| The LLM cannot decide anything | It only rephrases; the narrative is re-checked against the verdict and discarded on conflict |
| Missing or stale data yields no answer | Per-metric freshness windows and a 0.7 confidence floor; refusal is a returned result, not an exception |
| No plan reaches an athlete unapproved | Tiered gate: coach mandatory at elevated/high; approval bound to a content hash |
| Health data needs consent | PostgreSQL row-level security with FORCE, on a non-owner NOBYPASSRLS role |
| Every decision is recorded | Append-only hash-chained audit written before the response |

## Impact for women in sport

**Visibility.** Every score names the female-specific factors that produced it, in the
athlete's own language. A coach sees *why* — "ovulatory phase: raised oestrogen is associated
with increased ligament laxity" — not an opaque number.

**Equity by construction, not by intention.** Where a sex-specific input is missing, ShePeak
states the absence and substitutes nothing. A male-default baseline is not a fallback; it is
forbidden, and a test enforces it.

**Agency.** The athlete owns her consent per purpose and can withdraw it, which stops
processing at the database layer. She sees her own evidence, not a score handed down.

**Accessibility and reach.** The interface meets accessibility requirements — keyboard and
screen-reader operable, never conveying meaning by colour alone — and runs in English and Urdu
with full right-to-left support. Crucially the *refusal reasons and score evidence* are
translated, not only the menus: a reason an athlete cannot read is no explanation at all.

## Status and honesty

Working prototype: deterministic engine, live PostgreSQL enforcement, API, and a responsive
bilingual interface. **112 automated tests pass**, including refusal paths, RLS bypass attempts,
audit tamper detection, and score repeatability trials.

Three limits we state rather than hide:

1. The audit log is **tamper-evident, not independently verifiable**. It detects an altered
   entry; it does not defend against a database operator rewriting the chain. External
   anchoring of the chain head is specified and on the roadmap.
2. **Risk thresholds are provisional engineering defaults** pending sports-science validation.
   They are labelled as provisional in the product itself.
3. ShePeak is **not a medical device**. Diagnosis and treatment are out of scope and refused.

## Why it scales beyond this prototype

The rules are sport-agnostic with cricket-specific inputs layered on, so the same engine ran
unchanged for an athletics athlete in our demo. Metric sources are modelled generally enough
that wearable integration can be added without touching the risk, refusal, or consent rules.
The consent and audit layers are properties of the schema, so they extend to every new feature
rather than needing to be re-implemented in each one.
