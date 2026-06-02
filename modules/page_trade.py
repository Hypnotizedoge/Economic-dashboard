"""Trade — Exports, imports, trade balance, SITC"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_loader import load, fseries, latest, fmt, SITC_SECTIONS
from theme import style, COLORS


def render():
    st.markdown("## 🚢 Trade")
    st.caption("Monthly trade in goods")

    tr = load("trade_headline")
    sitc = load("trade_sitc")
    enduse = load("trade_enduse")

    tabs = fseries(tr, "abs").sort_values("date")

    # KPIs
    ev, d = latest(tabs, "exports")
    iv, _ = latest(tabs, "imports")
    bv, _ = latest(tabs, "balance")
    tv, _ = latest(tabs, "total")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Exports ({d.strftime('%b %Y') if d else ''})", fmt(ev, "RM "))
    c2.metric("Imports", fmt(iv, "RM "))
    c3.metric("Trade Balance", fmt(bv, "RM "))
    c4.metric("Total Trade", fmt(tv, "RM "))
    st.divider()

    # Exports vs Imports
    st.subheader("Exports vs Imports")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=tabs["date"], y=tabs["exports"], mode="lines", name="Exports",
        fill="tozeroy", line=dict(color=COLORS["primary"], width=2), fillcolor="rgba(0,212,170,0.08)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Exports: RM %{y:,.0f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=tabs["date"], y=tabs["imports"], mode="lines", name="Imports",
        fill="tozeroy", line=dict(color=COLORS["secondary"], width=2), fillcolor="rgba(108,99,255,0.08)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Imports: RM %{y:,.0f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Bar(x=tabs["date"], y=tabs["balance"], name="Balance", opacity=0.4,
        marker_color=[COLORS["pos"] if v >= 0 else COLORS["neg"] for v in tabs["balance"].fillna(0)],
        hovertemplate="<b>%{x|%b %Y}</b><br>Balance: RM %{y:,.0f}<extra></extra>"), secondary_y=True)
    fig = style(fig, 420)
    fig.update_yaxes(title_text="RM", secondary_y=False, gridcolor=COLORS["grid"])
    fig.update_yaxes(title_text="Trade Balance", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # SITC composition
    col1, col2 = st.columns(2)
    sitc_s = sitc.sort_values("date")
    sitc_no = sitc_s[sitc_s["section"] != "overall"]
    ld = sitc_no["date"].max()
    sl = sitc_no[sitc_no["date"] == ld]

    with col1:
        st.subheader(f"Export Composition ({ld.strftime('%b %Y')})")
        labels = [SITC_SECTIONS.get(str(s), str(s)) for s in sl["section"]]
        fig_pe = go.Figure(go.Pie(labels=labels, values=sl["exports"], hole=0.45,
            textinfo="label+percent", textfont=dict(size=10),
            hovertemplate="<b>%{label}</b><br>RM %{value:,.0f}<br>%{percent}<extra></extra>"))
        st.plotly_chart(style(fig_pe, 400), use_container_width=True)

    with col2:
        st.subheader(f"Import Composition ({ld.strftime('%b %Y')})")
        fig_pi = go.Figure(go.Pie(labels=labels, values=sl["imports"], hole=0.45,
            textinfo="label+percent", textfont=dict(size=10),
            hovertemplate="<b>%{label}</b><br>RM %{value:,.0f}<br>%{percent}<extra></extra>"))
        st.plotly_chart(style(fig_pi, 400), use_container_width=True)

    # YoY Growth
    st.subheader("Trade Growth (YoY %)")
    tyoy = fseries(tr, "growth_yoy").sort_values("date")
    fig_g = go.Figure()
    for col, lbl, clr in [("exports", "Exports", COLORS["primary"]), ("imports", "Imports", COLORS["secondary"])]:
        if col in tyoy.columns:
            fig_g.add_trace(go.Scatter(x=tyoy["date"], y=tyoy[col], mode="lines", name=lbl,
                line=dict(color=clr, width=2),
                hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}%<extra></extra>"))
    fig_g.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
    st.plotly_chart(style(fig_g, 350), use_container_width=True)
