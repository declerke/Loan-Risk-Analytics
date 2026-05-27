-- IFRS 9 ECL summary by stage — the key table for provision reporting.
-- Aggregates PD, LGD, EAD and ECL across all three IFRS 9 stages.
WITH ecl AS (
    SELECT * FROM {{ ref('int_ecl_inputs') }}
)

SELECT
    ifrs9_stage,
    credit_size_bucket,

    COUNT(*)                                                            AS loan_count,
    ROUND(SUM(ead), 0)                                                 AS total_ead,
    ROUND(SUM(ecl_amount), 0)                                          AS total_ecl,
    ROUND(AVG(empirical_pd) * 100, 2)                                  AS avg_pd_pct,
    ROUND(AVG(lgd) * 100, 2)                                           AS lgd_pct,

    -- ECL rate = ECL / EAD
    ROUND(
        CASE WHEN SUM(ead) > 0 THEN SUM(ecl_amount) / SUM(ead) * 100 ELSE 0 END,
        2
    )                                                                   AS ecl_rate_pct,

    -- Coverage by stage
    SUM(is_npl)                                                         AS npl_count,
    ROUND(
        CASE
            WHEN SUM(CASE WHEN is_npl = 1 THEN ead ELSE 0 END) > 0
            THEN SUM(CASE WHEN is_npl = 1 THEN ecl_amount ELSE 0 END) /
                 SUM(CASE WHEN is_npl = 1 THEN ead ELSE 0 END) * 100
            ELSE 0
        END, 2
    )                                                                   AS npl_provision_coverage_pct

FROM ecl
GROUP BY ifrs9_stage, credit_size_bucket
ORDER BY
    CASE ifrs9_stage WHEN 'Stage 1' THEN 1 WHEN 'Stage 2' THEN 2 ELSE 3 END,
    credit_size_bucket
