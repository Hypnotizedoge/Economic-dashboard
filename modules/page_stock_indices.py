"""
Stock Indices Page
Displays daily historical stock index data for all 12 global markets, grouped by continent.
Plots all available data with individual timeframes/rangesliders for each chart.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import datetime
from theme import style, COLORS

CONTINENT_GROUPS = {
    "North America": {
        "S&P 500": "S&P 500.csv",
        "Dow Jones": "Dow Jones Industrial Average Historical Data.csv",
        "NASDAQ Composite": "NASDAQ Composite.csv",
        "TSX Composite": "TSX Composite.csv",
        "TSX Venture": "TSX Venture Composite.csv",
    },
    "Europe": {
        "FTSE 100": "FTSE 100 Historical Data.csv",
        "Euro Stoxx 50": "Euro Stoxx 50 Historical Data.csv",
    },
    "Asia-Pacific": {
        "FTSE Malaysia KLCI": "FTSE Malaysia KLCI.csv",
        "Nikkei 225": "Nikkei 225.csv",
        "Hang Seng Index": "Hang Seng Index.csv",
        "KOSPI Composite": "KOSPI Historical Data.csv",
        "Shanghai Composite": "Shanghai Composite.csv",
    }
}

def clean_price(val):
    if pd.isna(val) or str(val).strip() in ("", "-"):
        return float("nan")
    return float(str(val).replace(",", "").replace('"', '').strip())

def clean_change(val):
    if pd.isna(val) or str(val).strip() in ("", "-"):
        return float("nan")
    return float(str(val).replace("%", "").replace(",", "").replace('"', '').strip())

@st.cache_data(show_spinner=False)
def load_individual_index(filename: str) -> pd.DataFrame:
    """Load and clean individual stock index CSV file."""
    csv_path = Path(__file__).parent.parent / "Stock indices" / filename
    if not csv_path.exists():
        return pd.DataFrame()
        
    df = pd.read_csv(csv_path, dtype=str)
    df.columns = df.columns.str.strip().str.replace('"', '')
    
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    df = df.dropna(subset=["Date"])
    
    for col in ["Price", "Open", "High", "Low"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_price)
            
    if "Change %" in df.columns:
        df["ChangeVal"] = df["Change %"].apply(clean_change)
        
    df = df.sort_values("Date").reset_index(drop=True)
    return df

def render_chart(index_name: str, filename: str, chart_type: str):
    df = load_individual_index(filename)
    if df.empty:
        st.warning(f"Data for {index_name} could not be loaded.")
        return
        
    latest_row = df.iloc[-1]
    latest_price = latest_row["Price"]
    latest_date = latest_row["Date"].strftime("%d %b %Y")
    
    # Compute Change
    change_pct = latest_row.get("ChangeVal", float("nan"))
    if pd.isna(change_pct) and len(df) > 1:
        prev_price = df.iloc[-2]["Price"]
        if pd.notna(prev_price) and prev_price != 0:
            change_pct = ((latest_price - prev_price) / prev_price) * 100
            
    change_abs = float("nan")
    if len(df) > 1:
        prev_price = df.iloc[-2]["Price"]
        if pd.notna(prev_price):
            change_abs = latest_price - prev_price
            
    if pd.notna(change_pct) and pd.notna(change_abs):
        delta_str = f"{change_abs:+.2f} ({change_pct:+.2f}%)"
    elif pd.notna(change_pct):
        delta_str = f"{change_pct:+.2f}%"
    else:
        delta_str = None

    # Render card title and metric
    st.metric(
        label=f"{index_name} (Close: {latest_date})",
        value=f"{latest_price:,.2f}",
        delta=delta_str
    )

    fig = go.Figure()
    
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Price"],
            name=index_name,
            increasing_line_color=COLORS["pos"],
            decreasing_line_color=COLORS["neg"]
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["Price"],
            mode="lines",
            line=dict(color=COLORS["primary"], width=2),
            name="Close Price",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Close: %{y:,.2f}<extra></extra>"
        ))
        
    fig = style(fig, 360)
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=85),
        xaxis_rangeslider_visible=True if chart_type == "Candlestick" else False,
    )
    st.plotly_chart(fig, use_container_width=True)

def render():
    st.markdown("## Global Stock Indices")
    st.caption("Historical price indices grouped by continent. Each chart displays all historical data with individual zoom and timeframe controls.")
    
    chart_type = st.radio(
        "Chart Style",
        options=["Candlestick", "Line Chart"],
        horizontal=True,
        key="global_stock_chart_style"
    )
    
    st.divider()
    
    for continent, indices in CONTINENT_GROUPS.items():
        st.markdown(f"### {continent}")
        
        # Grid layout (2 columns)
        indices_list = list(indices.items())
        for i in range(0, len(indices_list), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                name1, file1 = indices_list[i]
                render_chart(name1, file1, chart_type)
                st.markdown("<br>", unsafe_allow_html=True)
                
            with col2:
                if i + 1 < len(indices_list):
                    name2, file2 = indices_list[i+1]
                    render_chart(name2, file2, chart_type)
                    st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
