WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_worldbank_banking') }}
),

cleaned AS (
    SELECT
        year::INTEGER                           AS year,
        country_code,
        ROUND(npl_ratio_pct::DOUBLE, 2)        AS npl_ratio_pct,
        ROUND(credit_private_sector_gdp_pct::DOUBLE, 2) AS credit_private_sector_gdp_pct,
        ROUND(bank_capital_assets_ratio_pct::DOUBLE, 2) AS bank_capital_assets_ratio_pct,
        ROUND(gdp_growth_annual_pct::DOUBLE, 2) AS gdp_growth_annual_pct,
        ROUND(inflation_cpi_annual_pct::DOUBLE, 2) AS inflation_cpi_annual_pct
    FROM source
    WHERE year IS NOT NULL
      AND year BETWEEN 2000 AND 2025
)

SELECT * FROM cleaned
ORDER BY year
