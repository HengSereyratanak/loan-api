CREATE TABLE IF NOT EXISTS predictions (
    id               SERIAL PRIMARY KEY,
    income           NUMERIC(12, 2) NOT NULL,
    loan_amount      NUMERIC(12, 2) NOT NULL,
    term_months      INTEGER        NOT NULL,
    credit_score     INTEGER        NOT NULL,
    employment_years NUMERIC(5, 2)  NOT NULL,
    score            NUMERIC(6, 4)  NOT NULL,
    risk_band        VARCHAR(10)    NOT NULL,
    decision         VARCHAR(10)    NOT NULL,
    model_version    VARCHAR(20)    NOT NULL,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
