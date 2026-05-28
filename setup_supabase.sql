-- ============================================================
-- 육효의 세계 — Supabase 사용량 추적 테이블
-- Supabase 대시보드 > SQL Editor 에 붙여넣고 실행하세요.
-- ============================================================

CREATE TABLE IF NOT EXISTS usage (
    id       BIGSERIAL PRIMARY KEY,
    email    TEXT    NOT NULL,
    use_date DATE    NOT NULL DEFAULT CURRENT_DATE,
    count    INTEGER NOT NULL DEFAULT 1,
    UNIQUE (email, use_date)
);

-- 이메일 + 날짜 조합으로 빠른 조회를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_usage_email_date ON usage (email, use_date);

-- Row Level Security 비활성화 (service_role key 로 접근하므로 불필요)
ALTER TABLE usage DISABLE ROW LEVEL SECURITY;
