"""
Ingest Kenya banking sector macro indicators from World Bank Open Data API.
Indicators: NPL ratio, credit to private sector, bank capital ratio, GDP growth.
"""

import os
import duckdb
import pandas as pd
import wbgapi

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/opt/airflow/data/warehouse.duckdb")

INDICATORS = {
    "FB.AST.NPER.ZS": "npl_ratio_pct",
    "FD.AST.PRVT.GD.ZS": "credit_private_sector_gdp_pct",
    "FB.BNK.CAPA.ZS": "bank_capital_assets_ratio_pct",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_annual_pct",
    "FP.CPI.TOTL.ZG": "inflation_cpi_annual_pct",
}
COUNTRY = "KEN"
YEARS = range(2000, 2025)


def fetch_indicator(code: str, col_name: str) -> pd.DataFrame:
    # wbgapi.data.DataFrame returns shape (1, n_years): economy as row index, years as columns
    df = wbgapi.data.DataFrame(code, COUNTRY, mrv=25, numericTimeKeys=True)
    df = df.T                     # transpose: years become row index
    df.index.name = "year"
    df = df.reset_index()
    df.columns = ["year", col_name]
    df["country_code"] = COUNTRY
    return df


def run():
    frames = []
    for code, col in INDICATORS.items():
        try:
            df = fetch_indicator(code, col)
            frames.append(df)
            print(f"  Fetched {code}: {len(df)} rows")
        except Exception as e:
            print(f"  WARNING: Could not fetch {code}: {e}")

    if not frames:
        raise RuntimeError("No World Bank indicators fetched.")

    merged = frames[0]
    for df in frames[1:]:
        merged = merged.merge(df[["year", df.columns[1]]], on="year", how="outer")

    merged["year"] = merged["year"].astype(int)
    merged["country_code"] = COUNTRY
    merged = merged.sort_values("year").reset_index(drop=True)

    # Ensure all expected columns exist
    for col in INDICATORS.values():
        if col not in merged.columns:
            merged[col] = None

    with duckdb.connect(DUCKDB_PATH) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute("DROP TABLE IF EXISTS raw.raw_worldbank_banking")
        con.execute("""
            CREATE TABLE raw.raw_worldbank_banking AS SELECT * FROM merged
        """)
        row_count = con.execute("SELECT COUNT(*) FROM raw.raw_worldbank_banking").fetchone()[0]

    print(f"raw.raw_worldbank_banking loaded: {row_count} rows")


if __name__ == "__main__":
    run()
