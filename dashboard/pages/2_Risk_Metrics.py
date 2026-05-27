import os
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/data/warehouse.duckdb")

st.title("⚠️ Risk Metrics")
st.markdown("NPL analysis, DPD breakdown, provision coverage, and IFRS 9 ECL by stage.")


@st.cache_data(ttl=300)
def load_npl():
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = con.execute("SELECT * FROM main_marts.mart_npl_analysis").df()
    con.close()
    return df


@st.cache_data(ttl=300)
def load_ecl():
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = con.execute("SELECT * FROM main_marts.mart_ecl_estimates").df()
    con.close()
    return df


try:
    npl_df = load_npl()
    ecl_df = load_ecl()
except Exception as e:
    st.error(f"Dashboard not ready — run the Airflow DAG first. ({e})")
    st.stop()

# --- KPI Row ---
total_loans    = int(npl_df["loan_count"].sum())
total_npl      = int(npl_df["npl_count"].sum())
total_ecl_amt  = ecl_df["total_ecl"].sum()
total_ead      = ecl_df["total_ead"].sum()
portfolio_npl  = round(total_npl / total_loans * 100, 2) if total_loans > 0 else 0
ecl_rate       = round(total_ecl_amt / total_ead * 100, 2) if total_ead > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Portfolio NPL Rate",  f"{portfolio_npl}%",
          delta=f"{'↑ Above' if portfolio_npl > 15 else '✓ Below'} 15% CBK threshold")
k2.metric("NPL Loans",           f"{total_npl:,}")
k3.metric("Total ECL Provision", f"{total_ecl_amt:,.0f}")
k4.metric("Portfolio ECL Rate",  f"{ecl_rate}%")

st.divider()
col1, col2 = st.columns(2)

# NPL rate by DPD bucket
with col1:
    dpd_order = ["Current", "1-30 DPD", "31-60 DPD", "61-90 DPD", "90+ DPD"]
    dpd_df = npl_df.groupby("dpd_bucket").agg(
        loan_count=("loan_count", "sum"),
        npl_count=("npl_count", "sum")
    ).reset_index()
    dpd_df["npl_rate"] = (dpd_df["npl_count"] / dpd_df["loan_count"] * 100).round(2)
    dpd_df["dpd_bucket"] = dpd_df["dpd_bucket"].astype(
        "category"
    ).cat.set_categories(dpd_order, ordered=True)
    dpd_df = dpd_df.sort_values("dpd_bucket")
    fig = px.bar(
        dpd_df, x="dpd_bucket", y="npl_rate",
        title="NPL Rate by DPD Bucket (%)",
        labels={"npl_rate": "NPL Rate (%)", "dpd_bucket": "DPD Bucket"},
        color="npl_rate",
        color_continuous_scale="RdYlGn_r",
    )
    fig.add_hline(y=15, line_dash="dash", line_color="red",
                  annotation_text="CBK Warning (15%)")
    st.plotly_chart(fig, use_container_width=True)

# IFRS 9 Stage breakdown
with col2:
    stage_df = ecl_df.groupby("ifrs9_stage").agg(
        total_ead=("total_ead", "sum"),
        total_ecl=("total_ecl", "sum"),
        loan_count=("loan_count", "sum"),
    ).reset_index()
    stage_df["ecl_rate"] = (stage_df["total_ecl"] / stage_df["total_ead"].replace(0, float("nan")) * 100).round(2).fillna(0)
    fig2 = px.bar(
        stage_df, x="ifrs9_stage", y="ecl_rate",
        title="IFRS 9 ECL Rate by Stage (%)",
        labels={"ecl_rate": "ECL Rate (%)", "ifrs9_stage": "IFRS 9 Stage"},
        color="ifrs9_stage",
        color_discrete_map={
            "Stage 1": "#2ecc71", "Stage 2": "#f39c12", "Stage 3": "#e74c3c"
        },
    )
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

# Provision coverage by DPD bucket
with col3:
    cov_df = npl_df.groupby("dpd_bucket")["provision_coverage_pct"].mean().reset_index()
    fig3 = px.bar(
        cov_df, x="dpd_bucket", y="provision_coverage_pct",
        title="Provision Coverage Ratio by Bucket (%)",
        labels={"provision_coverage_pct": "Coverage (%)", "dpd_bucket": "DPD Bucket"},
        color="provision_coverage_pct",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig3, use_container_width=True)

# EAD by IFRS 9 stage
with col4:
    fig4 = px.pie(
        stage_df, names="ifrs9_stage", values="total_ead",
        title="Exposure at Default (EAD) by IFRS 9 Stage",
        color="ifrs9_stage",
        color_discrete_map={
            "Stage 1": "#2ecc71", "Stage 2": "#f39c12", "Stage 3": "#e74c3c"
        },
        hole=0.4,
    )
    st.plotly_chart(fig4, use_container_width=True)
