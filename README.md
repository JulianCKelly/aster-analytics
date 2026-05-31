# Aster Analytics

**Cross-border clinical intelligence pipeline — Snowflake Cortex + dbt + Streamlit**

Built as the data infrastructure layer for [Aster Health](https://github.com/JulianCKelly/aster-health), a platform that reconstructs fragmented medical histories for patients who have received care across multiple countries.

---

## The Problem

When someone immigrates, their medical history doesn't follow them. A patient who managed Type 2 diabetes in India for four years arrives at a US provider as an unknown. A cardiac patient from Mexico presents to an ED with chest pain — no prior records, no medication history. Providers make decisions blind. Patients face repeated diagnostics, medication gaps, and preventable complications.

This pipeline exists to change that.

---

## What This Does

Aster Analytics ingests fragmented clinical records from multiple countries, runs Snowflake Cortex LLM functions across each encounter, and surfaces structured care gap intelligence through a Streamlit dashboard.

**Pipeline:**
- Raw clinical records (encounters, labs, care gaps) loaded into Snowflake
- dbt staging models normalize and join across patient and encounter grain
- Cortex `COMPLETE()` runs risk analysis on each encounter and generates patient continuity profiles
- Mart models produce care gap severity rankings, cross-border encounter flags, and population-level trend signals
- Streamlit dashboard renders the full picture across five tabs

**Dashboard tabs:**
- **Care Gaps** — active gaps ranked by severity, filtered by CRITICAL/HIGH/MEDIUM/LOW, with Cortex-generated analysis per gap
- **Patient Profiles** — Cortex-synthesized continuity profile per patient across all available records
- **Encounters** — encounter-level risk signals with cross-border filter
- **Labs** — lab results with abnormal flags and Cortex clinical insight summaries
- **Trends** — population-level gap patterns by country of origin and gap type

---

## Stack

| Layer | Tool |
|---|---|
| Data warehouse | Snowflake |
| LLM functions | Snowflake Cortex (`COMPLETE`) |
| Transformation | dbt Core |
| Dashboard | Streamlit |
| Auth | RSA key-pair |

---

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

---

## Synthetic Patients

The pipeline runs on four synthetic patients representing common cross-border care scenarios:

| Patient | Origin | US Insurer | Primary Gap |
|---|---|---|---|
| Priya Sharma | India | Medi-Cal | T2DM continuity, diabetic retinopathy unmonitored 4 years |
| Carlos Mendoza | Mexico | Uninsured | Cardiac history unknown at ED presentation (NSTEMI) |
| Amara Okafor | Nigeria | Covered California | Hypothyroidism management, language barrier risk |
| Wei Zhang | China | Medicare | Osteoporosis therapy duration unknown, MCI baseline absent |

---

## Setup

```bash
# 1. Clone and configure
git clone https://github.com/JulianCKelly/aster-analytics.git
cd aster-analytics

# 2. Create Snowflake environment
# Run snowflake_sql/ scripts to create database, schemas, warehouse, role

# 3. Load clinical seed data
# Run INSERT statements in snowflake_sql/ for PATIENTS, CLINICAL_ENCOUNTERS, LAB_RESULTS, CARE_GAPS

# 4. Configure dbt
# Add Snowflake credentials to ~/.dbt/profiles.yml

# 5. Run pipeline
cd dbt
dbt deps
dbt run
dbt test

# 6. Launch dashboard
cd ../streamlit/src
streamlit run streamlit_app.py
```

---

## Related

[aster-health](https://github.com/JulianCKelly/aster-health) — the patient-facing interface layer this pipeline is designed to serve.

---

*Demo only. Synthetic data. Not for use with real patient information.*
