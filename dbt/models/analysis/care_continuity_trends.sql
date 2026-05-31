-- Care continuity trend analysis: cross-border gap patterns by country and type
SELECT
    g.origin_country,
    g.gap_type,
    COUNT(*) AS gap_count,
    ROUND(
        SUM(CASE WHEN g.us_provider_aware = FALSE THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) AS pct_provider_unaware,
    SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-7b',
        'You are a health equity analyst. Given this pattern of care gaps, summarize the systemic risk in 2 sentences. Country: ' || g.origin_country ||
        ', Gap type: ' || g.gap_type ||
        ', Total gaps: ' || COUNT(*) ||
        ', Provider unaware rate: ' || ROUND(SUM(CASE WHEN g.us_provider_aware = FALSE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '%'
    ) AS trend_insight
FROM {{ ref('fact_care_gaps') }} g
GROUP BY g.origin_country, g.gap_type
