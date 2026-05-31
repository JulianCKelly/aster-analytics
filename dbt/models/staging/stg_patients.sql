-- Staging model for cross-border patient registry
SELECT
    patient_id,
    full_name,
    date_of_birth,
    country_of_origin,
    primary_language,
    immigration_year,
    current_mrn,
    origin_mrn,
    insurance_status
FROM {{ source('raw', 'patients') }}
