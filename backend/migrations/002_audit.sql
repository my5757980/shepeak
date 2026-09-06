-- Append-only, hash-chained audit log (ADR-0001, FR-008, FR-009, FR-010).
--
-- Scope of the guarantee, stated honestly: this is tamper-EVIDENT against the application
-- and every caller reaching the database through it. It is NOT tamper-proof against a
-- superuser, who can disable these triggers and recompute the chain. Independence from the
-- database operator requires FR-010a (external chain-head anchoring), which is deferred to
-- the roadmap. Until it ships, nothing may describe this log as "independently verifiable".

BEGIN;

CREATE TABLE audit_entry (
    seq             bigserial PRIMARY KEY,
    actor_id        text        NOT NULL,
    actor_role      text        NOT NULL,
    action          text        NOT NULL,
    subject_id      text        NULL,
    payload         jsonb       NOT NULL,
    rule_set_version text       NULL,
    model_version   text        NULL,          -- FR-008: LLM model id when one was involved
    prev_hash       text        NOT NULL,
    entry_hash      text        NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX audit_entry_subject ON audit_entry (subject_id, seq DESC);

-- Postgres has no canonical jsonb rendering; define a stable key-sorted one. Declared
-- before audit_canonical_form because SQL function bodies are validated at creation time.
CREATE OR REPLACE FUNCTION jsonb_canonical(j jsonb)
RETURNS text
LANGUAGE plpgsql IMMUTABLE
AS $$
DECLARE
    v_key   text;
    v_parts text[] := ARRAY[]::text[];
BEGIN
    CASE jsonb_typeof(j)
        WHEN 'object' THEN
            FOR v_key IN SELECT k FROM jsonb_object_keys(j) AS k ORDER BY 1 LOOP
                v_parts := v_parts || (to_json(v_key)::text || ':' || jsonb_canonical(j -> v_key));
            END LOOP;
            RETURN '{' || array_to_string(v_parts, ',') || '}';
        WHEN 'array' THEN
            RETURN '[' || coalesce((
                SELECT string_agg(jsonb_canonical(v), ',' ORDER BY ord)
                FROM jsonb_array_elements(j) WITH ORDINALITY AS t(v, ord)
            ), '') || ']';
        ELSE
            RETURN j::text;
    END CASE;
END;
$$;

-- Canonical serialisation for hashing. Any change here changes every subsequent hash, so
-- it is deliberately explicit rather than relying on jsonb's textual output ordering.
CREATE OR REPLACE FUNCTION audit_canonical_form(e audit_entry)
RETURNS text
LANGUAGE sql IMMUTABLE
AS $$
    SELECT concat_ws('|',
        e.seq::text,
        e.actor_id,
        e.actor_role,
        e.action,
        coalesce(e.subject_id, ''),
        jsonb_canonical(e.payload),
        coalesce(e.rule_set_version, ''),
        coalesce(e.model_version, ''),
        to_char(e.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US'),
        e.prev_hash
    );
$$;

-- Chain append. ADR-0001 condition 4: appends are serialised by an advisory lock, because
-- two concurrent inserts reading the same predecessor hash would fork the chain — and a
-- forked chain either fails verification or, worse, verifies over one of the two branches.
CREATE OR REPLACE FUNCTION audit_before_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_prev text;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtext('shepeak_audit_chain'));

    SELECT entry_hash INTO v_prev
    FROM audit_entry
    ORDER BY seq DESC
    LIMIT 1;

    NEW.prev_hash := coalesce(v_prev, repeat('0', 64));
    NEW.entry_hash := encode(
        digest(audit_canonical_form(NEW), 'sha256'), 'hex'
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER audit_chain_append
    BEFORE INSERT ON audit_entry
    FOR EACH ROW EXECUTE FUNCTION audit_before_insert();

-- Append-only enforcement (FR-009).
--
-- The attempt is written to the SERVER LOG rather than to a table: a BEFORE UPDATE trigger
-- that inserted an audit row and then raised would have that insert rolled back with the
-- rest of the transaction. The server log lives outside transaction scope, so it survives.
-- A production system would use an autonomous transaction (dblink / pg_background) — that
-- is the same open decision as ADR-0001 condition 5.
CREATE OR REPLACE FUNCTION audit_reject_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_seq text := 'n/a';
BEGIN
    -- OLD is not bound in a statement-level TRUNCATE trigger.
    IF TG_LEVEL = 'ROW' THEN
        v_seq := OLD.seq::text;
    END IF;
    RAISE LOG 'SHEPEAK_AUDIT_TAMPER_ATTEMPT op=% user=% seq=%', TG_OP, current_user, v_seq;
    RAISE EXCEPTION
        'audit_entry is append-only (Constitution Principle V): % denied for user %',
        TG_OP, current_user
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER audit_no_update
    BEFORE UPDATE ON audit_entry
    FOR EACH ROW EXECUTE FUNCTION audit_reject_mutation();

CREATE TRIGGER audit_no_delete
    BEFORE DELETE ON audit_entry
    FOR EACH ROW EXECUTE FUNCTION audit_reject_mutation();

CREATE TRIGGER audit_no_truncate
    BEFORE TRUNCATE ON audit_entry
    FOR EACH STATEMENT EXECUTE FUNCTION audit_reject_mutation();

-- Independent verification (FR-010). Needs only read access and the chain rule; it does not
-- trust the application. Returns the first divergence, or no rows if the chain is intact.
CREATE OR REPLACE FUNCTION verify_audit_chain()
RETURNS TABLE (seq bigint, problem text)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    r           audit_entry;
    v_expected  text := repeat('0', 64);
    v_recomputed text;
BEGIN
    FOR r IN SELECT * FROM audit_entry ORDER BY seq LOOP
        IF r.prev_hash <> v_expected THEN
            seq := r.seq;
            problem := format('broken link: prev_hash %s, expected %s', r.prev_hash, v_expected);
            RETURN NEXT;
            RETURN;
        END IF;

        v_recomputed := encode(digest(audit_canonical_form(r), 'sha256'), 'hex');
        IF v_recomputed <> r.entry_hash THEN
            seq := r.seq;
            problem := format('altered entry: stored %s, recomputed %s', r.entry_hash, v_recomputed);
            RETURN NEXT;
            RETURN;
        END IF;

        v_expected := r.entry_hash;
    END LOOP;
END;
$$;

-- The current chain head. FR-010a will publish this outside the database on an interval;
-- until then it is only readable from inside, which is exactly the limitation recorded above.
CREATE OR REPLACE FUNCTION audit_chain_head()
RETURNS TABLE (entry_count bigint, head_hash text)
LANGUAGE sql STABLE
AS $$
    SELECT count(*)::bigint,
           coalesce((SELECT entry_hash FROM audit_entry ORDER BY seq DESC LIMIT 1),
                    repeat('0', 64))
    FROM audit_entry;
$$;

COMMIT;
