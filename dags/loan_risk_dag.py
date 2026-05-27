"""
LoanRisk Analytics Pipeline
Ingests World Bank Kenya macro data + UCI loan datasets → dbt transforms → DuckDB marts.
Schedule: @weekly
"""

import sys
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator

sys.path.insert(0, "/opt/airflow")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
    "depends_on_past": False,
}

DBT_DIR = "/opt/airflow/dbt"
POOL = "duckdb_pool"


def _ingest_worldbank():
    from ingestion.ingest_worldbank import run
    run()


def _ingest_credit_default():
    from ingestion.ingest_credit_default import run
    run()


def _ingest_bank_marketing():
    from ingestion.ingest_bank_marketing import run
    run()


with DAG(
    dag_id="loan_risk_pipeline",
    default_args=default_args,
    description="Banking risk analytics pipeline — World Bank + UCI loan data → dbt → DuckDB",
    schedule="@weekly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["finance", "banking", "risk", "dbt", "duckdb"],
) as dag:

    ingest_worldbank = PythonOperator(
        task_id="ingest_worldbank",
        python_callable=_ingest_worldbank,
        pool=POOL,
    )

    ingest_credit_default = PythonOperator(
        task_id="ingest_credit_default",
        python_callable=_ingest_credit_default,
        pool=POOL,
    )

    ingest_bank_marketing = PythonOperator(
        task_id="ingest_bank_marketing",
        python_callable=_ingest_bank_marketing,
        pool=POOL,
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_DIR} && dbt deps --profiles-dir {DBT_DIR}",
        pool=POOL,
    )

    dbt_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"cd {DBT_DIR} && dbt run --select staging --profiles-dir {DBT_DIR}",
        pool=POOL,
    )

    dbt_intermediate = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command=f"cd {DBT_DIR} && dbt run --select intermediate --profiles-dir {DBT_DIR}",
        pool=POOL,
    )

    dbt_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"cd {DBT_DIR} && dbt run --select marts --profiles-dir {DBT_DIR}",
        pool=POOL,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test --profiles-dir {DBT_DIR}",
        pool=POOL,
    )

    # Ingestion tasks run sequentially via duckdb_pool (1 slot — no concurrent writers)
    ingest_worldbank >> ingest_credit_default >> ingest_bank_marketing
    ingest_bank_marketing >> dbt_deps >> dbt_staging >> dbt_intermediate >> dbt_marts >> dbt_test
