WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_credit_default') }}
),

cleaned AS (
    SELECT
        id,
        credit_limit,
        gender,
        CASE education_level
            WHEN 1 THEN 'Graduate School'
            WHEN 2 THEN 'University'
            WHEN 3 THEN 'High School'
            ELSE 'Other'
        END                     AS education_level,
        CASE marital_status
            WHEN 1 THEN 'Married'
            WHEN 2 THEN 'Single'
            ELSE 'Other'
        END                     AS marital_status,
        age,
        -- Payment statuses: -2=no consumption, -1=paid duly, 0=revolving credit, 1-9=months delayed
        pay_status_sep,
        pay_status_aug,
        pay_status_jul,
        pay_status_jun,
        pay_status_may,
        pay_status_apr,
        -- Bill amounts (outstanding balance per month)
        bill_amt_sep,
        bill_amt_aug,
        bill_amt_jul,
        bill_amt_jun,
        bill_amt_may,
        bill_amt_apr,
        -- Payment amounts made
        pay_amt_sep,
        pay_amt_aug,
        pay_amt_jul,
        pay_amt_jun,
        pay_amt_may,
        pay_amt_apr,
        is_default::INTEGER     AS is_default
    FROM source
    WHERE credit_limit > 0
      AND age BETWEEN 18 AND 100
)

SELECT * FROM cleaned
