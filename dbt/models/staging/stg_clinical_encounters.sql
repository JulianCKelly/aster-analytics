-- Staging model for clinical encounters across borders
SELECT
    encounter_id,
    patient_id,
    encounter_date,
    facility,
    country,
    encounter_type,
    provider_name,
    chief_complaint,
    assessment,
    plan,
    source_format
FROM {{ source('raw', 'clinical_encounters') }}
