-- Classify each loan by worst delinquency bucket across the 6-month observation window.
-- DPD (Days Past Due) buckets align with CBK loan classification standards.
WITH base AS (
    SELECT * FROM {{ ref('stg_credit_default') }}
),

max_dpd AS (
    SELECT
        *,
        GREATEST(
            COALESCE(pay_status_sep, -2),
            COALESCE(pay_status_aug, -2),
            COALESCE(pay_status_jul, -2),
            COALESCE(pay_status_jun, -2),
            COALESCE(pay_status_may, -2),
            COALESCE(pay_status_apr, -2)
        ) AS max_months_delayed
    FROM base
)

SELECT
    id,
    credit_limit,
    age,
    gender,
    education_level,
    marital_status,
    is_default,
    max_months_delayed,
    CASE
        WHEN max_months_delayed <= 0  THEN 'Current'
        WHEN max_months_delayed = 1   THEN '1-30 DPD'
        WHEN max_months_delayed = 2   THEN '31-60 DPD'
        WHEN max_months_delayed = 3   THEN '61-90 DPD'
        ELSE '90+ DPD'
    END                                         AS dpd_bucket,
    CASE
        WHEN max_months_delayed <= 0  THEN 1    -- Performing
        WHEN max_months_delayed <= 2  THEN 2    -- Watch
        WHEN max_months_delayed <= 3  THEN 3    -- Substandard
        ELSE 4                                   -- Doubtful/Loss
    END                                         AS risk_grade,
    bill_amt_sep                                AS outstanding_balance,
    pay_amt_sep + pay_amt_aug + pay_amt_jul
        + pay_amt_jun + pay_amt_may + pay_amt_apr AS total_payments_6m
FROM max_dpd
