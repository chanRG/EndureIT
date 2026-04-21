-- Claude AI audit log: tracks every API call for cost monitoring.
-- No raw prompt text or PII is stored here.

CREATE TABLE IF NOT EXISTS claude_audit_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    feature     VARCHAR(100)  NOT NULL,   -- e.g. 'weekly_review', 'meal_variations', 'pdf_parse'
    model       VARCHAR(100)  NOT NULL,
    input_tokens           INTEGER NOT NULL DEFAULT 0,
    output_tokens          INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens      INTEGER NOT NULL DEFAULT 0,
    cache_write_tokens     INTEGER NOT NULL DEFAULT 0,
    outcome     VARCHAR(20)   NOT NULL DEFAULT 'ok',  -- 'ok' | 'error' | 'fallback'
    error_summary TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_claude_audit_logs_user_id   ON claude_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_claude_audit_logs_created_at ON claude_audit_logs(created_at DESC);
