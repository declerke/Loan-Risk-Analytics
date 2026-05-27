-- Regulatory ratio dashboard using real World Bank Kenya macro data.
-- Tracks key CBK-aligned metrics against minimum thresholds over time.
WITH wb AS (
    SELECT * FROM {{ ref('stg_worldbank_banking') }}
)

SELECT
    year,
    country_code,
    npl_ratio_pct,
    credit_private_sector_gdp_pct,
    bank_capital_assets_ratio_pct,
    gdp_growth_annual_pct,
    inflation_cpi_annual_pct,

    -- CBK regulatory thresholds (informational)
    15.0    AS npl_warning_threshold_pct,   -- CBK flags systemic risk above 15%
    8.0     AS min_capital_ratio_pct,        -- Basel III minimum Tier 1 + Tier 2
    10.5    AS cbk_min_core_capital_pct,     -- CBK minimum core capital ratio

    -- Compliance flags
    CASE WHEN npl_ratio_pct > 15.0 THEN 'BREACH' WHEN npl_ratio_pct > 10.0 THEN 'WATCH' ELSE 'OK' END
        AS npl_status,
    CASE WHEN bank_capital_assets_ratio_pct < 8.0 THEN 'BREACH' ELSE 'OK' END
        AS capital_status,
    CASE WHEN gdp_growth_annual_pct < 0 THEN 'RECESSION' WHEN gdp_growth_annual_pct < 3.0 THEN 'SLOW' ELSE 'OK' END
        AS gdp_status,

    -- YoY change in NPL ratio (risk deterioration signal)
    ROUND(
        npl_ratio_pct - LAG(npl_ratio_pct) OVER (ORDER BY year),
        2
    ) AS npl_yoy_change_pp

FROM wb
WHERE npl_ratio_pct IS NOT NULL
   OR bank_capital_assets_ratio_pct IS NOT NULL
ORDER BY year
