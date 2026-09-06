-- ShePeak schema — feature 001-athlete-health-core
-- Constitution v1.0.0. Entities follow spec.md "Key Entities".

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Identity ------------------------------------------------------------------------------

CREATE TABLE athlete (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name    text        NOT NULL,
    sport           text        NOT NULL DEFAULT 'cricket',
    coach_id        uuid        NULL,          -- NULL = unaffiliated; see FR-021 fail-closed
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE coach (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name    text        NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE athlete
    ADD CONSTRAINT athlete_coach_fk FOREIGN KEY (coach_id) REFERENCES coach (id);

-- Consent (FR-011, FR-012) --------------------------------------------------------------

CREATE TYPE consent_purpose AS ENUM (
    'injury_risk_scoring',
    'plan_generation',
    'explanation_generation'
);

CREATE TABLE consent_record (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id      uuid            NOT NULL REFERENCES athlete (id),
    purpose         consent_purpose NOT NULL,
    granted_at      timestamptz     NOT NULL DEFAULT now(),
    withdrawn_at    timestamptz     NULL,
    CONSTRAINT withdrawn_after_granted CHECK (withdrawn_at IS NULL OR withdrawn_at >= granted_at)
);

CREATE UNIQUE INDEX consent_active_uniq
    ON consent_record (athlete_id, purpose)
    WHERE withdrawn_at IS NULL;

-- A consent is live only while un-withdrawn. Used by every RLS policy on health data.
CREATE OR REPLACE FUNCTION has_consent(p_athlete uuid, p_purpose consent_purpose)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
    SELECT EXISTS (
        SELECT 1 FROM consent_record
        WHERE athlete_id = p_athlete
          AND purpose    = p_purpose
          AND withdrawn_at IS NULL
    );
$$;

-- Metrics (FR-024: capture time is distinct from ingestion time) -------------------------

CREATE TYPE metric_kind AS ENUM (
    'training_load', 'bowling_load', 'sleep', 'soreness',
    'cycle_phase', 'contraception_status', 'iron_status'
);

CREATE TABLE health_metric (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id      uuid        NOT NULL REFERENCES athlete (id),
    kind            metric_kind NOT NULL,
    value           text        NOT NULL,
    captured_at     timestamptz NOT NULL,   -- when the measurement was taken
    ingested_at     timestamptz NOT NULL DEFAULT now(),  -- when we received it
    source          text        NOT NULL DEFAULT 'manual',
    CONSTRAINT captured_not_future CHECK (captured_at <= ingested_at + interval '1 minute')
);

CREATE INDEX health_metric_lookup ON health_metric (athlete_id, kind, captured_at DESC);

-- Assessments and plans ------------------------------------------------------------------

CREATE TABLE risk_assessment (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id          uuid        NOT NULL REFERENCES athlete (id),
    score               int         NULL,     -- NULL when refused
    band                text        NULL,
    confidence          numeric(4,3) NULL,
    refusal_reason      text        NULL,
    refusal_detail      text        NULL,
    rule_set_version    text        NOT NULL,
    evidence            jsonb       NOT NULL DEFAULT '[]'::jsonb,
    fired_rules         jsonb       NOT NULL DEFAULT '[]'::jsonb,
    superseded_by       uuid        NULL REFERENCES risk_assessment (id),  -- FR-019
    computed_at         timestamptz NOT NULL,
    CONSTRAINT scored_or_refused CHECK (
        (score IS NOT NULL AND band IS NOT NULL AND refusal_reason IS NULL)
     OR (score IS NULL     AND refusal_reason IS NOT NULL)
    )
);

CREATE TYPE plan_state AS ENUM ('proposed', 'approved', 'rejected', 'superseded');

CREATE TABLE plan_proposal (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id          uuid        NOT NULL REFERENCES athlete (id),
    assessment_id       uuid        NOT NULL REFERENCES risk_assessment (id),
    version             int         NOT NULL DEFAULT 1,
    content             jsonb       NOT NULL,
    content_hash        text        NOT NULL,   -- FR-005: approval binds to this exact hash
    state               plan_state  NOT NULL DEFAULT 'proposed',
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE approval_record (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id             uuid        NOT NULL REFERENCES plan_proposal (id),
    approved_content_hash text      NOT NULL,   -- FR-005: invalidated if the plan changes
    approver_id         uuid        NOT NULL,
    approver_role       text        NOT NULL CHECK (approver_role IN ('coach', 'athlete')),
    decision            text        NOT NULL CHECK (decision IN ('approved', 'rejected')),
    decided_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE escalation (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id          uuid        NOT NULL REFERENCES athlete (id),
    reason              text        NOT NULL,
    detail              text        NOT NULL,
    routed_to           text        NOT NULL,
    raised_at           timestamptz NOT NULL DEFAULT now()
);

COMMIT;
