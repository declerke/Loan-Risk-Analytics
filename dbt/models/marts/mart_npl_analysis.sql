-- NPL analysis by segment — mirrors how banks report to regulators.
-- Provision coverage ratio = total ECL / total NPL outstanding.
WITH ecl AS (
    SELECT * FROM {{ ref('int_ecl_inputs') }}
)

SELECT
    dpd_bucket,
    ifrs9_stage,
    credit_size_bucket,
    education_level,

    COUNT(*)                                                        AS loan_count,
    SUM(is_npl)                                                     AS npl_count,
    ROUND(SUM(is_npl)::DOUBLE / COUNT(*) * 100, 2)                 AS npl_rate_pct,

    ROUND(SUM(ead), 0)                                             AS total_ead,
    ROUND(SUM(CASE WHEN is_npl = 1 THEN ead ELSE 0 END), 0)       AS npl_outstanding,
    ROUND(SUM(ecl_amount), 0)                                      AS total_ecl_provision,

    -- Provision coverage: ECL provision vs NPL outstanding
    ROUND(
        CASE
            WHEN SUM(CASE WHEN is_npl = 1 THEN ead ELSE 0 END) > 0
            THEN SUM(ecl_amount) /
                 SUM(CASE WHEN is_npl = 1 THEN ead ELSE 0 END) * 100
            ELSE 0
        END, 2
    )                                                               AS provision_coverage_pct,

    ROUND(AVG(empirical_pd) * 100, 2)                              AS avg_pd_pct,
    ROUND(AVG(utilisation_rate_pct), 2)                            AS avg_utilisation_pct

FROM ecl
GROUP BY
    dpd_bucket,
    ifrs9_stage,
    credit_size_bucket,
    education_level
ORDER BY
    CASE dpd_bucket
        WHEN 'Current'   THEN 1
        WHEN '1-30 DPD'  THEN 2
        WHEN '31-60 DPD' THEN 3
        WHEN '61-90 DPD' THEN 4
        ELSE 5
    END
