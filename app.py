"""
Malaysia Economic Dashboard — Main App
Reads from local parquet files in /data folder.
"""
import streamlit as st
from theme import inject_css

st.set_page_config(
    page_title="Malaysia Economic Dashboard",
    page_icon="🇲🇾",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

with st.sidebar:
    st.markdown("## 🇲🇾 Malaysia Economy")
    st.markdown("<p style='color:#8B95A5;font-size:0.85rem;margin-top:-10px;'>DOSM Open Data Dashboard</p>", unsafe_allow_html=True)
    st.divider()
    page = st.radio(
        "Navigate",
        options=[
            "📊 Economic Growth",
            "👷 Employment",
            "💰 Prices",
            "🚢 Trade",
            "🏭 Industrial & Retail",
            "🏦 Financial",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("<p style='color:#8B95A5;font-size:0.75rem;'>Data: <a href='https://open.dosm.gov.my' style='color:#00D4AA;'>open.dosm.gov.my</a></p>", unsafe_allow_html=True)

if page == "📊 Economic Growth":
    from pages import page_economic
    page_economic.render()
elif page == "👷 Employment":
    from pages import page_employment
    page_employment.render()
elif page == "💰 Prices":
    from pages import page_prices
    page_prices.render()
elif page == "🚢 Trade":
    from pages import page_trade
    page_trade.render()
elif page == "🏭 Industrial & Retail":
    from pages import page_industrial
    page_industrial.render()
elif page == "🏦 Financial":
    from pages import page_financial
    page_financial.render()
