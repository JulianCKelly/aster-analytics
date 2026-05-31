SELECT
    f.encounter_id,
    f.patient_id,
    f.full_name,
    f.country_of_origin,
    f.primary_language,
    f.encounter_date,
    f.facility,
    f.country,
    f.encounter_type,
    f.provider_name,
    f.chief_complaint,
    f.assessment,
    f.plan,
    f.source_format,
    f.is_cross_border,
    SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-7b',
        'You are a clinical risk analyst. Given this encounter assessment, identify any cross-border care continuity risks in 2-3 sentences. Assessment: ' || f.assessment
    ) AS risk_analysis
FROM {{ ref('fact_clinical_encounters') }} f
