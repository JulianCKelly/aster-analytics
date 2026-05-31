SELECT
    e.encounter_id,
    e.patient_id,
    p.full_name,
    p.country_of_origin,
    p.primary_language,
    p.immigration_year,
    e.encounter_date,
    e.facility,
    e.country,
    e.encounter_type,
    e.provider_name,
    e.chief_complaint,
    e.assessment,
    e.plan,
    e.source_format,
    CASE WHEN e.country != p.country_of_origin THEN TRUE ELSE FALSE END AS is_cross_border
FROM {{ ref('stg_clinical_encounters') }} e
LEFT JOIN {{ ref('stg_patients') }} p ON e.patient_id =
