-- Fact table joining labs with patient context
SELECT
    l.lab_id,
    l.patient_id,
    p.full_name,
    p.country_of_origin,
    p.primary_language,
    l.collection_date,
    l.facility,
    l.country,
    l.test_name,
    l.loinc_code,
    l.result_value,
    l.unit,
    l.reference_range,
    l.flag,
    l.source_format,
    CASE WHEN l.flag = 'H' THEN 'Elevated'
         WHEN l.flag = 'L' THEN 'Low'
         ELSE 'Normal' END AS result_status,
    CASE WHEN l.country != p.country_of_origin THEN TRUE ELSE FALSE END AS is_cross_border
FROM {{ ref('stg_lab_results') }} l
LEFT JOIN {{ ref('stg_patients') }} p ON l.patient_id = p.patient_id
