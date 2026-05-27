-- IFRS 9 Expected Credit Loss (ECL) inputs: Stage classification + PD/LGD/EAD.
-- Simplified approach (not IRB-model) suitable for portfolio analytics.
-- ECL = PD × LGD × EAD
WITH segments AS (
    SELECT * FROM {{ ref('int_portfolio_segments') }}
),

-- Empirical PD by DPD bucket (from actual default rates in dataset)
bucket_pd AS (
    SELECT
        dpd_bucket,
        ROUND(AVG(is_default::DOUBLE), 4) AS empirical_pd
    FROM segments
    GROUP BY dpd_bucket
),

ecl_staged AS (
    SELECT
        s.*,
        bp.empirical_pd,

        -- IFRS 9 Stage assignment
        CASE
            WHEN s.dpd_bucket = 'Current'  THEN 'Stage 1'
            WHEN s.dpd_bucket IN ('1-30 DPD', '31-60 DPD') THEN 'Stage 2'
            ELSE 'Stage 3'
        END AS ifrs9_stage,

        -- LGD: 45% for unsecured consumer credit (Basel III standard)
        0.45 AS lgd,

        -- EAD: outstanding balance (current bill amount)
        s.outstanding_balance AS ead,

        -- ECL calculation
        ROUND(bp.empirical_pd * 0.45 * s.outstanding_balance, 2) AS ecl_amount

    FROM segments s
    LEFT JOIN bucket_pd bp ON s.dpd_bucket = bp.dpd_bucket
)

SELECT * FROM ecl_staged
