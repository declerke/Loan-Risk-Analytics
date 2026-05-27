# Loan Risk Analytics

Enterprise credit risk dashboard built on real datasets — NPL analysis, IFRS 9 ECL staging, vintage curves, and CBK regulatory compliance monitoring for the Kenya banking sector.

![Portfolio Overview](assets/01_portfolio_overview.png)

![DAG Success](assets/05_dag_success.png)

## Overview

Full end-to-end data engineering pipeline that ingests three real-world financial datasets, runs them through a dbt transformation layer, and surfaces the results across four Streamlit dashboard pages. Mirrors the analytical workflows used by credit risk teams in commercial banks: portfolio segmentation, delinquency bucketing, IFRS 9 expected credit loss modelling, vintage analysis, and regulatory ratio tracking against Central Bank of Kenya thresholds.

| Metric | Value |
|--------|-------|
| Loan records | 30,000 (UCI Credit Card Default) |
| Marketing records | 41,188 (UCI Bank Marketing) |
| Macro indicators | 5 Kenya World Bank time series (25 years) |
| Airflow tasks | 8 (3 ingest → 4 dbt layers → test) |
| dbt models | 11 (3 staging · 3 intermediate · 5 marts) |
| dbt tests | 54 |
| Pytest tests | 16 |
| Dashboard pages | 4 |
| Cost to run | $0 — 100% open data + local stack |

---

## Architecture

```
World Bank API  ─┐
UCI id=350      ─┼─► Airflow 3.0 DAG ─► DuckDB raw ─► dbt ─► DuckDB marts ─► Streamlit
UCI id=222      ─┘       (8 tasks)                   (11 models)              (4 pages)
```

**Airflow DAG — `loan_risk_dag`**

```
ingest_worldbank ─┐
ingest_credit     ─┼─► dbt_deps ─► dbt_staging ─► dbt_intermediate ─► dbt_marts ─► dbt_test
ingest_marketing  ─┘
```

All DuckDB tasks share a single `duckdb_pool` (1 slot) to serialise writes and avoid file-lock contention.

---

## Datasets

| Dataset | Source | Records | Description |
|---------|--------|---------|-------------|
| Credit Card Default | UCI ML Repo id=350 | 30,000 | Taiwan credit card clients — 6-month payment history, default outcome |
| Bank Marketing | UCI ML Repo id=222 | 41,188 | Portuguese bank telemarketing — demographics, loan products, campaign results |
| Kenya Banking Indicators | World Bank Open Data (wbgapi) | 25 years | NPL ratio, capital ratio, credit-to-GDP, GDP growth, CPI inflation |

---

## dbt Transformation Layer

### Staging
| Model | Description |
|-------|-------------|
| `stg_credit_default` | Renames X1–X23 UCI columns to semantic names; casts types |
| `stg_bank_marketing` | Normalises column names; resolves 16-feature vs 21-feature version |
| `stg_worldbank_banking` | Transposes wbgapi year-as-columns shape; fills missing years |

### Intermediate
| Model | Description |
|-------|-------------|
| `int_loan_delinquency_buckets` | Classifies each loan into DPD bucket (Current → 90+ DPD) using `GREATEST(COALESCE(...,-2))` |
| `int_portfolio_segments` | Adds age band, credit size bucket, utilisation rate, NPL flag |
| `int_ecl_inputs` | Computes IFRS 9 stage, empirical PD per bucket, ECL = PD × 0.45 × EAD |

### Marts
| Model | Feeds |
|-------|-------|
| `mart_loan_portfolio_summary` | Portfolio Overview |
| `mart_npl_analysis` | Risk Metrics — NPL & provision |
| `mart_ecl_estimates` | Risk Metrics — IFRS 9 ECL |
| `mart_vintage_curves` | Vintage Analysis |
| `mart_regulatory_ratios` | Regulatory Compliance |

---

## Dashboard

| Page | Key Visuals |
|------|------------|
| **Portfolio Overview** | DPD bucket bar chart, education pie, exposure by credit size, age band distribution |
| **Risk Metrics** | NPL rate by DPD bucket, IFRS 9 stage ECL bar, provision coverage, EAD donut |
| **Vintage Analysis** | Delinquency curves by cohort, cumulative default curves, delinquency heatmap |
| **Regulatory Compliance** | NPL trend vs CBK 15% threshold, capital ratio vs Basel III 8%, GDP vs inflation |

![Risk Metrics](assets/02_risk_metrics.png)

![Provision and Exposure](assets/08_provision_exposure.png)

![Vintage Analysis](assets/03_vintage_analysis.png)

![Eventual Default Curves](assets/06_eventual_default.png)

![Average Balance and Delinquency](assets/07_avg_balance_delinquency.png)

![Regulatory Compliance](assets/04_regulatory_compliance.png)

![Domestic Credit and GDP](assets/09_domestic_gdp.png)

![Total Exposure and Borrowers](assets/10_exposure_borrowers.png)

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| DuckDB over Postgres | Columnar OLAP for analytical queries; file-based so no separate DB service for the data warehouse; zero-config for local dev |
| Airflow `duckdb_pool` (1 slot) | DuckDB does not support concurrent writers from multiple processes; pool serialises all ingestion + dbt tasks without code-level locking |
| dbt `generate_schema_name` macro | dbt-duckdb prepends `main_` to custom schemas by default; macro strips it so `marts` resolves as `main_marts` matching Streamlit queries |
| UCI id=350 column remapping | ucimlrepo returns unlabelled X1–X23 columns; explicit positional map is required before any downstream SQL references semantic names |
| wbgapi transpose | `wbgapi.data.DataFrame` returns economies as rows and years as columns (shape 1×n); transpose before merge is non-negotiable |
| Streamlit `read_only=True` | All dashboard connections open DuckDB in read-only mode; prevents accidental writes from UI layer and allows concurrent reads |
| Context manager for DuckDB writes | All ingestion scripts use `with duckdb.connect(...) as con:` so the file lock is always released on exception — bare `con.close()` leaks locks on error paths |

---

## Skills Demonstrated

- **Apache Airflow 3.0** — AIP-72 Task SDK, dag-processor as separate service, pool-based concurrency control, cross-task lazy imports
- **DuckDB** — OLAP queries, schema management, named volume persistence, read-only vs write connections
- **dbt-duckdb** — 3-layer model architecture, custom schema macro, 54 data quality tests, source declarations
- **IFRS 9 credit risk modelling** — Stage classification, PD/LGD/EAD components, ECL calculation, provision coverage
- **Regulatory analytics** — CBK NPL thresholds, Basel III capital ratios, World Bank macro indicators
- **Streamlit** — Multi-page dashboard, `st.cache_data`, Plotly charts, zero-division guards for empty mart states
- **Docker Compose** — Multi-service stack, shared named volume, healthchecks, init service pattern
- **Python data engineering** — ucimlrepo, wbgapi, pandas DataFrame shaping, pytest fixtures with temp DuckDB

---

## Project Structure

```
loan-risk-analytics/
├── dags/
│   └── loan_risk_dag.py          # 8-task Airflow DAG
├── ingestion/
│   ├── ingest_credit_default.py  # UCI id=350 — 30,000 credit records
│   ├── ingest_bank_marketing.py  # UCI id=222 — 41,188 campaign records
│   └── ingest_worldbank.py       # World Bank Kenya — 5 indicators × 25 years
├── dbt/
│   ├── models/
│   │   ├── staging/              # 3 staging models + schema.yml
│   │   ├── intermediate/         # 3 intermediate models + schema.yml
│   │   └── marts/                # 5 mart models + schema.yml
│   ├── macros/
│   │   └── generate_schema_name.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── dashboard/
│   ├── Home.py
│   └── pages/
│       ├── 1_Portfolio_Overview.py
│       ├── 2_Risk_Metrics.py
│       ├── 3_Vintage_Analysis.py
│       └── 4_Regulatory_Compliance.py
├── tests/
│   ├── test_ingestion.py         # 9 ingestion tests
│   └── test_transformations.py   # 7 transformation unit tests
├── assets/                       # Dashboard screenshots
├── Dockerfile.airflow
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Running Locally

**Prerequisites:** Docker Desktop, Git

```bash
git clone https://github.com/declerke/Loan-Risk-Analytics.git
cd Loan-Risk-Analytics

cp .env.example .env
# Generate a JWT secret:
python -c "import secrets; print(secrets.token_hex(32))"
# Paste output into AIRFLOW__API_AUTH__JWT_SECRET= in .env

docker compose up -d
```

Once healthy (allow ~3 minutes for init):

```bash
# Trigger the pipeline
docker compose exec airflow-api-server airflow dags trigger loan_risk_dag

# Monitor at http://localhost:8080  (admin / admin)
# Dashboard at http://localhost:8501
```

---

## Running Tests

```bash
# Create local venv (requires uv)
uv venv && uv pip install -r requirements.txt

# Run all 16 tests
pytest tests/ -v
```

---

## License

MIT
