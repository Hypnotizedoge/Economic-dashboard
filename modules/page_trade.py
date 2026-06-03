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
    st.subheader("Trade Balance")
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
    sitc_s = sitc.sort_values(["section", "date"]).copy()
    sitc_s["exports_yoy"] = sitc_s.groupby("section")["exports"].pct_change(12) * 100
    sitc_s["imports_yoy"] = sitc_s.groupby("section")["imports"].pct_change(12) * 100
    
    sitc_no = sitc_s[sitc_s["section"] != "overall"].copy()

    st.subheader("SITC Composition Analysis")
    comp_metric = st.radio(
        "SITC Composition Metric",
        options=["Nominal Value", "YoY Growth (%)"],
        horizontal=True,
        key="sitc_metric_sel",
        label_visibility="collapsed"
    )

    st.subheader("Export Composition by SITC (Time Series)")
    
    sitc_cats = {k: v for k, v in SITC_SECTIONS.items() if k != "overall"}
    sel_sitc_cats = st.multiselect(
        "Filter SITC Sections",
        options=list(sitc_cats.keys()),
        default=list(sitc_cats.keys()),
        format_func=lambda x: sitc_cats[x],
        key="sitc_categories_sel"
    )

    # 1. Export Composition Chart
    fig_pe = go.Figure()
    idx = 0
    for code in sel_sitc_cats:
        lbl = sitc_cats[code]
        sd = sitc_no[sitc_no["section"] == code].sort_values("date")
        if sd.empty: continue
        color = COLOR_SEQ[idx % len(COLOR_SEQ)]
        if comp_metric == "Nominal Value":
            fig_pe.add_trace(go.Bar(
                x=sd["date"], y=sd["exports"], name=lbl,
                marker_color=color,
                hovertemplate=f"<b>{lbl} (Export)</b><br>%{{x|%b %Y}}<br>RM %{{y:,.0f}}<extra></extra>"
            ))
        else:
            fig_pe.add_trace(go.Scatter(
                x=sd["date"], y=sd["exports_yoy"], mode="lines", name=lbl,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{lbl} (Export YoY)</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}%<extra></extra>"
            ))
        idx += 1
    fig_pe = style(fig_pe, 420)
    if comp_metric == "Nominal Value":
        fig_pe.update_yaxes(title_text="RM")
        fig_pe.update_layout(barmode="stack")
    else:
        fig_pe.update_yaxes(title_text="YoY Growth (%)")
        fig_pe.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
    st.plotly_chart(fig_pe, use_container_width=True)

    # 2. Import Composition Chart
    st.subheader("Import Composition by SITC (Time Series)")
    fig_pi = go.Figure()
    idx = 0
    for code in sel_sitc_cats:
        lbl = sitc_cats[code]
        sd = sitc_no[sitc_no["section"] == code].sort_values("date")
        if sd.empty: continue
        color = COLOR_SEQ[idx % len(COLOR_SEQ)]
        if comp_metric == "Nominal Value":
            fig_pi.add_trace(go.Bar(
                x=sd["date"], y=sd["imports"], name=lbl,
                marker_color=color,
                hovertemplate=f"<b>{lbl} (Import)</b><br>%{{x|%b %Y}}<br>RM %{{y:,.0f}}<extra></extra>"
            ))
        else:
            fig_pi.add_trace(go.Scatter(
                x=sd["date"], y=sd["imports_yoy"], mode="lines", name=lbl,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{lbl} (Import YoY)</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}%<extra></extra>"
            ))
        idx += 1
    fig_pi = style(fig_pi, 420)
    if comp_metric == "Nominal Value":
        fig_pi.update_yaxes(title_text="RM")
        fig_pi.update_layout(barmode="stack")
    else:
        fig_pi.update_yaxes(title_text="YoY Growth (%)")
        fig_pi.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
    st.plotly_chart(fig_pi, use_container_width=True)

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
