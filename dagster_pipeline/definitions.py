from dagster import Definitions, asset, AssetExecutionContext
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
FHIR_DIR = ROOT / "synthea/output/fhir"


def patient_bundles(fhir_dir: Path) -> list[Path]:
    """Patient FHIR bundles only, excluding Synthea infrastructure files."""
    return sorted(
        f for f in fhir_dir.glob("*.json")
        if not f.name.startswith("hospital")
        and not f.name.startswith("practitioner")
    )


@asset
def synthea_fhir_files(context: AssetExecutionContext):
    """Generate synthetic FHIR R4 patient bundles using Synthea."""
    # Clean prior output so hospital/practitioner files don't accumulate
    if FHIR_DIR.exists():
        shutil.rmtree(FHIR_DIR)
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
    files = patient_bundles(FHIR_DIR)
    context.log.info(f"Generated {len(files)} patient FHIR bundles")
    return [str(f) for f in files]


@asset(deps=[synthea_fhir_files])
def snowflake_stage_load(context: AssetExecutionContext):
    """Transform FHIR bundles and load into Snowflake staging tables."""
    sys.path.insert(0, str(ROOT))
    from pipeline.transform.fhir_to_staging import transform_all
    from pipeline.load.snowflake_loader import load_all
    results = transform_all(str(FHIR_DIR))
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


from dagster import (
    ScheduleDefinition, define_asset_job, sensor,
    RunRequest, SkipReason, SensorEvaluationContext,
)

pipeline_job = define_asset_job("pipeline_job", selection="*")

daily_schedule = ScheduleDefinition(
    job=pipeline_job,
    cron_schedule="0 6 * * *",
    name="daily_pipeline_schedule",
)


@sensor(job=pipeline_job, minimum_interval_seconds=30)
def new_fhir_files_sensor(context: SensorEvaluationContext):
    if not FHIR_DIR.exists():
        yield SkipReason(f"FHIR output dir does not exist yet: {FHIR_DIR}")
        return

    files = patient_bundles(FHIR_DIR)
    if not files:
        yield SkipReason(f"No patient FHIR bundles found in {FHIR_DIR}")
        return

    latest_mtime = max(f.stat().st_mtime for f in files)
    signature = f"{len(files)}:{latest_mtime:.0f}"

    if signature != (context.cursor or ""):
        context.update_cursor(signature)
        yield RunRequest(run_key=signature)
    else:
        yield SkipReason(
            f"No change: {len(files)} bundles, latest mtime {latest_mtime:.0f}"
        )


defs = Definitions(
    assets=[synthea_fhir_files, snowflake_stage_load, dbt_clinical_models],
    schedules=[daily_schedule],
    sensors=[new_fhir_files_sensor],
)
