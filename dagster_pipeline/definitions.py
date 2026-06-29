from dagster import Definitions, asset, AssetExecutionContext
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

@asset
def synthea_fhir_files(context: AssetExecutionContext):
    """Generate synthetic FHIR R4 patient bundles using Synthea."""
    result = subprocess.run([
        "java", "-jar", str(ROOT / "synthea/synthea.jar"),
        "-p", "5", "-s", "42", "Massachusetts",
        "--exporter.fhir.export=true",
        f"--exporter.baseDirectory={ROOT}/synthea/output",
        "--exporter.csv.export=false",
        "--exporter.ccda.export=false",
        "--exporter.text.export=false",
    ], capture_output=True, text=True, cwd=ROOT / "synthea")
    context.log.info(result.stdout[-500:])
    fhir_files = list((ROOT / "synthea/output/fhir").glob("*.json"))
    context.log.info(f"Generated {len(fhir_files)} FHIR files")
    return [str(f) for f in fhir_files]

@asset(deps=[synthea_fhir_files])
def snowflake_stage_load(context: AssetExecutionContext):
    """Transform FHIR bundles and load into Snowflake staging tables."""
    sys.path.insert(0, str(ROOT))
    from pipeline.transform.fhir_to_staging import transform_all
    from pipeline.load.snowflake_loader import load_all
    results = transform_all(str(ROOT / "synthea/output/fhir"))
    context.log.info(f"Transformed {len(results)} patients")
    load_all(results)
    context.log.info("Loaded to Snowflake")
    return len(results)

@asset(deps=[snowflake_stage_load])
def dbt_clinical_models(context: AssetExecutionContext):
    """Run dbt to materialize clinical fact and analysis models."""
    result = subprocess.run(
        ["dbt", "run"],
        capture_output=True, text=True,
        cwd=ROOT / "dbt"
    )
    context.log.info(result.stdout[-1000:])
    if result.returncode != 0:
        raise Exception(f"dbt run failed:\n{result.stderr}")
    return "dbt run complete"

from dagster import ScheduleDefinition, define_asset_job, sensor, RunRequest, SensorEvaluationContext
import os

pipeline_job = define_asset_job("pipeline_job", selection="*")

daily_schedule = ScheduleDefinition(
    job=pipeline_job,
    cron_schedule="0 6 * * *",
    name="daily_pipeline_schedule",
)

@sensor(job=pipeline_job, minimum_interval_seconds=30)
def new_fhir_files_sensor(context: SensorEvaluationContext):
    fhir_dir = Path("/Users/juliancharlankelly/aster-analytics/synthea/output/fhir")
    if not fhir_dir.exists():
        return
    patient_files = [
        f for f in fhir_dir.glob("*.json")
        if not f.name.startswith("hospital") and not f.name.startswith("practitioner")
    ]
    current_count = len(patient_files)
    last_count = int(context.cursor or 0)
    if current_count > last_count:
        context.update_cursor(str(current_count))
        yield RunRequest(run_key=str(current_count))

defs = Definitions(
    assets=[synthea_fhir_files, snowflake_stage_load, dbt_clinical_models],
    schedules=[daily_schedule],
    sensors=[new_fhir_files_sensor],
)
