"""
Ingest UCI Bank Marketing dataset (id=222).
41,188 real bank customer records — demographics, loan products, campaign outcomes.
Source: https://archive.ics.uci.edu/dataset/222/bank+marketing
"""

import os
import duckdb
import pandas as pd
from ucimlrepo import fetch_ucirepo

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/opt/airflow/data/warehouse.duckdb")


def run():
    print("Fetching UCI Bank Marketing dataset (id=222)...")
    dataset = fetch_ucirepo(id=222)

    features = dataset.data.features
    targets = dataset.data.targets
    df = pd.concat([features, targets], axis=1)

    # Normalise column names — dots and spaces to underscores, lowercase
    df.columns = [c.replace(".", "_").replace(" ", "_").lower() for c in df.columns]

    # ucimlrepo id=222 returns the 16-feature version (no macro indicators like emp_var_rate)
    rename_map = {
        "default":      "has_credit_default",
        "housing":      "has_housing_loan",
        "loan":         "has_personal_loan",
        "y":            "subscribed_term_deposit",
        "duration":     "call_duration_sec",
        "campaign":     "num_contacts_campaign",
        "previous":     "num_previous_contacts",
        "pdays":        "days_since_prev_contact",
        "poutcome":     "prev_campaign_outcome",
        "day_of_week":  "contact_day_of_week",
        "balance":      "avg_yearly_balance",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Add surrogate ID
    df.insert(0, "id", range(1, len(df) + 1))

    with duckdb.connect(DUCKDB_PATH) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute("DROP TABLE IF EXISTS raw.raw_bank_marketing")
        con.execute("CREATE TABLE raw.raw_bank_marketing AS SELECT * FROM df")
        row_count = con.execute("SELECT COUNT(*) FROM raw.raw_bank_marketing").fetchone()[0]

    print(f"raw.raw_bank_marketing loaded: {row_count} rows")


if __name__ == "__main__":
    run()
