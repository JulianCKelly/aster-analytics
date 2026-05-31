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
