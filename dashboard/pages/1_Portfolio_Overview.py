import os
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/data/warehouse.duckdb")

st.title("📊 Portfolio Overview")
st.markdown("Loan portfolio composition, exposure distribution, and segment breakdown.")


@st.cache_data(ttl=300)
def load_data():
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = con.execute("SELECT * FROM main_marts.mart_loan_portfolio_summary").df()
    con.close()
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Dashboard not ready — run the Airflow DAG first. ({e})")
    st.stop()

# --- KPI Row ---
total_loans    = int(df["loan_count"].sum())
total_exposure = df["total_credit_limit"].sum()
avg_util       = round(df["avg_utilisation_pct"].mean(), 1)
overall_npl    = round(df["npl_count"].sum() / total_loans * 100, 2) if total_loans > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Loans",      f"{total_loans:,}")
k2.metric("Total Exposure",   f"{total_exposure:,.0f}")
k3.metric("Avg Utilisation",  f"{avg_util}%")
k4.metric("Portfolio NPL Rate", f"{overall_npl}%")

st.divider()

col1, col2 = st.columns(2)

# DPD bucket distribution
with col1:
    dpd_df = df.groupby("dpd_bucket")["loan_count"].sum().reset_index()
    dpd_order = ["Current", "1-30 DPD", "31-60 DPD", "61-90 DPD", "90+ DPD"]
    dpd_df["dpd_bucket"] = pd.Categorical(dpd_df["dpd_bucket"], categories=dpd_order, ordered=True)
    dpd_df = dpd_df.sort_values("dpd_bucket")
    fig = px.bar(
        dpd_df, x="dpd_bucket", y="loan_count",
        color="dpd_bucket",
        color_discrete_map={
            "Current": "#2ecc71", "1-30 DPD": "#f39c12",
            "31-60 DPD": "#e67e22", "61-90 DPD": "#e74c3c", "90+ DPD": "#8e44ad"
        },
        title="Loans by DPD Bucket",
        labels={"loan_count": "Loan Count", "dpd_bucket": "DPD Bucket"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Education level distribution
with col2:
    edu_df = df.groupby("education_level")["loan_count"].sum().reset_index()
    fig2 = px.pie(
        edu_df, names="education_level", values="loan_count",
        title="Borrowers by Education Level",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4,
    )
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

# Credit size bucket — exposure
with col3:
    size_df = df.groupby("credit_size_bucket")["total_credit_limit"].sum().reset_index()
    size_order = ["Micro (<50K)", "Small (50K-150K)", "Medium (150K-300K)", "Large (>300K)"]
    size_df["credit_size_bucket"] = pd.Categorical(size_df["credit_size_bucket"], categories=size_order, ordered=True)
    size_df = size_df.sort_values("credit_size_bucket")
    fig3 = px.bar(
        size_df, x="credit_size_bucket", y="total_credit_limit",
        title="Total Exposure by Credit Size Bucket",
        labels={"total_credit_limit": "Total Exposure", "credit_size_bucket": "Segment"},
        color="credit_size_bucket",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig3.update_layout(showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

# Age band distribution
with col4:
    age_df = df.groupby("age_band")["loan_count"].sum().reset_index()
    age_order = ["18-29", "30-39", "40-49", "50-59", "60+"]
    age_df["age_band"] = pd.Categorical(age_df["age_band"], categories=age_order, ordered=True)
    age_df = age_df.sort_values("age_band")
    fig4 = px.bar(
        age_df, x="age_band", y="loan_count",
        title="Borrowers by Age Band",
        labels={"loan_count": "Loan Count", "age_band": "Age Band"},
        color="age_band",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig4.update_layout(showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)
