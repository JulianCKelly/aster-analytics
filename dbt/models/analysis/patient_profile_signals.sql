-- Cortex LLM: synthesize a clinical profile signal per patient
WITH encounter_agg AS (
    SELECT
        patient_id,
        COUNT(*) AS total_encounters,
        COUNT(CASE WHEN is_cross_border THEN 1 END) AS cross_border_encounters,
        MIN(encounter_date) AS first_encounter,
        MAX(encounter_date) AS last_encounter,
        LISTAGG(assessment, ' | ') AS all_assessments
    FROM {{ ref('fact_clinical_encounters') }}
    GROUP BY patient_id
),
gap_agg AS (
    SELECT
        patient_id,
        COUNT(*) AS total_gaps,
        COUNT(CASE WHEN severity IN ('CRITICAL','HIGH') THEN 1 END) AS high_severity_gaps,
        LISTAGG(gap_type, ', ') AS gap_types
    FROM {{ ref('fact_care_gaps') }}
    GROUP BY patient_id
)
SELECT
    p.patient_id,
    p.full_name,
    p.country_of_origin,
    p.primary_language,
    p.insurance_status,
    p.immigration_year,
    e.total_encounters,
    e.cross_border_encounters,
    e.first_encounter,
    e.last_encounter,
    g.total_gaps,
    g.high_severity_gaps,
    g.gap_types,
    SNOWFLAKE.CORTEX.COMPLETE('mixtral-8x7b',
        CONCAT(
            'You are a care coordinator building a patient profile for a cross-border immigrant patient. ',
            'Patient immigrated from ', p.country_of_origin, ' in ', p.immigration_year::VARCHAR, '. ',
            'Language: ', p.primary_language, '. Insurance: ', p.insurance_status, '. ',
            'They have ', e.total_encounters::VARCHAR, ' recorded encounters and ',
            g.total_gaps::VARCHAR, ' care gaps including ', g.high_severity_gaps::VARCHAR, ' high severity. ',
            'Gap types: ', COALESCE(g.gap_types, 'none'), '. ',
            'Clinical history: ', COALESCE(e.all_assessments, 'none'), '. ',
            'In 2-3 sentences, summarize this patient''s care continuity profile and top priority. ',
            'Be direct and clinical.'
        )
    ) AS patient_profile
FROM {{ ref('stg_patients') }} p
LEFT JOIN encounter_agg e ON p.patient_id = e.patient_id
LEFT JOIN gap_agg g ON p.patient_id = g.patient_id
