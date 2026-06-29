# Aster Analytics Dashboard

The Streamlit interface for [Aster Analytics](../README.md), the cross-border clinical intelligence pipeline. It reads directly from the Snowflake `ANALYTICS` schema and renders Cortex-generated care gap intelligence across five clinical views.

## Tabs

- **Care Gaps** - active care gaps ranked by severity (CRITICAL / HIGH / MEDIUM / LOW), each with a Cortex-generated clinical analysis explaining the gap and its risk.
- **Patient Profiles** - a Cortex-synthesized continuity profile per patient, reconstructed across all available records and countries of origin.
- **Encounters** - encounter-level risk signals with a cross-border filter to isolate patients carrying care history from outside the US.
- **Labs** - lab results with abnormal-value flags and Cortex clinical insight summaries interpreting results in context.
- **Trends** - population-level care gap patterns broken down by country of origin and gap type.

## Data Source

The dashboard queries materialized dbt models in Snowflake:

- `ANALYTICS.FACT_CARE_GAPS` - care gaps with Cortex `COMPLETE()` analysis
- `ANALYTICS.PATIENT_PROFILE_SIGNALS` - per-patient continuity profiles
- `ANALYTICS.FACT_CLINICAL_ENCOUNTERS` - encounters with `is_cross_border` flag
- `ANALYTICS.FACT_LAB_RESULTS` - labs with abnormal flags and insight summaries
- `ANALYTICS.CARE_CONTINUITY_TRENDS` - population-level gap trends

Run the upstream pipeline (`dbt run` from `../dbt`) before launching so these models are populated.

## Running Locally

    cd src
    streamlit run streamlit_app.py

Configure `.streamlit/secrets.toml` with your Snowflake RSA key-pair credentials before running.

## Auth

Connects to Snowflake via RSA key-pair authentication. The private key path and account details are read from `.streamlit/secrets.toml`, which is gitignored and never committed.

---

Demo only. Synthetic Synthea data. Not for use with real patient information.
