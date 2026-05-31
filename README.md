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

---

## Data Model
