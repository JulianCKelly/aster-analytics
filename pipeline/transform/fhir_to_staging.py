"""
Transforms Synthea FHIR R4 bundles into Aster Analytics staging schema.
Adds synthetic cross-border immigration context to make records relevant
to the Aster thesis: fragmented care across country borders.
"""

import json
import uuid
import random
import re
from pathlib import Path
from datetime import datetime, timedelta

# Cross-border immigration scenarios mapped to Synthea demographics
# We overlay these onto generated patients to create the immigration narrative
IMMIGRATION_SCENARIOS = [
    {"country_of_origin": "India", "primary_language": "Hindi", "immigration_year_offset": -4},
    {"country_of_origin": "Mexico", "primary_language": "Spanish", "immigration_year_offset": -6},
    {"country_of_origin": "Philippines", "primary_language": "Filipino", "immigration_year_offset": -3},
    {"country_of_origin": "China", "primary_language": "Mandarin", "immigration_year_offset": -7},
    {"country_of_origin": "Nigeria", "primary_language": "English", "immigration_year_offset": -2},
    {"country_of_origin": "El Salvador", "primary_language": "Spanish", "immigration_year_offset": -5},
    {"country_of_origin": "Vietnam", "primary_language": "Vietnamese", "immigration_year_offset": -8},
    {"country_of_origin": "Guatemala", "primary_language": "Spanish", "immigration_year_offset": -3},
    {"country_of_origin": "Ethiopia", "primary_language": "Amharic", "immigration_year_offset": -4},
    {"country_of_origin": "Bangladesh", "primary_language": "Bengali", "immigration_year_offset": -5},
]

INSURANCE_BY_COUNTRY = {
    "India": ["Medi-Cal", "Covered California", "Employer"],
    "Mexico": ["Uninsured", "Medi-Cal", "Covered California"],
    "Philippines": ["Employer", "Medicare", "Covered California"],
    "China": ["Medicare", "Medi-Cal", "Employer"],
    "Nigeria": ["Covered California", "Medi-Cal", "Uninsured"],
    "El Salvador": ["Uninsured", "Medi-Cal"],
    "Vietnam": ["Medi-Cal", "Medicare", "Covered California"],
    "Guatemala": ["Uninsured", "Medi-Cal"],
    "Ethiopia": ["Medi-Cal", "Covered California"],
    "Bangladesh": ["Medi-Cal", "Uninsured", "Covered California"],
}

def extract_patient(bundle: dict, scenario: dict, patient_idx: int) -> dict:
    patient_resources = [
        e["resource"] for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "Patient"
    ]
    if not patient_resources:
        return None

    p = patient_resources[0]
    name = p.get("name", [{}])[0]
    given = " ".join(re.sub(r'\d+$', '', w) for w in name.get("given", ["Unknown"]))
    family = re.sub(r'\d+$', '', name.get("family", "Unknown"))

    dob = p.get("birthDate", "1980-01-01")
    birth_year = int(dob[:4])
    current_year = 2024
    immigration_year = min(2024, max(birth_year + 18, current_year + scenario["immigration_year_offset"]))

    country = scenario["country_of_origin"]
    insurance_options = INSURANCE_BY_COUNTRY.get(country, ["Medi-Cal"])
    insurance = random.choice(insurance_options)

    return {
        "patient_id": f"SYN-{patient_idx:04d}",
        "full_name": f"{given} {family}",
        "date_of_birth": dob,
        "country_of_origin": country,
        "primary_language": scenario["primary_language"],
        "insurance_status": insurance,
        "immigration_year": immigration_year,
        "fhir_id": p.get("id", ""),
    }


def extract_encounters(bundle: dict, patient: dict) -> list:
    encounters = []
    current_year = 2024

    for entry in bundle.get("entry", []):
        r = entry["resource"]
        if r["resourceType"] != "Encounter":
            continue

        start = r.get("period", {}).get("start", "")
        if not start:
            continue

        encounter_year = int(start[:4])
        encounter_country = patient["country_of_origin"] if encounter_year < patient["immigration_year"] else "USA"

        facility = "Unknown Facility"
        if r.get("serviceProvider", {}).get("display"):
            facility = r["serviceProvider"]["display"]
        elif encounter_country != "USA":
            facility = f"General Hospital {patient['country_of_origin']}"

        encounter_type = "outpatient"
        if r.get("class", {}).get("code") == "IMP":
            encounter_type = "inpatient"
        elif r.get("class", {}).get("code") == "EMER":
            encounter_type = "emergency"

        reason = ""
        if r.get("reasonCode"):
            reason = r["reasonCode"][0].get("text", "") or \
                     r["reasonCode"][0].get("coding", [{}])[0].get("display", "")

        encounters.append({
            "encounter_id": f"ENC-{r.get('id', uuid.uuid4().hex)[:8].upper()}",
            "patient_id": patient["patient_id"],
            "encounter_date": start[:10],
            "facility": facility,
            "country": encounter_country,
            "encounter_type": encounter_type,
            "provider_name": "Provider on file",
            "chief_complaint": reason or "Routine visit",
            "assessment": reason or "See encounter notes",
            "plan": "Follow up as needed",
            "source_format": "FHIR R4",
        })

    return encounters[:10]  # cap at 10 per patient


def extract_labs(bundle: dict, patient: dict) -> list:
    labs = []
    current_year = 2024

    lab_loinc = {
        "2339-0": ("Glucose", "mg/dL"),
        "4548-4": ("HbA1c", "%"),
        "2160-0": ("Creatinine", "mg/dL"),
        "33914-3": ("eGFR", "mL/min"),
        "2085-9": ("HDL Cholesterol", "mg/dL"),
        "13457-7": ("LDL Cholesterol", "mg/dL"),
        "2093-3": ("Total Cholesterol", "mg/dL"),
        "718-7": ("Hemoglobin", "g/dL"),
        "1920-8": ("AST", "U/L"),
        "1742-6": ("ALT", "U/L"),
        "3016-3": ("TSH", "mIU/L"),
        "1975-2": ("Total Bilirubin", "mg/dL"),
    }

    for entry in bundle.get("entry", []):
        r = entry["resource"]
        if r["resourceType"] != "Observation":
            continue
        if r.get("status") not in ("final", "amended"):
            continue
        if not r.get("valueQuantity"):
            continue

        coding = r.get("code", {}).get("coding", [{}])
        loinc = next((c.get("code") for c in coding if c.get("system", "").endswith("loinc.org")), None)
        if loinc not in lab_loinc:
            continue

        test_name, unit = lab_loinc[loinc]
        value = r["valueQuantity"].get("value")
        if value is None:
            continue

        collected = r.get("effectiveDateTime", r.get("issued", ""))[:10]
        if not collected:
            continue

        collected_year = int(collected[:4])
        lab_country = patient["country_of_origin"] if collected_year < patient["immigration_year"] else "USA"

        flag = r.get("interpretation", [{}])[0].get("coding", [{}])[0].get("code", "N")
        if flag not in ("H", "L", "N"):
            flag = "N"

        labs.append({
            "lab_id": f"LAB-{r.get('id', uuid.uuid4().hex)[:8].upper()}",
            "patient_id": patient["patient_id"],
            "collection_date": collected,
            "facility": "Lab on file",
            "country": lab_country,
            "test_name": test_name,
            "loinc_code": loinc,
            "result_value": round(float(value), 2),
            "unit": unit,
            "reference_range": "",
            "flag": flag,
            "source_format": "FHIR R4",
        })

    return labs[:15]  # cap at 15 per patient


def extract_care_gaps(patient: dict, conditions: list, encounters: list) -> list:
    gaps = []
    gap_templates = [
        {
            "gap_type": "CONTINUITY",
            "severity": "CRITICAL",
            "description": f"Medical records from {patient['country_of_origin']} not transferred to US provider. Prior treatment history unknown at point of care.",
        },
        {
            "gap_type": "LANGUAGE",
            "severity": "MEDIUM",
            "description": f"Patient primary language is {patient['primary_language']}. No documented interpreter services or translated materials.",
        },
        {
            "gap_type": "MEDICATION",
            "severity": "HIGH",
            "description": f"Medications prescribed in {patient['country_of_origin']} not reconciled with current US formulary. Potential duplication or gap.",
        },
        {
            "gap_type": "SCREENING",
            "severity": "MEDIUM",
            "description": "Preventive screening history from country of origin unavailable. US provider cannot verify prior screenings.",
        },
        {
            "gap_type": "VACCINATION",
            "severity": "HIGH",
            "description": f"Vaccination records from {patient['country_of_origin']} not transferable to US immunization registry. I-693 civil surgeon cannot verify.",
        },
    ]

    num_gaps = random.randint(2, 4)
    selected = random.sample(gap_templates, num_gaps)

    for i, gap in enumerate(selected):
        gaps.append({
            "gap_id": f"GAP-{patient['patient_id']}-{i+1:02d}",
            "patient_id": patient["patient_id"],
            "identified_date": f"{2024 - random.randint(0, 1)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gap_type": gap["gap_type"],
            "description": gap["description"],
            "severity": gap["severity"],
            "origin_country": patient["country_of_origin"],
            "us_provider_aware": random.choice([True, False, False]),
            "status": "OPEN",
        })

    return gaps

def clean_term(t):
    return re.sub(r'\s*\([^)]+\)$', '', t).strip()


def generate_sample_note(bundle, patient):
    conditions = [
        clean_term(e["resource"].get("code", {}).get("text", ""))
        for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "Condition"
        and e["resource"].get("code", {}).get("text", "")
        and "finding" not in e["resource"].get("code", {}).get("text", "").lower()
        and "situation" not in e["resource"].get("code", {}).get("text", "").lower()
    ][:4]

    meds = [
        e["resource"].get("medicationCodeableConcept", {}).get("text", "")
        for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "MedicationRequest"
        and e["resource"].get("medicationCodeableConcept", {}).get("text", "")
        and e["resource"].get("status") == "active"
    ][:3]

    encounters = [
        e["resource"] for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "Encounter"
    ]
    last_enc = encounters[-1] if encounters else {}
    enc_date = last_enc.get("period", {}).get("start", "2024-01-01")[:10]
    enc_type = clean_term(last_enc.get("type", [{}])[0].get("text", "Establish care"))
    cond_str = ", ".join(conditions) if conditions else "multiple chronic conditions"
    med_str = ", ".join(meds) if meds else "medications on file"

    return (
        f"Patient: {patient['full_name']}, DOB on file, DOS {enc_date}\n\n"
        f"CC: {enc_type}\n\n"
        f"HPI: Patient immigrated from {patient['country_of_origin']} in {patient['immigration_year']}. "
        f"Primary language: {patient['primary_language']}. Insurance: {patient['insurance_status']}. "
        f"Presenting for follow-up and care establishment. Medical records from country of origin not available.\n\n"
        f"PMH: {cond_str}\n\n"
        f"Current Medications: {med_str}\n\n"
        f"Assessment:\n"
        f"1. {conditions[0] if conditions else 'See problem list'}\n"
        f"2. Cross-border care continuity gap - prior records unavailable\n"
        f"3. Medication reconciliation needed\n\n"
        f"Plan:\n"
        f"- Request records from {patient['country_of_origin']} provider\n"
        f"- Reconcile current medications with US formulary\n"
        f"- Schedule appropriate follow-up\n"
        f"- Arrange interpreter services if needed"
    )


def transform_bundle(fhir_path: Path, patient_idx: int) -> dict:
    with open(fhir_path) as f:
        bundle = json.load(f)

    scenario = IMMIGRATION_SCENARIOS[patient_idx % len(IMMIGRATION_SCENARIOS)]
    random.seed(patient_idx)

    patient = extract_patient(bundle, scenario, patient_idx)
    if not patient:
        return None

    conditions = [
        e["resource"] for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "Condition"
    ]

    encounters = extract_encounters(bundle, patient)
    labs = extract_labs(bundle, patient)
    care_gaps = extract_care_gaps(patient, conditions, encounters)

    return {
        "patient": patient,
        "encounters": encounters,
        "labs": labs,
        "care_gaps": care_gaps,
        "sample_note": generate_sample_note(bundle, patient),
    }


def transform_all(fhir_dir: str) -> list:
    fhir_path = Path(fhir_dir)
    patient_files = [
        f for f in fhir_path.glob("*.json")
        if not f.name.startswith("hospital") and not f.name.startswith("practitioner")
    ]

    results = []
    for idx, path in enumerate(sorted(patient_files)):
        print(f"Transforming {path.name}...")
        result = transform_bundle(path, idx)
        if result:
            results.append(result)

    return results


if __name__ == "__main__":
    results = transform_all("synthea/output/fhir")
    for r in results:
        p = r["patient"]
        print(f"\n{p['full_name']} ({p['country_of_origin']} → USA, {p['immigration_year']})")
        print(f"  Encounters: {len(r['encounters'])}, Labs: {len(r['labs'])}, Gaps: {len(r['care_gaps'])}")
