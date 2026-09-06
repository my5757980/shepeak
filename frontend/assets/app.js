/* ShePeak client.
   Two design rules that come from the constitution rather than from taste:
   1. A refusal renders as a full, calm panel with its reason — never a red error toast.
      Withholding a score is the product working (Principle IV), so it must not look broken.
   2. Evidence is always on screen with the score, never behind a click. Principle VII says
      a coach must be able to interrogate the number; hiding the reasoning defeats that. */

const { I18N, BANDS, RULES_UR, REFUSAL_UR, PLAN_UR } = window.SHEPEAK_I18N;

const state = {
  token: localStorage.getItem('shepeak_token') || null,
  role: null,
  lang: localStorage.getItem('shepeak_lang') || 'en',
  athletes: [],
};

const $ = (id) => document.getElementById(id);
const t = (key) => I18N[state.lang][key] ?? I18N.en[key] ?? key;
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* ---------- API ---------- */

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) { signOut(); throw new Error('Session expired'); }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`);
  return body;
}

function toast(message) {
  const el = $('toast');
  el.textContent = message;
  el.hidden = false;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.hidden = true; }, 4200);
}

/* ---------- Language ---------- */

function applyLang() {
  const cfg = I18N[state.lang];
  document.documentElement.lang = state.lang;
  document.documentElement.dir = cfg.dir;
  document.body.dir = cfg.dir;
  $('langLabel').textContent = cfg.label;
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  localStorage.setItem('shepeak_lang', state.lang);
}

$('langToggle').addEventListener('click', () => {
  state.lang = state.lang === 'en' ? 'ur' : 'en';
  applyLang();
  render();
});

/* ---------- Sign in ---------- */

const DEMO = [
  { key: 'coach',   role: 'coach',   name: 'Coach Meera Devi', why: 'Approve or reject plans for the whole squad' },
  { key: 'priya',   role: 'athlete', name: 'Priya Raman',      why: 'Low risk — everything recorded' },
  { key: 'aisha',   role: 'athlete', name: 'Aisha Khan',       why: 'Elevated — ovulatory ACL risk + bowling load' },
  { key: 'fatima',  role: 'athlete', name: 'Fatima Noor',      why: 'High — RED-S indicator, invisible to male-default models' },
  { key: 'sana',    role: 'athlete', name: 'Sana Iqbal',       why: 'Refused — data out of date. Fail closed.' },
  { key: 'zainab',  role: 'athlete', name: 'Zainab Ali',       why: 'Elevated, no coach — plan cannot activate at all' },
];

async function loadProfiles() {
  let tokens = {};
  try { tokens = await (await fetch('/assets/demo-tokens.json')).json(); } catch { /* optional */ }

  $('demoProfiles').innerHTML = DEMO.map((p) => `
    <button class="profile" type="button" role="listitem" data-token="${esc(tokens[p.key] || '')}">
      <span class="role">${p.role}</span>
      <strong>${esc(p.name)}</strong>
      <span class="why">${esc(p.why)}</span>
    </button>`).join('');

  document.querySelectorAll('.profile').forEach((btn) => {
    btn.addEventListener('click', () => {
      const token = btn.dataset.token;
      if (!token) return toast('Run  python seed.py  to generate demo tokens.');
      signIn(token);
    });
  });
}

function signIn(token) {
  state.token = token;
  localStorage.setItem('shepeak_token', token);
  render();
}

function signOut() {
  state.token = null;
  state.role = null;
  localStorage.removeItem('shepeak_token');
  render();
}

$('signOut').addEventListener('click', signOut);
$('tokenGo').addEventListener('click', () => {
  const v = $('tokenInput').value.trim();
  if (v) signIn(v);
});

/* ---------- Rendering ---------- */

function bandChip(band) {
  const label = BANDS[state.lang]?.[band] ?? band;
  return `<span class="band-chip band-${esc(band)}">${esc(label)}</span>`;
}

function ruleText(rule) {
  // Urdu is keyed by rule_id so the athlete reads the same fact, not a machine translation.
  return state.lang === 'ur' ? (RULES_UR[rule.rule_id] || rule.because) : rule.because;
}

function refusalText(result) {
  return state.lang === 'ur' ? (REFUSAL_UR[result.reason] || result.detail) : result.detail;
}

function renderAssessment(a) {
  if (a.outcome === 'refused') {
    return `
      <section class="refusal" aria-labelledby="refHead">
        <h2 id="refHead">${bandChip('refused')} ${esc(t('refusedTitle'))}</h2>
        <p>${esc(t('refusedLead'))}</p>
        <p><strong>${esc(refusalText(a))}</strong></p>
        ${a.confidence != null ? `<p class="muted small">${esc(t('confidence'))}: ${a.confidence.toFixed(2)}</p>` : ''}
        <div class="notice">${esc(t('escalated'))}</div>
      </section>`;
  }

  const rules = (a.fired_rules || []).slice().sort((x, y) => y.points - x.points);
  const deg = Math.round((a.score / 100) * 360);
  const colour = `var(--${a.band})`;

  return `
    <section class="panel" aria-labelledby="scoreHead">
      <h2 id="scoreHead">${esc(t('riskNow'))}</h2>
      <div class="score-card">
        <div class="dial" style="background:conic-gradient(${colour} ${deg}deg, var(--line) ${deg}deg)">
          <div class="dial-inner">
            <span class="dial-score" style="color:${colour}">${a.score}</span>
            <span class="dial-of">${esc(t('outOf'))}</span>
          </div>
        </div>

        <div>
          <p>${bandChip(a.band)}</p>
          ${a.narrative ? `<p>${esc(a.narrative)}</p>` : ''}
          <p class="muted small">
            ${esc(t('confidence'))} ${a.confidence.toFixed(2)} ·
            ${esc(t('ruleSet'))} <span class="hash">${esc(a.rule_set_version)}</span>
          </p>
          ${a.requires_coach_approval ? `<div class="notice notice-warn">${esc(t('coachNeeded'))}</div>` : ''}
        </div>
      </div>

      <div class="evidence">
        <h3>${esc(t('whyThisScore'))}</h3>
        ${rules.length === 0
          ? `<p class="muted">${esc(t('noRules'))}</p>`
          : rules.map((r) => `
            <div class="rule">
              <span class="rule-points">+${r.points}</span>
              <div class="rule-body">
                <p class="rule-because">${esc(ruleText(r))}</p>
                <div>
                  ${r.is_sex_specific ? `<span class="tag tag-sex">${esc(t('femaleSpecific'))}</span>` : ''}
                  ${r.inputs.map((i) => `<span class="tag tag-src">${esc(t(i) || i)}</span>`).join('')}
                  <span class="tag tag-src">${esc(r.rule_id)} v${esc(r.rule_version)}</span>
                </div>
              </div>
            </div>`).join('')}

        ${(a.absent_sex_specific_inputs || []).length ? `
          <div class="notice">
            <strong>${esc(t('notIncluded'))}:</strong>
            ${a.absent_sex_specific_inputs.map((k) => esc(t(k) || k.replace(/_/g, ' '))).join(', ')}.
            ${esc(t('noDefault'))}
          </div>` : ''}
      </div>
    </section>`;
}

function fmtAge(hours) {
  // Days past 48h — "960.0h ago" is technically right and humanly useless.
  if (hours < 48) return `${hours.toFixed(1)}${t('hoursAgo')}`;
  return `${Math.round(hours / 24)}${t('daysAgo')}`;
}

function renderMetrics(metrics) {
  if (!metrics.length) return `<p class="muted">—</p>`;
  const now = Date.now();
  const windows = { training_load: 48, bowling_load: 48, sleep: 24, soreness: 24,
                    cycle_phase: 168, contraception_status: 2160, iron_status: 2160 };
  return `<div class="table-scroll"><table class="metric-table">
    <caption>${esc(t('capturedAgainst'))}</caption>
    <thead><tr>
      <th scope="col">${esc(t('metric'))}</th><th scope="col">${esc(t('value'))}</th>
      <th scope="col">${esc(t('captured'))}</th><th scope="col">${esc(t('status'))}</th>
    </tr></thead>
    <tbody>${metrics.map((m) => {
      const hours = (now - new Date(m.captured_at)) / 3.6e6;
      const stale = hours > (windows[m.kind] ?? 1e9);
      return `<tr>
        <th scope="row">${esc(t(m.kind) || m.kind)}</th>
        <td class="num">${esc(m.value)}</td>
        <td class="num">${fmtAge(hours)}</td>
        <td>${stale ? `<span class="stale">⚠ ${esc(t('staleLabel'))}</span>` : esc(t('fresh'))}</td>
      </tr>`;
    }).join('')}</tbody></table></div>`;
}

function renderPlan(plan, canDecide) {
  if (plan.outcome === 'no_plan') {
    return `<div class="notice notice-warn"><strong>${esc(t('noPlan'))}</strong><br>${esc(plan.detail)}</div>`;
  }
  const c = plan.content;
  const local = state.lang === 'ur' ? (PLAN_UR[c.derived_from_band] || {}) : {};
  const headline = local.headline || c.headline;
  const sessions = local.sessions || c.sessions || [];
  const stateLabel = plan.state === 'approved' ? t('planApproved')
                   : plan.state === 'rejected' ? t('planRejected') : t('planNeedsApproval');
  return `
    <p><strong>${esc(headline)}</strong></p>
    <p class="muted small">${stateLabel} · ${esc(c.load_change_pct)}% load</p>
    <ul>${sessions.map((s) => `<li>${esc(s)}</li>`).join('')}</ul>
    ${!canDecide && plan.state === 'proposed' && plan.requires_coach_approval
      ? `<div class="notice notice-warn">${esc(t('coachNeeded'))}</div>` : ''}
    ${canDecide && plan.state === 'proposed' ? `
      <div class="actions">
        <button class="btn btn-approve" data-plan="${esc(plan.plan_id)}" data-decision="approved">${esc(t('approve'))}</button>
        <button class="btn btn-reject"  data-plan="${esc(plan.plan_id)}" data-decision="rejected">${esc(t('reject'))}</button>
      </div>` : ''}
    <p class="muted small hash">hash ${esc((plan.content_hash || '').slice(0, 16))}…</p>`;
}

function renderConsent(consents, athleteId) {
  return `<div class="table-scroll"><table class="metric-table">
    <thead><tr>
      <th scope="col">${esc(t('purpose'))}</th><th scope="col">${esc(t('status'))}</th><th scope="col"></th>
    </tr></thead>
    <tbody>${consents.map((c) => {
      const live = !c.withdrawn_at;
      return `<tr>
        <th scope="row">${esc(c.purpose.replace(/_/g, ' '))}</th>
        <td>${live ? esc(t('active')) : esc(t('withdrawn'))}</td>
        <td><button class="btn btn-ghost" data-consent="${esc(c.purpose)}"
              data-athlete="${esc(athleteId)}" data-action="${live ? 'withdraw' : 'grant'}">
            ${live ? esc(t('withdraw')) : esc(t('grant'))}</button></td>
      </tr>`;
    }).join('')}</tbody></table></div>`;
}

async function renderAudit() {
  try {
    const v = await api('/api/audit/verify');
    const e = await api('/api/audit/entries?limit=6');
    $('auditPanel').hidden = false;
    $('auditSlot').innerHTML = `
      <p>
        <span class="${v.intact ? 'chain-ok' : 'chain-bad'}">
          ${v.intact ? '✓ ' + esc(t('chainIntact')) : '✕ ' + esc(t('chainBroken'))}
        </span>
        · ${v.entry_count} ${esc(t('entries'))}
      </p>
      <p class="hash">head ${esc(v.head_hash.slice(0, 32))}…</p>
      <p class="muted small"><strong>${esc(t('guaranteeScope'))}:</strong> ${esc(v.guarantee)}. ${esc(v.not_yet)}</p>
      <div class="table-scroll"><table class="metric-table"><tbody>
        ${e.entries.map((x) => `<tr>
          <td class="num">#${x.seq}</td><td>${esc(x.action)}</td>
          <td>${esc(x.actor_role)}</td>
          <td class="hash">${esc(x.entry_hash.slice(0, 12))}…</td>
        </tr>`).join('')}
      </tbody></table></div>`;
  } catch { $('auditPanel').hidden = true; }
}

/* ---------- Views ---------- */

async function renderAthlete() {
  const me = state.athletes[0];
  $('athleteName').textContent = me.display_name;
  $('athleteMeta').textContent = me.coach_name
    ? `${me.sport} · ${me.coach_name}`
    : `${me.sport} · no coach assigned`;

  $('assessmentSlot').innerHTML = '<div class="spinner" role="status" aria-label="Loading"></div>';
  const [assessment, metrics, consents] = await Promise.all([
    api(`/api/athletes/${me.id}/assessment`),
    api(`/api/athletes/${me.id}/metrics`),
    api(`/api/consent/${me.id}`),
  ]);

  $('assessmentSlot').innerHTML = renderAssessment(assessment);
  $('metricsSlot').innerHTML = renderMetrics(metrics.metrics);
  $('consentSlot').innerHTML = renderConsent(consents.consents, me.id);

  const plan = await api(`/api/athletes/${me.id}/plan`);
  $('planSlot').innerHTML = renderPlan(
    plan, state.role === 'athlete' && !plan.requires_coach_approval);

  $('metricForm').onsubmit = async (ev) => {
    ev.preventDefault();
    await api(`/api/athletes/${me.id}/metrics`, {
      method: 'POST',
      body: JSON.stringify({ kind: $('metricKind').value, value: $('metricValue').value }),
    });
    $('metricValue').value = '';
    toast('Saved');
    render();
  };

  bindActions();
  renderAudit();
}

async function renderCoach() {
  $('squadSlot').innerHTML = '<div class="spinner" role="status" aria-label="Loading"></div>';
  const cards = await Promise.all(state.athletes.map(async (a) => {
    const assessment = await api(`/api/athletes/${a.id}/assessment`).catch(() => null);
    let plan = null;
    if (assessment && assessment.outcome === 'assessed') {
      plan = await api(`/api/athletes/${a.id}/plan`).catch(() => null);
    }
    return { a, assessment, plan };
  }));

  $('squadSlot').innerHTML = cards.map(({ a, assessment, plan }) => `
    <article class="squad-card">
      <header>
        <h2>${esc(a.display_name)}</h2>
        ${assessment
          ? (assessment.outcome === 'refused'
              ? bandChip('refused')
              : `${bandChip(assessment.band)} <strong>${assessment.score}</strong>`)
          : ''}
      </header>
      ${assessment && assessment.outcome === 'refused'
        ? `<p class="muted">${esc(refusalText(assessment))}</p>`
        : assessment
          ? `<p class="muted small">${(assessment.fired_rules || []).length} contributing rules ·
              ${esc(t('confidence'))} ${assessment.confidence.toFixed(2)}</p>
             ${(assessment.fired_rules || []).filter((r) => r.is_sex_specific).map((r) =>
               `<p class="small">${esc(ruleText(r))}</p>`).join('')}`
          : '<p class="muted">—</p>'}
      ${plan ? renderPlan(plan, true) : ''}
    </article>`).join('');

  bindActions();
  renderAudit();
}

function bindActions() {
  document.querySelectorAll('[data-plan]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        const out = await api(`/api/plans/${btn.dataset.plan}/decision`, {
          method: 'POST',
          body: JSON.stringify({ decision: btn.dataset.decision }),
        });
        // A denial is the guarantee working — show its reason, not a generic failure.
        toast(out.allowed ? `Recorded: ${out.decision}` : out.detail);
      } catch (e) { toast(e.message); }
      render();
    });
  });

  document.querySelectorAll('[data-consent]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const { consent, athlete, action } = btn.dataset;
      try {
        await api(`/api/consent/${athlete}/${consent}/${action}`, { method: 'POST' });
        toast(action === 'withdraw' ? 'Consent withdrawn — processing stopped' : 'Consent granted');
      } catch (e) { toast(e.message); }
      render();
    });
  });
}

/* ---------- Root ---------- */

async function render() {
  applyLang();
  const signedIn = Boolean(state.token);
  $('signInView').hidden = signedIn;
  $('signOut').hidden = !signedIn;
  $('athleteView').hidden = true;
  $('coachView').hidden = true;
  $('auditPanel').hidden = true;

  if (!signedIn) { loadProfiles(); return; }

  try {
    const me = await api('/api/me');
    state.role = me.role;
    state.athletes = me.athletes;

    if (me.role === 'athlete') { $('athleteView').hidden = false; await renderAthlete(); }
    else { $('coachView').hidden = false; await renderCoach(); }
  } catch (e) { toast(e.message); }
}

$('refreshBtn').addEventListener('click', render);
$('coachRefresh').addEventListener('click', render);

render();
