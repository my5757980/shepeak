# ShePeak — 3-minute demo video script

**Hard limit: 3:00.** Timings below total 2:52, leaving room to breathe.

**Before recording**

```bash
docker compose up -d
cd backend && python seed.py
python -m uvicorn api.main:app --app-dir src --port 8000
```

Open `http://localhost:8000`. Browser at 1280×800, zoom 110%, no bookmarks bar. Have a terminal
ready in a second window for the test run at 2:05.

---

### 0:00–0:20 — The problem, concretely

> "Women athletes face injury risks that most monitoring tools simply don't model. But here's
> the specific failure I want to show you.
>
> In almost every athlete system, an athlete recording that her period has stopped, and an
> athlete who just didn't fill in the form, produce the *same database null*.
>
> One of those is a RED-S warning sign — it carries bone-stress injury risk. The other is a
> blank. If your system can't tell them apart, you will miss the athlete who most needs you."

*On screen:* title card, then the two identical NULL cells.

---

### 0:20–0:55 — A score that shows its working

*Click Fatima Noor.*

> "This is Fatima. Her risk is 94 — high. And every number here can be interrogated.
>
> The largest contributor is a training load spike. But look at the second one: **menstruation
> recorded as absent, while not on hormonal contraception** — that's the RED-S signal, worth 25
> points. Tagged female-specific, because a model built on male defaults doesn't have this rule
> at all.
>
> Each card shows the exact metrics used, when they were captured, and the rule version that
> fired. This isn't a story written about the score afterwards — it's the same computation that
> produced it."

*Scroll slowly through the evidence cards. Pause on the RED-S card.*

---

### 0:55–1:20 — It refuses

*Sign out, click Sana Iqbal.*

> "Now Sana. No score at all.
>
> Her soreness reading is 31 hours old — past its 24-hour window. So ShePeak withholds the
> score, tells her exactly which input was stale and how stale, and escalates to her coach.
>
> Notice this isn't an error message. It's a designed screen. A system that knows when to say
> nothing is worth more to an athlete than one that always has an answer."

*On screen:* the refusal panel, full width.

---

### 1:20–1:50 — A human has to say yes

*Sign in as Coach Meera Devi.*

> "This is the coach view. Aisha is elevated, Fatima is high — and both plans are sitting here
> inactive, waiting for her.
>
> The athlete cannot approve these herself. Below elevated she can; at elevated and above, only
> the coach.
>
> And here's the edge that rule creates. Zainab is also at elevated risk — but she has no coach
> assigned. So her plan can't activate *at all*. We could have let her self-approve. We fail
> closed instead, and tell her why. A guarantee with a convenient exception isn't a guarantee."

*Approve Aisha's plan. Show the state change.*

---

### 1:50–2:20 — Enforced below the application

*Switch to the terminal. Run `python -m pytest tests/security -q`.*

> "These guarantees aren't in the app code — they're in the database.
>
> Consent runs on PostgreSQL row-level security, forced, on a role that owns no tables and has
> no bypass privileges. Forget to bind the caller's identity and you get *zero rows* — not
> everything.
>
> Every decision is appended to a hash-chained audit log before the response returns. These
> tests try to bypass the policies and tamper with the log. They fail, on purpose."

*On screen:* tests passing, then the audit trail panel showing chain intact.

> "And what we *don't* claim: this is tamper-evident, not independently verifiable. It detects
> an altered entry. It doesn't stop a database operator rewriting the chain — that needs
> external anchoring, which is designed and on the roadmap, not built. We'd rather say so."

---

### 2:20–2:40 — For every athlete

*Back to the browser. Click the language toggle.*

> "Same athlete, Urdu, right-to-left. And the important part — the *reasons* are translated,
> not just the menus. A refusal an athlete can't read is no explanation at all.
>
> The interface is keyboard and screen-reader operable, and nothing here depends on colour
> alone."

---

### 2:40–2:52 — Close

> "ShePeak: deterministic injury risk for women athletes. The guarantees are in the code and
> the database, not in a model. 112 tests, running today from a single compose file.
>
> Cricket-first — bowling workload is a first-class input — and the engine runs unchanged for
> other sports."

*End card: ShePeak · ICC × Ignyte · "Not a medical device. Thresholds provisional pending
sports-science validation."*

---

## Recording notes

- **Do not say** "fully auditable", "tamper-proof", or "independently verifiable" — the
  anchoring work is deferred and the claim would be false.
- **Do say** the thresholds are provisional. It reads as rigour, not weakness.
- If a demo step fails live, cut to the refusal screen — it is genuinely the strongest 20
  seconds in the video.
