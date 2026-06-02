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

col_title, col_nav = st.columns([2, 1])

with col_title:
    st.markdown("# 🇲🇾 Malaysia Economy")
    st.markdown("<p style='color:#8B95A5;font-size:0.85rem;margin-top:-10px;'>DOSM Open Data Dashboard</p>", unsafe_allow_html=True)

with col_nav:
    page = st.selectbox(
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
