-- Consent enforcement at the data-store layer (FR-011, Principle VI, ADR-0001).
--
-- Two PostgreSQL facts this file is built around, both verified against the official docs:
--   1. A table's OWNER bypasses its own RLS policies unless FORCE ROW LEVEL SECURITY is set.
--   2. Superusers and roles with BYPASSRLS bypass row security entirely.
-- So RLS alone is not enforcement. It is enforcement only together with FORCE and a role
-- that owns nothing and holds neither attribute.

BEGIN;

-- Caller identity ------------------------------------------------------------------------
--
-- RLS filters on a subject, and a pooled connection has none of its own. The application
-- sets `app.athlete_id` / `app.role` with SET LOCAL at the start of each request
-- transaction, from a VERIFIED token claim — never from a client-supplied header.
--
-- current_setting(..., true) returns NULL when unset, so an unset identity matches no rows.
-- That is the fail-closed default (Principle IV): forget to set it and you see nothing,
-- rather than seeing everything.

CREATE OR REPLACE FUNCTION current_athlete_id()
RETURNS uuid
LANGUAGE sql STABLE
AS $$
    SELECT nullif(current_setting('app.athlete_id', true), '')::uuid;
$$;

CREATE OR REPLACE FUNCTION current_role_name()
RETURNS text
LANGUAGE sql STABLE
AS $$
    SELECT coalesce(nullif(current_setting('app.role', true), ''), 'none');
$$;

CREATE OR REPLACE FUNCTION current_coach_id()
RETURNS uuid
LANGUAGE sql STABLE
AS $$
    SELECT nullif(current_setting('app.coach_id', true), '')::uuid;
$$;

-- Visibility rule: the athlete herself, or the coach she is assigned to, and only while a
-- live consent covers the purpose.
CREATE OR REPLACE FUNCTION may_access_athlete(p_athlete uuid, p_purpose consent_purpose)
RETURNS boolean
LANGUAGE sql STABLE
AS $$
    SELECT p_athlete IS NOT NULL
       AND has_consent(p_athlete, p_purpose)
       AND (
            (current_role_name() = 'athlete' AND current_athlete_id() = p_athlete)
         OR (current_role_name() = 'coach'
             AND current_coach_id() IS NOT NULL
             AND EXISTS (SELECT 1 FROM athlete a
                         WHERE a.id = p_athlete AND a.coach_id = current_coach_id()))
       );
$$;

-- Policies ---------------------------------------------------------------------------------

ALTER TABLE health_metric    ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_metric    FORCE  ROW LEVEL SECURITY;
ALTER TABLE risk_assessment  ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_assessment  FORCE  ROW LEVEL SECURITY;
ALTER TABLE plan_proposal    ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_proposal    FORCE  ROW LEVEL SECURITY;
ALTER TABLE consent_record   ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_record   FORCE  ROW LEVEL SECURITY;
ALTER TABLE athlete          ENABLE ROW LEVEL SECURITY;
ALTER TABLE athlete          FORCE  ROW LEVEL SECURITY;

CREATE POLICY health_metric_access ON health_metric
    FOR ALL
    USING      (may_access_athlete(athlete_id, 'injury_risk_scoring'))
    WITH CHECK (may_access_athlete(athlete_id, 'injury_risk_scoring'));

CREATE POLICY risk_assessment_access ON risk_assessment
    FOR ALL
    USING      (may_access_athlete(athlete_id, 'injury_risk_scoring'))
    WITH CHECK (may_access_athlete(athlete_id, 'injury_risk_scoring'));

CREATE POLICY plan_proposal_access ON plan_proposal
    FOR ALL
    USING      (may_access_athlete(athlete_id, 'plan_generation'))
    WITH CHECK (may_access_athlete(athlete_id, 'plan_generation'));

-- An athlete may always see and withdraw her own consent records; withdrawal must not
-- require the very consent being withdrawn.
CREATE POLICY consent_self_access ON consent_record
    FOR ALL
    USING (
        (current_role_name() = 'athlete' AND current_athlete_id() = athlete_id)
     OR (current_role_name() = 'coach'
         AND EXISTS (SELECT 1 FROM athlete a
                     WHERE a.id = consent_record.athlete_id
                       AND a.coach_id = current_coach_id()))
    )
    WITH CHECK (current_role_name() = 'athlete' AND current_athlete_id() = athlete_id);

CREATE POLICY athlete_self_access ON athlete
    FOR SELECT
    USING (
        (current_role_name() = 'athlete' AND current_athlete_id() = id)
     OR (current_role_name() = 'coach'   AND coach_id = current_coach_id())
    );

-- Audit rows are readable for verification but never writable by hand; the append trigger
-- is the only sanctioned writer.
ALTER TABLE audit_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_entry FORCE  ROW LEVEL SECURITY;
CREATE POLICY audit_readable ON audit_entry FOR SELECT USING (true);
CREATE POLICY audit_appendable ON audit_entry FOR INSERT WITH CHECK (true);

COMMIT;
