import streamlit as st

st.set_page_config(
    page_title="LoanRisk Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("pages/1_Portfolio_Overview.py",    title="Portfolio Overview",      icon="📊"),
    st.Page("pages/2_Risk_Metrics.py",          title="Risk Metrics",            icon="⚠️"),
    st.Page("pages/3_Vintage_Analysis.py",      title="Vintage Analysis",        icon="📈"),
    st.Page("pages/4_Regulatory_Compliance.py", title="Regulatory Compliance",   icon="🏛️"),
]

pg = st.navigation(pages)
pg.run()
