import os
import duckdb
import plotly.express as px
import streamlit as st

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/data/warehouse.duckdb")

st.title("📈 Vintage Analysis")
st.markdown("""
Tracks how default and delinquency rates evolve across the 6-month observation window (Apr–Sep 2005),
segmented by credit limit cohort. Mirrors how lenders monitor portfolio aging over time.
""")


@st.cache_data(ttl=300)
def load_data():
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = con.execute("SELECT * FROM main_marts.mart_vintage_curves ORDER BY cohort, month_num").df()
    con.close()
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Dashboard not ready — run the Airflow DAG first. ({e})")
    st.stop()

cohort_order = ["Micro (<50K)", "Small (50K-150K)", "Medium (150K-300K)", "Large (>300K)"]

# --- Delinquency rate curves ---
st.subheader("Delinquency Rate by Cohort Over Time")
fig = px.line(
    df, x="obs_month", y="delinquency_rate_pct", color="cohort",
    markers=True,
    category_orders={"cohort": cohort_order},
    title="60+ DPD Delinquency Rate (%) — Monthly Cohort Performance",
    labels={"delinquency_rate_pct": "Delinquency Rate (%)", "obs_month": "Month"},
    color_discrete_sequence=px.colors.qualitative.Set1,
)
fig.update_layout(legend_title="Credit Cohort", height=400)
st.plotly_chart(fig, use_container_width=True)

# --- Default rate curves ---
st.subheader("Eventual Default Rate by Cohort Over Time")
fig2 = px.line(
    df, x="obs_month", y="default_rate_pct", color="cohort",
    markers=True,
    category_orders={"cohort": cohort_order},
    title="Cumulative Default Rate (%) — Same cohort tracked month-by-month",
    labels={"default_rate_pct": "Default Rate (%)", "obs_month": "Month"},
    color_discrete_sequence=px.colors.qualitative.Bold,
)
fig2.update_layout(legend_title="Credit Cohort", height=400)
st.plotly_chart(fig2, use_container_width=True)

col1, col2 = st.columns(2)

# Average balance per cohort over time
with col1:
    fig3 = px.line(
        df, x="obs_month", y="avg_balance", color="cohort",
        markers=True,
        category_orders={"cohort": cohort_order},
        title="Average Outstanding Balance by Cohort",
        labels={"avg_balance": "Avg Balance", "obs_month": "Month"},
    )
    st.plotly_chart(fig3, use_container_width=True)

# Delinquent count heatmap
with col2:
    pivot = df.pivot(index="cohort", columns="obs_month", values="delinquency_rate_pct")
    month_cols = ["Apr 2005", "May 2005", "Jun 2005", "Jul 2005", "Aug 2005", "Sep 2005"]
    pivot = pivot.reindex(columns=[c for c in month_cols if c in pivot.columns])
    pivot = pivot.reindex([c for c in cohort_order if c in pivot.index])

    fig4 = px.imshow(
        pivot,
        title="Delinquency Rate Heatmap (% 60+ DPD)",
        color_continuous_scale="RdYlGn_r",
        aspect="auto",
        labels={"color": "Delinquency %"},
    )
    st.plotly_chart(fig4, use_container_width=True)
