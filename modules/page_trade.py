"""Trade — Exports, imports, trade balance, SITC"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_loader import load, fseries, latest, fmt, SITC_SECTIONS
from theme import style, COLORS, COLOR_SEQ


def render():
    st.markdown("## Trade")
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
    sitc_s = sitc.sort_values("date")
    sitc_no = sitc_s[sitc_s["section"] != "overall"]

    st.subheader("Trade Composition by SITC (Time Series)")
    fig_comp = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Export Composition", "Import Composition"),
        shared_yaxes=True,
        horizontal_spacing=0.05
    )

    first_legend = True
    idx = 0
    for code, lbl in SITC_SECTIONS.items():
        if code == "overall": continue
        sd = sitc_no[sitc_no["section"] == code]
        if sd.empty: continue

        color = COLOR_SEQ[idx % len(COLOR_SEQ)]

        # Add Exports (Col 1)
        fig_comp.add_trace(
            go.Bar(x=sd["date"], y=sd["exports"], name=lbl,
                legendgroup=lbl, showlegend=first_legend, marker_color=color,
                hovertemplate=f"<b>{lbl} (Export)</b><br>%{{x|%b %Y}}<br>RM %{{y:,.0f}}<extra></extra>"),
            row=1, col=1
        )

        # Add Imports (Col 2)
        fig_comp.add_trace(
            go.Bar(x=sd["date"], y=sd["imports"], name=lbl,
                legendgroup=lbl, showlegend=False, marker_color=color,
                hovertemplate=f"<b>{lbl} (Import)</b><br>%{{x|%b %Y}}<br>RM %{{y:,.0f}}<extra></extra>"),
            row=1, col=2
        )
        first_legend = False
        idx += 1

    fig_comp.update_layout(barmode="stack")
    fig_comp = style(fig_comp, 500)
    fig_comp.update_yaxes(title_text="RM million", row=1, col=1)
    st.plotly_chart(fig_comp, use_container_width=True)

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
