"""
Ingest UCI Default of Credit Card Clients dataset (id=350).
30,000 real credit card client records — payment history, delinquency, default outcomes.
Source: https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
"""

import os
import duckdb
import pandas as pd
from ucimlrepo import fetch_ucirepo

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/opt/airflow/data/warehouse.duckdb")


def run():
    print("Fetching UCI Credit Card Default dataset (id=350)...")
    dataset = fetch_ucirepo(id=350)

    features = dataset.data.features
    targets = dataset.data.targets
    df = pd.concat([features, targets], axis=1)

    # ucimlrepo returns X1-X23 for features and Y for target — apply explicit positional rename
    col_map = {
        "X1": "credit_limit",
        "X2": "gender",
        "X3": "education_level",
        "X4": "marital_status",
        "X5": "age",
        "X6": "pay_status_sep",
        "X7": "pay_status_aug",
        "X8": "pay_status_jul",
        "X9": "pay_status_jun",
        "X10": "pay_status_may",
        "X11": "pay_status_apr",
        "X12": "bill_amt_sep",
        "X13": "bill_amt_aug",
        "X14": "bill_amt_jul",
        "X15": "bill_amt_jun",
        "X16": "bill_amt_may",
        "X17": "bill_amt_apr",
        "X18": "pay_amt_sep",
        "X19": "pay_amt_aug",
        "X20": "pay_amt_jul",
        "X21": "pay_amt_jun",
        "X22": "pay_amt_may",
        "X23": "pay_amt_apr",
        "Y": "is_default",
    }
    df = df.rename(columns=col_map)

    df.insert(0, "id", range(1, len(df) + 1))

    with duckdb.connect(DUCKDB_PATH) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute("DROP TABLE IF EXISTS raw.raw_credit_default")
        con.execute("CREATE TABLE raw.raw_credit_default AS SELECT * FROM df")
        row_count = con.execute("SELECT COUNT(*) FROM raw.raw_credit_default").fetchone()[0]

    print(f"raw.raw_credit_default loaded: {row_count} rows")


if __name__ == "__main__":
    run()
