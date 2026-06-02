"""
theme.py — Plotly chart styling and custom CSS.
"""
import streamlit as st
import plotly.graph_objects as go

COLORS = {
    "primary": "#00D4AA", "secondary": "#6C63FF", "accent1": "#FF6B6B",
    "accent2": "#FFD93D", "accent3": "#4ECDC4", "accent4": "#FF8E53",
    "accent5": "#A78BFA", "accent6": "#F472B6", "text": "#FAFAFA",
    "muted": "#8B95A5", "grid": "#2A3040", "pos": "#00D4AA", "neg": "#FF6B6B",
}

COLOR_SEQ = [
    "#00D4AA", "#6C63FF", "#FF6B6B", "#FFD93D", "#4ECDC4",
    "#FF8E53", "#A78BFA", "#F472B6", "#45B7D1", "#96CEB4",
]

LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=COLORS["text"], size=13),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=COLORS["muted"]),
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
    ),
    xaxis=dict(gridcolor=COLORS["grid"], showgrid=True, gridwidth=1, zeroline=False),
    yaxis=dict(gridcolor=COLORS["grid"], showgrid=True, gridwidth=1, zeroline=False),
    margin=dict(l=40, r=20, t=60, b=40),
    hoverlabel=dict(bgcolor="#1A1F2E", font_size=12, font_color=COLORS["text"], bordercolor=COLORS["primary"]),
    colorway=COLOR_SEQ,
)


def style(fig: go.Figure, h: int = 420) -> go.Figure:
    fig.update_layout(**LAYOUT, height=h)
    
    # Apply time-series controls (range selector and slider) to Cartesian charts
    if hasattr(fig, "data") and len(fig.data) > 0:
        # Check if first trace is a Pie chart
        if not isinstance(fig.data[0], go.Pie):
            fig.update_xaxes(
                type="date", # Force date type to resolve undefined labels on rangeslider
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(count=5, label="5Y", step="year", stepmode="backward"),
                        dict(count=10, label="10Y", step="year", stepmode="backward"),
                        dict(step="all", label="ALL")
                    ]),
                    bgcolor="#1A1F2E",
                    activecolor="#00D4AA",
                    font=dict(color="#FAFAFA", size=11),
                    bordercolor="rgba(0,212,170,0.15)",
                    borderwidth=1
                ),
                rangeslider=dict(visible=True, thickness=0.08)
            )
    return fig


def inject_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
        border: 1px solid rgba(0, 212, 170, 0.15); border-radius: 12px;
        padding: 16px 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,212,170,0.15);
        border-color: rgba(0,212,170,0.3);
    }
    div[data-testid="stMetric"] label {
        color: #8B95A5 !important; font-weight: 500; font-size: 0.82rem;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.8rem; font-weight: 700; color: #FAFAFA;
    }
    h1 { background: linear-gradient(90deg, #00D4AA, #6C63FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 700; letter-spacing: -0.5px; }
    section[data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="collapsedControl"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 8px; padding: 8px 16px; color: #8B95A5; }
    .stTabs [aria-selected="true"] { background-color: rgba(0,212,170,0.15) !important; color: #00D4AA !important; }
    hr { border-color: rgba(0,212,170,0.15); }
    </style>""", unsafe_allow_html=True)
