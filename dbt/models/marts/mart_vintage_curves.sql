-- Vintage-style analysis: cumulative default rates by credit cohort across 6 observation months.
-- Cohorts are defined by credit limit band; months are Apr→Sep 2005 (the observation window).
-- This mirrors how lenders track portfolio aging over time.
WITH base AS (
    SELECT * FROM {{ ref('stg_credit_default') }}
),

-- Month-by-month delinquency status — each row is one client in one month
monthly_status AS (
    SELECT id, credit_limit, is_default,
           1 AS month_num, 'Apr 2005' AS obs_month, pay_status_apr AS pay_status, bill_amt_apr AS balance
    FROM base
    UNION ALL
    SELECT id, credit_limit, is_default,
           2, 'May 2005', pay_status_may, bill_amt_may
    FROM base
    UNION ALL
    SELECT id, credit_limit, is_default,
           3, 'Jun 2005', pay_status_jun, bill_amt_jun
    FROM base
    UNION ALL
    SELECT id, credit_limit, is_default,
           4, 'Jul 2005', pay_status_jul, bill_amt_jul
    FROM base
    UNION ALL
    SELECT id, credit_limit, is_default,
           5, 'Aug 2005', pay_status_aug, bill_amt_aug
    FROM base
    UNION ALL
    SELECT id, credit_limit, is_default,
           6, 'Sep 2005', pay_status_sep, bill_amt_sep
    FROM base
),

with_cohort AS (
    SELECT
        *,
        CASE
            WHEN credit_limit <= 50000  THEN 'Micro (<50K)'
            WHEN credit_limit <= 150000 THEN 'Small (50K-150K)'
            WHEN credit_limit <= 300000 THEN 'Medium (150K-300K)'
            ELSE 'Large (>300K)'
        END AS cohort
    FROM monthly_status
)

SELECT
    cohort,
    month_num,
    obs_month,
    COUNT(DISTINCT id)                                                      AS loan_count,
    SUM(CASE WHEN pay_status >= 3 THEN 1 ELSE 0 END)                      AS delinquent_count,
    SUM(is_default)                                                         AS default_count,
    ROUND(SUM(CASE WHEN pay_status >= 3 THEN 1 ELSE 0 END)::DOUBLE
          / COUNT(DISTINCT id) * 100, 2)                                    AS delinquency_rate_pct,
    ROUND(SUM(is_default)::DOUBLE / COUNT(DISTINCT id) * 100, 2)          AS default_rate_pct,
    ROUND(AVG(balance), 0)                                                  AS avg_balance
FROM with_cohort
GROUP BY cohort, month_num, obs_month
ORDER BY cohort, month_num
