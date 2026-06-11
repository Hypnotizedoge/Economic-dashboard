"""
Stock Indices Page
Displays daily historical stock index data using Candlestick or Line charts.
Reads directly from the individual CSV files to get Open, High, Low, Close data.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import datetime
from theme import style, COLORS

# Map of display name -> CSV filename
INDEX_FILES = {
    "FTSE Malaysia KLCI": "FTSE Malaysia KLCI.csv",
    "Dow Jones Industrial Average": "Dow Jones Industrial Average Historical Data.csv",
    "S&P 500": "S&P 500.csv",
    "NASDAQ Composite": "NASDAQ Composite.csv",
    "FTSE 100": "FTSE 100 Historical Data.csv",
    "Euro Stoxx 50": "Euro Stoxx 50 Historical Data.csv",
    "Nikkei 225": "Nikkei 225.csv",
    "Hang Seng Index": "Hang Seng Index.csv",
    "KOSPI Composite": "KOSPI Historical Data.csv",
    "Shanghai Composite": "Shanghai Composite.csv",
    "TSX Composite": "TSX Composite.csv",
    "TSX Venture Composite": "TSX Venture Composite.csv",
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
    # Strip spaces and quotes from columns
    df.columns = df.columns.str.strip().str.replace('"', '')
    
    # Parse Dates - format is MM/DD/YYYY
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    df = df.dropna(subset=["Date"])
    
    # Clean numeric columns
    for col in ["Price", "Open", "High", "Low"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_price)
            
    if "Change %" in df.columns:
        df["ChangeVal"] = df["Change %"].apply(clean_change)
        
    df = df.sort_values("Date").reset_index(drop=True)
    return df

def render():
    st.markdown("## Global Stock Indices")
    st.caption("Daily historical stock index prices (OHLC) for major global markets.")

    # 1. Selection options
    col_sel, col_chart = st.columns([2, 1])
    
    with col_sel:
        selected_name = st.selectbox(
            "Select Stock Index",
            options=list(INDEX_FILES.keys()),
            index=0
        )
        
    with col_chart:
        chart_type = st.radio(
            "Chart Style",
            options=["Candlestick", "Line Chart"],
            horizontal=True
        )

    # 2. Load data
    filename = INDEX_FILES[selected_name]
    df = load_individual_index(filename)
    
    if df.empty:
        st.error(f"Data for {selected_name} could not be loaded or the file does not exist.")
        return
        
    # Get overall limits for date range selector
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    
    # Default to show last 6 months for readable candlestick charts
    default_start = max(min_date, max_date - datetime.timedelta(days=180))
    
    # Date Range Selector
    selected_range = st.date_input(
        "Date Range",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date,
        key="stock_date_range_picker"
    )
    
    if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date = default_start
        end_date = max_date
        
    # Filter Data
    df_filtered = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)].copy()
    
    if df_filtered.empty:
        st.warning("No data found for the selected date range.")
        return

    # 3. KPIs metrics block (using latest row in filtered data or overall dataset)
    latest_row = df.iloc[-1]
    latest_price = latest_row["Price"]
    latest_open = latest_row["Open"]
    latest_high = latest_row["High"]
    latest_low = latest_row["Low"]
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
            
    # Format Metric Delta
    if pd.notna(change_pct) and pd.notna(change_abs):
        delta_str = f"{change_abs:+.2f} ({change_pct:+.2f}%)"
    elif pd.notna(change_pct):
        delta_str = f"{change_pct:+.2f}%"
    else:
        delta_str = None
        
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Latest Close ({latest_date})", f"{latest_price:,.2f}", delta=delta_str)
    c2.metric("Open", f"{latest_open:,.2f}" if pd.notna(latest_open) else "N/A")
    c3.metric("High", f"{latest_high:,.2f}" if pd.notna(latest_high) else "N/A")
    c4.metric("Low", f"{latest_low:,.2f}" if pd.notna(latest_low) else "N/A")
    
    st.divider()

    # 4. Plot Chart
    fig = go.Figure()
    
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df_filtered["Date"],
            open=df_filtered["Open"],
            high=df_filtered["High"],
            low=df_filtered["Low"],
            close=df_filtered["Price"],
            name=selected_name,
            increasing_line_color=COLORS["pos"],
            decreasing_line_color=COLORS["neg"]
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df_filtered["Date"],
            y=df_filtered["Price"],
            mode="lines",
            line=dict(color=COLORS["primary"], width=2.5),
            name="Close Price",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Close: %{y:,.2f}<extra></extra>"
        ))
        
    fig = style(fig, 500)
    fig.update_layout(
        yaxis_title="Index Price Value",
        xaxis_rangeslider_visible=True if chart_type == "Candlestick" else False,
    )
    
    # Display Chart
    st.plotly_chart(fig, use_container_width=True)
