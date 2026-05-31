-- Staging model for care gaps from cross-border fragmentation
SELECT
    gap_id,
    patient_id,
    identified_date,
    gap_type,
    description,
    severity,
    origin_country,
    us_provider_aware,
    status
FROM {{ source('raw', 'care_gaps') }}
