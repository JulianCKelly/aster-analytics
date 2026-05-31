-- Staging model for lab results with LOINC standardization
SELECT
    lab_id,
    patient_id,
    collection_date,
    facility,
    country,
    test_name,
    loinc_code,
    result_value,
    unit,
    reference_range,
    flag,
    source_format
FROM {{ source('raw', 'lab_results') }}
