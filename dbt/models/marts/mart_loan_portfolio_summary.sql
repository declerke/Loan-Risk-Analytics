-- Portfolio-level summary grouped by segment for the overview dashboard.
WITH segments AS (
    SELECT * FROM {{ ref('int_portfolio_segments') }}
)

SELECT
    credit_size_bucket,
    age_band,
    education_level,
    dpd_bucket,
    COUNT(*)                                                AS loan_count,
    ROUND(SUM(credit_limit), 0)                            AS total_credit_limit,
    ROUND(AVG(credit_limit), 0)                            AS avg_credit_limit,
    ROUND(SUM(outstanding_balance), 0)                     AS total_outstanding,
    ROUND(AVG(outstanding_balance), 0)                     AS avg_outstanding,
    ROUND(AVG(utilisation_rate_pct), 2)                    AS avg_utilisation_pct,
    SUM(is_default)                                        AS default_count,
    SUM(is_npl)                                            AS npl_count,
    ROUND(SUM(is_default)::DOUBLE / COUNT(*) * 100, 2)    AS default_rate_pct,
    ROUND(SUM(is_npl)::DOUBLE / COUNT(*) * 100, 2)        AS npl_rate_pct
FROM segments
GROUP BY
    credit_size_bucket,
    age_band,
    education_level,
    dpd_bucket
ORDER BY
    credit_size_bucket,
    age_band
