/* Translations — FR-028, SC-014.
   The requirement is deliberately not "translate the UI chrome". Refusal reasons and the
   evidence behind a score must translate too: a reason an athlete cannot read is a refusal
   without an explanation, which fails Principle VII. So rule explanations and refusal
   reasons are keyed here alongside the labels. */

(function () {
const I18N = {
  en: {
    dir: 'ltr', label: 'اردو',
    tagline: 'Injury risk, built for women athletes',
    signOut: 'Sign out', signInTitle: 'Sign in',
    signInHelp: 'Choose a demo profile. Each one exercises a different guarantee — including the ones where the system refuses to answer.',
    pasteToken: 'Or paste an access token', tokenLabel: 'Access token', continue: 'Continue',
    refresh: 'Refresh', planTitle: "This week's plan", metricsTitle: 'Your recorded data',
    addMetric: 'Add a measurement', metricKind: 'Measurement', metricValue: 'Value', save: 'Save',
    consentTitle: 'Your consent',
    consentHelp: 'Your health data is only processed for purposes you have agreed to. Withdrawing consent stops processing straight away — it is enforced by the database, not by the app.',
    coachTitle: 'Squad',
    coachHelp: 'Plans following elevated or high risk cannot activate without your approval.',
    auditTitle: 'Audit trail',
    footerNote: 'Training guidance only. Not a medical device, and not a diagnosis.',
    footerProvisional: 'Risk thresholds are provisional engineering defaults pending sports-science validation.',

    riskNow: 'Injury risk right now', outOf: 'out of 100', confidence: 'Confidence',
    ruleSet: 'Rule set', whyThisScore: 'Why this score',
    noRules: 'No risk rule was triggered by your current data.',
    femaleSpecific: 'Female-specific',
    notIncluded: 'Not included, because it has not been recorded',
    noDefault: 'No default value was substituted in its place.',
    coachNeeded: 'Coach approval required before any plan from this assessment can start.',
    measured: 'measured', hoursAgo: 'h ago', daysAgo: 'd ago',
    capturedAgainst: 'Freshness is measured from when each value was captured, not when it was entered.',

    refusedTitle: 'No score issued',
    refusedLead: 'ShePeak has withheld a risk score rather than guess. Here is exactly why:',
    escalated: 'This has been escalated to your coach.',
    whatToDo: 'What fixes it',

    metric: 'Measurement', value: 'Value', captured: 'Captured', status: 'Status',
    fresh: 'Current', staleLabel: 'Out of date',
    purpose: 'Purpose', granted: 'Granted', withdraw: 'Withdraw', grant: 'Grant',
    withdrawn: 'Withdrawn', active: 'Active',
    approve: 'Approve', reject: 'Reject', viewEvidence: 'View evidence',
    planNeedsApproval: 'Awaiting your approval', planApproved: 'Approved and active',
    planRejected: 'Rejected', noPlan: 'No plan — no score was issued',
    chainIntact: 'Chain intact', chainBroken: 'Chain broken',
    entries: 'entries', guaranteeScope: 'Guarantee',

    training_load: 'Training load', bowling_load: 'Bowling load', sleep: 'Sleep',
    soreness: 'Soreness', cycle_phase: 'Cycle phase',
    contraception_status: 'Hormonal contraception', iron_status: 'Ferritin',
    menstrual_cycle_phase: 'menstrual cycle phase', hormonal_contraception_status: 'contraception status',
  },

  ur: {
    dir: 'rtl', label: 'English',
    tagline: 'خواتین کھلاڑیوں کے لیے بنایا گیا انجری رسک',
    signOut: 'سائن آؤٹ', signInTitle: 'سائن ان',
    signInHelp: 'ایک ڈیمو پروفائل منتخب کریں۔ ہر ایک الگ ضمانت دکھاتا ہے — بشمول وہ جہاں سسٹم جواب دینے سے انکار کر دیتا ہے۔',
    pasteToken: 'یا رسائی ٹوکن پیسٹ کریں', tokenLabel: 'رسائی ٹوکن', continue: 'جاری رکھیں',
    refresh: 'تازہ کریں', planTitle: 'اس ہفتے کا پلان', metricsTitle: 'آپ کا ریکارڈ شدہ ڈیٹا',
    addMetric: 'پیمائش شامل کریں', metricKind: 'پیمائش', metricValue: 'قدر', save: 'محفوظ کریں',
    consentTitle: 'آپ کی رضامندی',
    consentHelp: 'آپ کا صحت کا ڈیٹا صرف ان مقاصد کے لیے استعمال ہوتا ہے جن پر آپ نے رضامندی دی ہے۔ رضامندی واپس لینے پر کارروائی فوراً رک جاتی ہے — یہ ڈیٹابیس نافذ کرتا ہے، ایپ نہیں۔',
    coachTitle: 'اسکواڈ',
    coachHelp: 'بلند یا زیادہ رسک والے پلان آپ کی منظوری کے بغیر فعال نہیں ہو سکتے۔',
    auditTitle: 'آڈٹ ریکارڈ',
    footerNote: 'صرف تربیتی رہنمائی۔ یہ طبی آلہ نہیں اور نہ ہی تشخیص ہے۔',
    footerProvisional: 'رسک کی حدیں عارضی ہیں، اسپورٹس سائنس کی توثیق باقی ہے۔',

    riskNow: 'اس وقت انجری کا رسک', outOf: '100 میں سے', confidence: 'اعتماد',
    ruleSet: 'رول سیٹ', whyThisScore: 'یہ اسکور کیوں',
    noRules: 'آپ کے موجودہ ڈیٹا سے کوئی رسک رول متحرک نہیں ہوا۔',
    femaleSpecific: 'خواتین کے لیے مخصوص',
    notIncluded: 'شامل نہیں، کیونکہ یہ ریکارڈ نہیں کیا گیا',
    noDefault: 'اس کی جگہ کوئی ڈیفالٹ قدر استعمال نہیں کی گئی۔',
    coachNeeded: 'اس تشخیص سے بننے والا کوئی بھی پلان شروع کرنے سے پہلے کوچ کی منظوری ضروری ہے۔',
    measured: 'پیمائش', hoursAgo: ' گھنٹے پہلے', daysAgo: ' دن پہلے',
    capturedAgainst: 'تازگی اس وقت سے ناپی جاتی ہے جب پیمائش ہوئی، نہ کہ جب درج کی گئی۔',

    refusedTitle: 'کوئی اسکور جاری نہیں کیا گیا',
    refusedLead: 'ShePeak نے اندازہ لگانے کے بجائے رسک اسکور روک دیا ہے۔ وجہ یہ ہے:',
    escalated: 'یہ آپ کے کوچ کو بھیج دیا گیا ہے۔',
    whatToDo: 'اسے کیسے ٹھیک کریں',

    metric: 'پیمائش', value: 'قدر', captured: 'ریکارڈ ہوا', status: 'حالت',
    fresh: 'تازہ', staleLabel: 'پرانا',
    purpose: 'مقصد', granted: 'دی گئی', withdraw: 'واپس لیں', grant: 'دیں',
    withdrawn: 'واپس لی گئی', active: 'فعال',
    approve: 'منظور کریں', reject: 'مسترد کریں', viewEvidence: 'شواہد دیکھیں',
    planNeedsApproval: 'آپ کی منظوری کا منتظر', planApproved: 'منظور شدہ اور فعال',
    planRejected: 'مسترد شدہ', noPlan: 'کوئی پلان نہیں — کوئی اسکور جاری نہیں ہوا',
    chainIntact: 'چین محفوظ', chainBroken: 'چین ٹوٹی ہوئی',
    entries: 'اندراجات', guaranteeScope: 'ضمانت',

    training_load: 'ٹریننگ لوڈ', bowling_load: 'باؤلنگ لوڈ', sleep: 'نیند',
    soreness: 'پٹھوں کا درد', cycle_phase: 'ماہواری کا مرحلہ',
    contraception_status: 'ہارمونل مانع حمل', iron_status: 'فیریٹن',
    menstrual_cycle_phase: 'ماہواری کا مرحلہ', hormonal_contraception_status: 'مانع حمل کی حالت',
  },
};

/* Band names and rule explanations translate too — this is the SC-014 requirement.
   English rule text comes from the engine itself (it is the same computation that produced
   the score); Urdu is keyed by rule_id so the athlete reads the same fact, not a summary. */
const BANDS = {
  en: { low:'Low', moderate:'Moderate', elevated:'Elevated', high:'High' },
  ur: { low:'کم', moderate:'درمیانہ', elevated:'بلند', high:'زیادہ' },
};

const RULES_UR = {
  load_spike: 'ٹریننگ لوڈ آپ کی بنیادی سطح سے کافی زیادہ ہے۔',
  bowling_workload: 'اس دورانیے میں بہت زیادہ اوورز کرائے گئے ہیں۔',
  sleep_debt: 'نیند بحالی کی مطلوبہ حد سے کم ہے۔',
  high_soreness: 'خود بتایا گیا پٹھوں کا درد زیادہ ہے۔',
  acl_ovulatory_laxity: 'بیضہ دانی کا مرحلہ: ایسٹروجن بڑھنے سے لگامنٹ ڈھیلے ہوتے ہیں اور ACL انجری کا خطرہ بڑھتا ہے۔',
  luteal_recovery_cost: 'لیوٹیل مرحلہ: جسمانی درجہ حرارت اور دباؤ بڑھنے سے بحالی مشکل ہوتی ہے۔',
  red_s_amenorrhoea: 'ماہواری غیر موجود ریکارڈ ہوئی اور مانع حمل استعمال نہیں — یہ RED-S کی علامت ہے، ہڈی کی چوٹ کا خطرہ۔',
  iron_deficiency: 'فیریٹن کھلاڑیوں کی 30 ng/mL حد سے کم ہے، جو آکسیجن اور بحالی متاثر کرتا ہے۔',
};

const REFUSAL_UR = {
  missing_required_metric: 'ضروری پیمائش ریکارڈ نہیں کی گئی۔',
  stale_metric: 'ضروری پیمائش بہت پرانی ہو چکی ہے۔',
  low_confidence: 'دستیاب ڈیٹا سے اعتماد مطلوبہ حد سے کم ہے۔',
  no_baseline: 'ابھی تک کوئی بنیادی ٹریننگ لوڈ موجود نہیں۔',
  out_of_scope_medical: 'یہ درخواست طبی تشخیص کے دائرے میں آتی ہے۔',
};

/* Plan content is deterministic and band-keyed, so it translates the same way the rules
   do — by key, not by machine translation of the server's English. */
const PLAN_UR = {
  low: { headline: 'حسبِ منصوبہ جاری رکھیں',
    sessions: ['معمول کا تربیتی ہفتہ', 'موجودہ لوڈ برقرار رکھیں', 'روزانہ ڈیٹا درج کرتی رہیں'] },
  moderate: { headline: 'معمولی کمی اور قریبی نگرانی',
    sessions: ['حجم تقریباً 10% کم کریں', 'ایک مکمل آرام کا دن شامل کریں', 'نیند کو ترجیح دیں'] },
  elevated: { headline: 'نمایاں ڈی لوڈ — کوچ کی منظوری ضروری',
    sessions: ['حجم تقریباً 25% کم کریں', 'ایک سخت سیشن کی جگہ تکنیکی کام کریں',
               'مسلسل دو راتیں 8 گھنٹے سے زیادہ نیند'] },
  high: { headline: 'بڑا ڈی لوڈ — کوچ کی منظوری ضروری',
    sessions: ['حجم تقریباً 40% کم کریں', 'اس ہفتے کوئی سخت یا زیادہ اثر والا کام نہیں',
               'مکمل تربیت پر واپسی سے پہلے کوچ سے مشورہ کریں'] },
};

window.SHEPEAK_I18N = { I18N, BANDS, RULES_UR, REFUSAL_UR, PLAN_UR };
})();
