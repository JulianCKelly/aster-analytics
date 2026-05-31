-- Fact table joining care gaps with patient context
SELECT
    g.gap_id,
    g.patient_id,
    p.full_name,
    p.country_of_origin,
    p.primary_language,
    p.insurance_status,
    g.identified_date,
    g.gap_type,
    g.description,
    g.severity,
    g.origin_country,
    g.us_provider_aware,
    g.status,
    CASE WHEN g.severity = 'CRITICAL' THEN 1
         WHEN g.severity = 'HIGH' THEN 2
         WHEN g.severity = 'MEDIUM' THEN 3
         ELSE 4 END AS severity_rank
FROM {{ ref('stg_care_gaps') }} g
LEFT JOIN {{ ref('stg_patients') }} p ON g.patient_id = p.patient_id
