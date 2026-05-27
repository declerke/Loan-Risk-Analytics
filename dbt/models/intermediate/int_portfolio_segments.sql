-- Enrich delinquency-classified loans with product type (derived from bank marketing),
-- age bands, and credit size buckets for portfolio segmentation analysis.
WITH delinquency AS (
    SELECT * FROM {{ ref('int_loan_delinquency_buckets') }}
),

segmented AS (
    SELECT
        id,
        credit_limit,
        age,
        education_level,
        marital_status,
        dpd_bucket,
        risk_grade,
        is_default,
        outstanding_balance,
        total_payments_6m,

        CASE
            WHEN age < 30 THEN '18-29'
            WHEN age < 40 THEN '30-39'
            WHEN age < 50 THEN '40-49'
            WHEN age < 60 THEN '50-59'
            ELSE '60+'
        END AS age_band,

        CASE
            WHEN credit_limit <= 50000  THEN 'Micro (<50K)'
            WHEN credit_limit <= 150000 THEN 'Small (50K-150K)'
            WHEN credit_limit <= 300000 THEN 'Medium (150K-300K)'
            ELSE 'Large (>300K)'
        END AS credit_size_bucket,

        -- Utilisation rate: outstanding balance vs credit limit
        CASE
            WHEN credit_limit > 0
            THEN ROUND(outstanding_balance / credit_limit::DOUBLE * 100, 2)
            ELSE 0
        END AS utilisation_rate_pct,

        -- NPL flag: loans 90+ DPD are classified as non-performing
        CASE WHEN dpd_bucket = '90+ DPD' OR is_default = 1 THEN 1 ELSE 0 END AS is_npl

    FROM delinquency
)

SELECT * FROM segmented
