import os
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/data/warehouse.duckdb")

st.title("🏛️ Regulatory Compliance")
st.markdown("Kenya banking sector macro ratios from World Bank data vs CBK regulatory thresholds.")


@st.cache_data(ttl=300)
def load_data():
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = con.execute("SELECT * FROM main_marts.mart_regulatory_ratios ORDER BY year").df()
    con.close()
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Dashboard not ready — run the Airflow DAG first. ({e})")
    st.stop()

latest = df.dropna(subset=["npl_ratio_pct"]).iloc[-1]
latest_cap = df.dropna(subset=["bank_capital_assets_ratio_pct"]).iloc[-1]
latest_gdp = df.dropna(subset=["gdp_growth_annual_pct"]).iloc[-1]

# --- Status badges ---
def badge(status):
    colours = {"OK": "🟢", "WATCH": "🟡", "BREACH": "🔴", "SLOW": "🟡", "RECESSION": "🔴"}
    return colours.get(status, "⚪")

k1, k2, k3, k4 = st.columns(4)
k1.metric("NPL Ratio (Latest)",
          f"{latest['npl_ratio_pct']:.1f}%",
          f"{badge(latest['npl_status'])} {latest['npl_status']} | Threshold: 15%")
k2.metric("Bank Capital Ratio",
          f"{latest_cap['bank_capital_assets_ratio_pct']:.1f}%",
          f"{badge(latest_cap['capital_status'])} {latest_cap['capital_status']} | Min: 8%")
k3.metric("GDP Growth",
          f"{latest_gdp['gdp_growth_annual_pct']:.1f}%",
          f"{badge(latest_gdp['gdp_status'])} {latest_gdp['gdp_status']}")
k4.metric("Data Year", f"{int(latest['year'])}")

st.divider()
col1, col2 = st.columns(2)

# NPL ratio trend with threshold line
with col1:
    npl_df = df.dropna(subset=["npl_ratio_pct"])
    fig = px.line(
        npl_df, x="year", y="npl_ratio_pct",
        title="Kenya Bank NPL Ratio — World Bank Data (%)",
        labels={"npl_ratio_pct": "NPL Ratio (%)", "year": "Year"},
        markers=True,
        color_discrete_sequence=["#e74c3c"],
    )
    fig.add_hline(y=15, line_dash="dash", line_color="darkred",
                  annotation_text="CBK Warning Threshold (15%)")
    fig.add_hline(y=10, line_dash="dot", line_color="orange",
                  annotation_text="Watch Level (10%)")
    st.plotly_chart(fig, use_container_width=True)

# Bank capital ratio trend
with col2:
    cap_df = df.dropna(subset=["bank_capital_assets_ratio_pct"])
    fig2 = px.line(
        cap_df, x="year", y="bank_capital_assets_ratio_pct",
        title="Kenya Bank Capital to Assets Ratio (%)",
        labels={"bank_capital_assets_ratio_pct": "Capital Ratio (%)", "year": "Year"},
        markers=True,
        color_discrete_sequence=["#2ecc71"],
    )
    fig2.add_hline(y=8, line_dash="dash", line_color="red",
                   annotation_text="Basel III Minimum (8%)")
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

# Credit to private sector
with col3:
    cred_df = df.dropna(subset=["credit_private_sector_gdp_pct"])
    fig3 = px.area(
        cred_df, x="year", y="credit_private_sector_gdp_pct",
        title="Domestic Credit to Private Sector (% of GDP)",
        labels={"credit_private_sector_gdp_pct": "% of GDP", "year": "Year"},
        color_discrete_sequence=["#3498db"],
    )
    st.plotly_chart(fig3, use_container_width=True)

# GDP growth vs Inflation
with col4:
    macro_df = df.dropna(subset=["gdp_growth_annual_pct", "inflation_cpi_annual_pct"])
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=macro_df["year"], y=macro_df["gdp_growth_annual_pct"],
        name="GDP Growth (%)", line=dict(color="#27ae60"), mode="lines+markers"
    ))
    fig4.add_trace(go.Scatter(
        x=macro_df["year"], y=macro_df["inflation_cpi_annual_pct"],
        name="Inflation CPI (%)", line=dict(color="#e67e22"), mode="lines+markers"
    ))
    fig4.update_layout(
        title="GDP Growth vs Inflation — Kenya",
        xaxis_title="Year",
        yaxis_title="%",
        legend_title="Indicator",
    )
    st.plotly_chart(fig4, use_container_width=True)

# Full compliance table
st.subheader("Full Regulatory Ratio History")
display_cols = ["year", "npl_ratio_pct", "bank_capital_assets_ratio_pct",
                "credit_private_sector_gdp_pct", "gdp_growth_annual_pct",
                "npl_status", "capital_status", "gdp_status"]
st.dataframe(
    df[display_cols].sort_values("year", ascending=False),
    use_container_width=True,
    hide_index=True,
)
