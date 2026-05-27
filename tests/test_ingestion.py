"""
Pytest tests for all three ingestion scripts.
Runs against a temporary DuckDB file to avoid touching the production warehouse.
"""

import os
import tempfile
import pytest
import duckdb


@pytest.fixture(scope="module")
def tmp_db(tmp_path_factory):
    db_path = str(tmp_path_factory.mktemp("db") / "test_warehouse.duckdb")
    os.environ["DUCKDB_PATH"] = db_path
    yield db_path
    os.environ.pop("DUCKDB_PATH", None)


def test_ingest_worldbank(tmp_db):
    from ingestion.ingest_worldbank import run
    run()
    con = duckdb.connect(tmp_db, read_only=True)
    count = con.execute("SELECT COUNT(*) FROM raw.raw_worldbank_banking").fetchone()[0]
    con.close()
    assert count > 10, f"Expected >10 World Bank rows, got {count}"


def test_worldbank_has_kenya(tmp_db):
    con = duckdb.connect(tmp_db)
    codes = con.execute(
        "SELECT DISTINCT country_code FROM raw.raw_worldbank_banking"
    ).fetchall()
    con.close()
    assert ("KEN",) in codes, "Expected country_code='KEN' in World Bank data"


def test_worldbank_npl_not_all_null(tmp_db):
    con = duckdb.connect(tmp_db)
    non_null = con.execute(
        "SELECT COUNT(*) FROM raw.raw_worldbank_banking WHERE npl_ratio_pct IS NOT NULL"
    ).fetchone()[0]
    con.close()
    assert non_null > 0, "npl_ratio_pct is entirely NULL — indicator may have changed"


def test_ingest_credit_default(tmp_db):
    from ingestion.ingest_credit_default import run
    run()
    con = duckdb.connect(tmp_db, read_only=True)
    count = con.execute("SELECT COUNT(*) FROM raw.raw_credit_default").fetchone()[0]
    con.close()
    assert count == 30000, f"Expected 30,000 credit default rows, got {count}"


def test_credit_default_schema(tmp_db):
    con = duckdb.connect(tmp_db)
    cols = {r[0] for r in con.execute(
        "DESCRIBE raw.raw_credit_default"
    ).fetchall()}
    con.close()
    required = {"id", "credit_limit", "age", "is_default"}
    missing = required - cols
    assert not missing, f"Missing columns: {missing}"


def test_credit_default_binary_target(tmp_db):
    con = duckdb.connect(tmp_db)
    invalid = con.execute(
        "SELECT COUNT(*) FROM raw.raw_credit_default WHERE is_default NOT IN (0, 1)"
    ).fetchone()[0]
    con.close()
    assert invalid == 0, f"{invalid} rows with invalid is_default values"


def test_ingest_bank_marketing(tmp_db):
    from ingestion.ingest_bank_marketing import run
    run()
    con = duckdb.connect(tmp_db, read_only=True)
    count = con.execute("SELECT COUNT(*) FROM raw.raw_bank_marketing").fetchone()[0]
    con.close()
    assert count >= 40000, f"Expected ~41,188 bank marketing rows, got {count}"


def test_bank_marketing_schema(tmp_db):
    con = duckdb.connect(tmp_db)
    cols = {r[0] for r in con.execute(
        "DESCRIBE raw.raw_bank_marketing"
    ).fetchall()}
    con.close()
    required = {"id", "age", "job", "subscribed_term_deposit"}
    missing = required - cols
    assert not missing, f"Missing columns: {missing}"


def test_bank_marketing_target_values(tmp_db):
    con = duckdb.connect(tmp_db)
    # ucimlrepo id=222 target 'y' is renamed to 'subscribed_term_deposit' — values are 'yes'/'no'
    invalid = con.execute(
        "SELECT COUNT(*) FROM raw.raw_bank_marketing WHERE subscribed_term_deposit NOT IN ('yes', 'no')"
    ).fetchone()[0]
    con.close()
    assert invalid == 0, f"{invalid} rows with invalid subscribed_term_deposit values"
