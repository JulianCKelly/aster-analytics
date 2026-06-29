"""
Loads transformed FHIR patient data into Snowflake staging tables.
Uses key-pair auth matching dbt profiles.yml.
"""
import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import snowflake.connector

SNOWFLAKE_CONFIG = {
    "account": "rorvdct-mib64142",
    "user": "JULIANKELLY",
    "private_key_path": os.path.expanduser("~/.ssh/snowflake_key.p8"),
    "database": "DBT_CORTEX_LLMS",
    "warehouse": "CORTEX_WH",
    "role": "DBT_ROLE",
    "schema": "STAGE",
}

def get_private_key():
    with open(SNOWFLAKE_CONFIG["private_key_path"], "rb") as f:
        pk = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    return pk.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())

def get_connection():
    return snowflake.connector.connect(
        account=SNOWFLAKE_CONFIG["account"],
        user=SNOWFLAKE_CONFIG["user"],
        private_key=get_private_key(),
        database=SNOWFLAKE_CONFIG["database"],
        warehouse=SNOWFLAKE_CONFIG["warehouse"],
        role=SNOWFLAKE_CONFIG["role"],
        schema=SNOWFLAKE_CONFIG["schema"],
    )

def upsert(cursor, table, pk_col, pk_val, cols, vals):
    set_clause = ", ".join(f"{c} = %s" for c in cols)
    col_list = ", ".join([pk_col] + cols)
    placeholders = ", ".join(["%s"] * (len(cols) + 1))
    cursor.execute(f"""
        MERGE INTO STAGE.{table} t
        USING (SELECT %s AS {pk_col}) s ON t.{pk_col} = s.{pk_col}
        WHEN MATCHED THEN UPDATE SET {set_clause}
        WHEN NOT MATCHED THEN INSERT ({col_list}) VALUES ({placeholders})
    """, [pk_val] + vals + [pk_val] + vals)

def load_all(results):
    conn = get_connection()
    cur = conn.cursor()
    patients, encounters, labs, gaps = [], [], [], []
    for r in results:
        patients.append(r["patient"])
        encounters.extend(r["encounters"])
        labs.extend(r["labs"])
        gaps.extend(r["care_gaps"])

    print(f"Loading {len(patients)} patients...")
    for p in patients:
        upsert(cur, "PATIENTS", "patient_id", p["patient_id"],
               ["full_name","country_of_origin","primary_language","insurance_status","immigration_year"],
               [p["full_name"],p["country_of_origin"],p["primary_language"],p["insurance_status"],p["immigration_year"]])

    print(f"Loading {len(encounters)} encounters...")
    for e in encounters:
        upsert(cur, "CLINICAL_ENCOUNTERS", "encounter_id", e["encounter_id"],
               ["patient_id","encounter_date","facility","country","encounter_type","provider_name","chief_complaint","assessment","plan","source_format"],
               [e["patient_id"],e["encounter_date"],e["facility"],e["country"],e["encounter_type"],e["provider_name"],e["chief_complaint"],e["assessment"],e["plan"],e["source_format"]])

    print(f"Loading {len(labs)} labs...")
    for l in labs:
        upsert(cur, "LAB_RESULTS", "lab_id", l["lab_id"],
               ["patient_id","collection_date","facility","country","test_name","loinc_code","result_value","unit","reference_range","flag","source_format"],
               [l["patient_id"],l["collection_date"],l["facility"],l["country"],l["test_name"],l["loinc_code"],l["result_value"],l["unit"],l["reference_range"],l["flag"],l["source_format"]])

    print(f"Loading {len(gaps)} care gaps...")
    for g in gaps:
        upsert(cur, "CARE_GAPS", "gap_id", g["gap_id"],
               ["patient_id","identified_date","gap_type","description","severity","origin_country","us_provider_aware","status"],
               [g["patient_id"],g["identified_date"],g["gap_type"],g["description"],g["severity"],g["origin_country"],g["us_provider_aware"],g["status"]])

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone: {len(patients)} patients, {len(encounters)} encounters, {len(labs)} labs, {len(gaps)} gaps loaded.")

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from pipeline.transform.fhir_to_staging import transform_all
    results = transform_all("synthea/output/fhir")
    load_all(results)
