-- Application role (ADR-0001 condition 2).
--
-- The application connects as a role that:
--   * owns no table          → FORCE ROW LEVEL SECURITY is not the only thing standing between
--                              it and the data, but ownership bypass is removed regardless
--   * is not a superuser     → superusers bypass row security entirely
--   * lacks BYPASSRLS        → same
-- Enforcement is only as real as this separation. See tests/security/.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shepeak_app') THEN
        CREATE ROLE shepeak_app LOGIN PASSWORD 'shepeak_dev_only_change_me'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
END
$$;

-- Explicitly strip the attributes even if the role pre-existed with them.
ALTER ROLE shepeak_app NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB;

GRANT USAGE ON SCHEMA public TO shepeak_app;

GRANT SELECT, INSERT, UPDATE ON
    athlete, coach, consent_record, health_metric,
    risk_assessment, plan_proposal, approval_record, escalation
TO shepeak_app;

-- Audit: insert and read only. No UPDATE, no DELETE — the triggers refuse anyway, but the
-- grant makes the intent explicit and removes the privilege as well as the ability.
GRANT SELECT, INSERT ON audit_entry TO shepeak_app;
GRANT USAGE, SELECT ON SEQUENCE audit_entry_seq_seq TO shepeak_app;

GRANT EXECUTE ON FUNCTION
    has_consent(uuid, consent_purpose),
    may_access_athlete(uuid, consent_purpose),
    current_athlete_id(), current_coach_id(), current_role_name(),
    verify_audit_chain(), audit_chain_head()
TO shepeak_app;

COMMIT;
