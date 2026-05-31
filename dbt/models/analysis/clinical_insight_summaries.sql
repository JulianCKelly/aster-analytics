-- Cortex LLM: generate actionable insight summary per patient across all data
SELECT
    l.patient_id,
    p.full_name,
    COUNT(*) AS total_labs,
    SUM(CASE WHEN l.flag = 'H' THEN 1 ELSE 0 END) AS abnormal_high,
    SUM(CASE WHEN l.flag = 'L' THEN 1 ELSE 0 END) AS abnormal_low,
    SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-7b',
        'You are a clinical analyst. Summarize the key lab findings for this patient in 2-3 sentences, highlighting any abnormal results and clinical implications. Labs: ' ||
        LISTAGG(l.test_name || ': ' || l.result_value || ' ' || COALESCE(l.unit, '') || ' (' || COALESCE(l.flag, 'N') || ')', ', ')
    ) AS clinical_insight
FROM {{ ref('stg_lab_results') }} l
LEFT JOIN {{ ref('stg_patients') }} p ON l.patient_id = p.patient_id
GROUP BY l.patient_id, p.full_name