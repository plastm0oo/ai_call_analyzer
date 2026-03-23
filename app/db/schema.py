CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS call_reports (
        id BIGSERIAL PRIMARY KEY,
        employee_id INTEGER NOT NULL,
        call_id TEXT NOT NULL UNIQUE,
        raw_score NUMERIC(10, 2),
        short_summary TEXT,
        result_text TEXT,
        script_comment TEXT,
        main_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
        missing_stages JSONB NOT NULL DEFAULT '[]'::jsonb,
        full_report_json JSONB NOT NULL,
        raw_json_path TEXT,
        pdf_path TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS call_dialog_stages (
        id BIGSERIAL PRIMARY KEY,
        report_id BIGINT NOT NULL REFERENCES call_reports(id) ON DELETE CASCADE,
        stage_name TEXT,
        found BOOLEAN NOT NULL DEFAULT FALSE,
        replicas JSONB NOT NULL DEFAULT '[]'::jsonb
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS call_mistakes (
        id BIGSERIAL PRIMARY KEY,
        report_id BIGINT NOT NULL REFERENCES call_reports(id) ON DELETE CASCADE,
        mistake_type TEXT,
        quote TEXT,
        description TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS call_recommendations (
        id BIGSERIAL PRIMARY KEY,
        report_id BIGINT NOT NULL REFERENCES call_reports(id) ON DELETE CASCADE,
        recommendation_type TEXT,
        recommendation_subtype TEXT,
        suggestion TEXT,
        raw_text TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_call_reports_call_id
    ON call_reports(call_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_call_dialog_stages_report_id
    ON call_dialog_stages(report_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_call_mistakes_report_id
    ON call_mistakes(report_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_call_recommendations_report_id
    ON call_recommendations(report_id)
    """,
]