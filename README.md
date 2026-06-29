# Aster Analytics

Cross-border clinical intelligence pipeline — Snowflake Cortex + dbt + Streamlit + Dagster

Built as the data infrastructure layer for [Aster Health](https://github.com/JulianCKelly/aster-health), a platform that reconstructs fragmented medical histories for patients who have received care across multiple countries.

## The Problem

When someone immigrates, their medical history doesn't follow them. A patient who managed Type 2 diabetes in India for four years arrives at a US provider as an unknown. A cardiac patient from Mexico presents to an ED with chest pain — no prior records, no medication history. Providers make decisions blind. Patients face repeated diagnostics, medication gaps, and preventable complications.

This pipeline exists to change that.

## What This Does

Aster Analytics ingests fragmented clinical records from multiple countries, runs Snowflake Cortex LLM functions across each encounter, and surfaces structured care gap intelligence through a Streamlit dashboard. A Dagster orchestration layer automates the full pipeline end to end.

Pipeline:

- Synthea FHIR R4 bundles generated and transformed into staging records via a custom Python ingestion layer
- Raw clinical records loaded into Snowflake staging tables via MERGE upsert with RSA key-pair auth
- dbt staging models normalize and join across patient and encounter grain
- Cortex COMPLETE() runs risk analysis on each encounter and generates patient continuity profiles
- Mart models produce care gap severity rankings, cross-border encounter flags, and population-level trend signals
- Streamlit dashboard renders the full picture across five tabs
- Dagster orchestrates the full pipeline: FHIR generation, Snowflake load, and dbt run as a three-asset DAG

Dashboard tabs:

- **Care Gaps** — active gaps ranked by severity (CRITICAL/HIGH/MEDIUM/LOW), with Cortex-generated analysis per gap
- **Patient Profiles** — Cortex-synthesized continuity profile per patient across all available records
- **Encounters** — encounter-level risk signals with cross-border filter
- **Labs** — lab results with abnormal flags and Cortex clinical insight summaries
- **Trends** — population-level gap patterns by country of origin and gap type

## Stack

| Layer | Tool |
|---|---|
| Data warehouse | Snowflake |
| LLM functions | Snowflake Cortex (COMPLETE) |
| Transformation | dbt Core |
| FHIR ingestion | Python (Synthea + custom transformer) |
| Orchestration | Dagster (schedule + file sensor) |
| Dashboard | Streamlit |
| Auth | RSA key-pair |

## Orchestration

Dagster manages three assets in sequence:

    synthea_fhir_files -> snowflake_stage_load -> dbt_clinical_models

- **synthea_fhir_files** — generates synthetic FHIR R4 patient bundles using Synthea
- **snowflake_stage_load** — transforms bundles and upserts into Snowflake staging tables
- **dbt_clinical_models** — runs dbt to materialize all fact and analysis models

Automation:

- **daily_pipeline_schedule** — runs the full pipeline at 06:00 UTC
- **new_fhir_files_sensor** — triggers a run when new FHIR bundles appear in the output directory

## Data Model

    STAGE schema (Snowflake)
    ├── PATIENTS
    ├── CLINICAL_ENCOUNTERS
    ├── LAB_RESULTS
    └── CARE_GAPS

    dbt models
    ├── staging/
    │   ├── stg_patients.sql
    │   ├── stg_clinical_encounters.sql
    │   ├── stg_lab_results.sql
    │   └── stg_care_gaps.sql
    ├── fact/
    │   ├── fact_clinical_encounters.sql   -- encounter + patient join, is_cross_border flag
    │   ├── fact_lab_results.sql
    │   └── fact_care_gaps.sql
    └── analysis/
        ├── encounter_risk_analysis.sql    -- Cortex risk analysis per encounter
        ├── patient_profile_signals.sql    -- Cortex continuity profile per patient
        ├── clinical_insight_summaries.sql -- Cortex lab interpretation per patient
        └── care_continuity_trends.sql     -- population-level gap trends

## Synthetic Patients

Nine synthetic patients representing common cross-border care scenarios. Four are hand-crafted clinical narratives; five are Synthea-generated FHIR R4 bundles with cross-border immigration overlays applied during ingestion.

| Patient | Origin | US Insurer | Primary Gap |
|---|---|---|---|
| Priya Sharma | India | Medi-Cal | T2DM continuity, diabetic retinopathy unmonitored 4 years |
| Carlos Mendoza | Mexico | Uninsured | Cardiac history unknown at ED presentation (NSTEMI) |
| Amara Okafor | Nigeria | Covered California | Hypothyroidism management, language barrier risk |
| Wei Zhang | China | Medicare | Osteoporosis therapy duration unknown, MCI baseline absent |
| Corie Sofia Kohler | India | Covered California | Synthea-generated, immigration overlay applied |
| Ezekiel Leslie Walter | Mexico | Uninsured | Synthea-generated, immigration overlay applied |
| Jona Bonnie Schoen | Philippines | Employer | Synthea-generated, immigration overlay applied |
| Shalanda Kelsie Berge | China | Medicare | Synthea-generated, immigration overlay applied |
| Wilfredo Isaiah Fritsch | Nigeria | Covered California | Synthea-generated, immigration overlay applied |

## Setup

    # 1. Clone and configure
    git clone https://github.com/JulianCKelly/aster-analytics.git
    cd aster-analytics

    # 2. Create Snowflake environment
    # Run snowflake_sql/ scripts to create database, schemas, warehouse, role

    # 3. Configure dbt
    # Add Snowflake credentials to ~/.dbt/profiles.yml

    # 4. Run pipeline manually
    cd dbt && dbt deps && dbt run && dbt test

    # 5. Launch dashboard
    cd ../streamlit/src && streamlit run streamlit_app.py

    # 6. Or run via Dagster
    cd .. && dagster dev -f dagster_pipeline/definitions.py

## Related

[aster-health](https://github.com/JulianCKelly/aster-health) — the patient-facing interface layer this pipeline is designed to serve.

---

Demo only. Synthetic data. Not for use with real patient information.
