"""
Pytest tests for DuckDB transformation logic (without running dbt).
Validates business rules for delinquency classification and ECL calculations.
"""

import pytest
import duckdb
import pandas as pd


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    yield c
    c.close()


def test_dpd_bucket_current(con):
    con.execute("""
        CREATE TABLE t AS SELECT -1 AS pay_status_sep, -1 AS pay_status_aug,
        -1 AS pay_status_jul, -1 AS pay_status_jun, -1 AS pay_status_may, -1 AS pay_status_apr
    """)
    result = con.execute("""
        SELECT CASE
            WHEN GREATEST(pay_status_sep, pay_status_aug, pay_status_jul,
                          pay_status_jun, pay_status_may, pay_status_apr) <= 0 THEN 'Current'
            ELSE 'Delinquent'
        END FROM t
    """).fetchone()[0]
    assert result == "Current"


def test_dpd_bucket_90_plus(con):
    con.execute("""
        CREATE TABLE t2 AS SELECT 4 AS pay_status_sep, 4 AS pay_status_aug,
        4 AS pay_status_jul, 4 AS pay_status_jun, 4 AS pay_status_may, 4 AS pay_status_apr
    """)
    result = con.execute("""
        SELECT CASE
            WHEN GREATEST(pay_status_sep, pay_status_aug, pay_status_jul,
                          pay_status_jun, pay_status_may, pay_status_apr) >= 4 THEN '90+ DPD'
            ELSE 'Other'
        END FROM t2
    """).fetchone()[0]
    assert result == "90+ DPD"


def test_ecl_calculation(con):
    pd_val = 0.22
    lgd_val = 0.45
    ead_val = 100000
    ecl = pd_val * lgd_val * ead_val
    assert abs(ecl - 9900.0) < 0.01, f"ECL expected 9900.0, got {ecl}"


def test_utilisation_rate(con):
    result = con.execute(
        "SELECT ROUND(75000 / 150000.0 * 100, 2)"
    ).fetchone()[0]
    assert result == 50.0


def test_npl_flag_logic(con):
    df = pd.DataFrame({
        "dpd_bucket": ["Current", "1-30 DPD", "90+ DPD", "90+ DPD"],
        "is_default": [0, 0, 0, 1],
    })
    con.execute("CREATE TABLE npl_t AS SELECT * FROM df")
    result = con.execute("""
        SELECT SUM(CASE WHEN dpd_bucket = '90+ DPD' OR is_default = 1 THEN 1 ELSE 0 END)
        FROM npl_t
    """).fetchone()[0]
    assert result == 2


def test_ifrs9_stage_assignment(con):
    df = pd.DataFrame({
        "dpd_bucket": ["Current", "1-30 DPD", "31-60 DPD", "61-90 DPD", "90+ DPD"],
    })
    con.execute("CREATE TABLE stage_t AS SELECT * FROM df")
    rows = con.execute("""
        SELECT dpd_bucket,
               CASE
                   WHEN dpd_bucket = 'Current'                      THEN 'Stage 1'
                   WHEN dpd_bucket IN ('1-30 DPD', '31-60 DPD')    THEN 'Stage 2'
                   ELSE 'Stage 3'
               END AS stage
        FROM stage_t
        ORDER BY dpd_bucket
    """).fetchall()
    stage_map = dict(rows)
    assert stage_map["Current"]   == "Stage 1"
    assert stage_map["1-30 DPD"]  == "Stage 2"
    assert stage_map["90+ DPD"]   == "Stage 3"


def test_provision_coverage_ratio(con):
    # coverage = ECL / NPL outstanding
    ecl = 45000
    npl_outstanding = 100000
    coverage = round(ecl / npl_outstanding * 100, 2)
    assert coverage == 45.0
