-- ucimlrepo id=222 returns the 16-feature bank marketing dataset (no macro indicators).
-- Columns: age, job, marital, education, has_credit_default, avg_yearly_balance,
--          has_housing_loan, has_personal_loan, contact, contact_day_of_week, month,
--          call_duration_sec, num_contacts_campaign, days_since_prev_contact,
--          num_previous_contacts, prev_campaign_outcome, subscribed_term_deposit
WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_bank_marketing') }}
),

cleaned AS (
    SELECT
        id,
        age,
        job,
        marital,
        education,
        CASE has_credit_default WHEN 'yes' THEN 1 WHEN 'no' THEN 0 ELSE NULL END AS has_credit_default,
        avg_yearly_balance,
        CASE has_housing_loan  WHEN 'yes' THEN 1 WHEN 'no' THEN 0 ELSE NULL END AS has_housing_loan,
        CASE has_personal_loan WHEN 'yes' THEN 1 WHEN 'no' THEN 0 ELSE NULL END AS has_personal_loan,
        contact                 AS contact_type,
        month,
        contact_day_of_week     AS day_of_week,
        call_duration_sec,
        num_contacts_campaign,
        days_since_prev_contact,
        num_previous_contacts,
        prev_campaign_outcome,
        subscribed_term_deposit
    FROM source
    WHERE age BETWEEN 18 AND 100
)

SELECT * FROM cleaned
