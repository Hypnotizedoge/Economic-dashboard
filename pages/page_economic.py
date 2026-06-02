"""Economic Growth — GDP, Productivity"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from data_loader import load, load_historical_gdp, fseries, latest, delta, fmt, GDP_SUPPLY_SECTORS, GDP_DEMAND_TYPES
from theme import style, COLORS


def render():
    st.markdown("## 📊 Economic Growth")
    st.caption("Quarterly Nominal GDP & Productivity")

    gdp_s = load("gdp_supply")
    gdp_d = load("gdp_demand")
    gdp_hist = load_historical_gdp()
    prod = load("productivity")

    # KPIs
    ov = fseries(gdp_s, "abs").query("sector=='p0'").sort_values("date")
    v, d = latest(ov, "value")
    dv = delta(ov, "value")
    yoy_ov = fseries(gdp_s, "growth_yoy").query("sector=='p0'").sort_values("date")
    yoy_v, _ = latest(yoy_ov, "value")
    qoq_ov = fseries(gdp_s, "growth_qoq").query("sector=='p0'").sort_values("date")
    qoq_v, _ = latest(qoq_ov, "value")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Nominal GDP ({d.strftime('%b %Y') if d else 'N/A'})", fmt(v, "RM "), fmt(dv, "RM ") if dv else None)
    c2.metric("YoY Growth", f"{yoy_v:.1f}%" if yoy_v is not None else "N/A")
    c3.metric("QoQ Growth", f"{qoq_v:.1f}%" if qoq_v is not None else "N/A")
    c4.metric("Data Range", f"1991 – {d.strftime('%b %Y') if d else 'N/A'}")
    st.divider()

    # Long-term GDP
    st.subheader("Long-Term GDP Trend (1991 – Present)")
    dosm = ov[["date", "value"]].rename(columns={"value": "gdp_nominal"})
    combined = pd.concat([gdp_hist, dosm]).sort_values("date").drop_duplicates("date", keep="last")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=combined["date"], y=combined["gdp_nominal"], mode="lines", fill="tozeroy",
        line=dict(color=COLORS["primary"], width=2), fillcolor="rgba(0,212,170,0.1)",
        name="Nominal GDP (RM mn)", hovertemplate="<b>%{x|%b %Y}</b><br>RM %{y:,.0f}M<extra></extra>"))
    fig.add_vline(x="2015-01-01", line_dash="dot", line_color=COLORS["muted"], opacity=0.5)
    fig.add_annotation(x="2015-01-01", y=combined["gdp_nominal"].max()*0.9, text="← CEIC | DOSM →",
        showarrow=False, font=dict(size=10, color=COLORS["muted"]))
    st.plotly_chart(style(fig, 380), use_container_width=True)

    # Supply & Demand side-by-side
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("GDP by Sector (Supply)")
        sabs = fseries(gdp_s, "abs").query("sector != 'p0'")
        fig_s = go.Figure()
        for code, lbl in list(GDP_SUPPLY_SECTORS.items())[1:]:
            sd = sabs.query(f"sector=='{code}'").sort_values("date")
            if sd.empty: continue
            fig_s.add_trace(go.Scatter(x=sd["date"], y=sd["value"], mode="lines", stackgroup="one",
                name=lbl, line=dict(width=0.5), hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>RM %{{y:,.0f}}M<extra></extra>"))
        fig_s = style(fig_s)
        fig_s.update_layout(yaxis_title="RM million")
        st.plotly_chart(fig_s, use_container_width=True)

    with col2:
        st.subheader("GDP by Expenditure (Demand)")
        dabs = fseries(gdp_d, "abs").query("type != 'e0'")
        fig_d = go.Figure()
        for code, lbl in list(GDP_DEMAND_TYPES.items())[1:]:
            dd = dabs.query(f"type=='{code}'").sort_values("date")
            if dd.empty: continue
            fig_d.add_trace(go.Bar(x=dd["date"], y=dd["value"], name=lbl,
                hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>RM %{{y:,.0f}}M<extra></extra>"))
        fig_d = style(fig_d)
        fig_d.update_layout(barmode="relative", yaxis_title="RM million")
        st.plotly_chart(fig_d, use_container_width=True)

    # Growth rates
    st.subheader("Sector Growth (YoY %)")
    yoy = fseries(gdp_s, "growth_yoy")
    sel = st.multiselect("Select sectors", list(GDP_SUPPLY_SECTORS.keys()), default=["p0","p3","p5"],
        format_func=lambda x: GDP_SUPPLY_SECTORS[x], key="gdp_sec")
    fig_g = go.Figure()
    for code in sel:
        lbl = GDP_SUPPLY_SECTORS[code]
        gd = yoy.query(f"sector=='{code}'").sort_values("date")
        if gd.empty: continue
        fig_g.add_trace(go.Scatter(x=gd["date"], y=gd["value"], mode="lines+markers", name=lbl,
            marker=dict(size=4), hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}%<extra></extra>"))
    fig_g.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
    st.plotly_chart(style(fig_g, 380), use_container_width=True)

    # Productivity
    st.subheader("Quarterly Productivity by Sector")
    prod_s = prod.sort_values("date") if "date" in prod.columns else prod
    if "sector" in prod.columns:
        sectors = prod["sector"].unique()
        fig_p = go.Figure()
        for s in sectors:
            ps = prod_s[prod_s["sector"] == s]
            col_val = [c for c in ps.columns if c not in ("date", "sector", "series")][0] if len(ps.columns) > 2 else None
            if col_val:
                fig_p.add_trace(go.Scatter(x=ps["date"], y=ps[col_val], mode="lines", name=str(s)))
        st.plotly_chart(style(fig_p, 380), use_container_width=True)
    else:
        st.dataframe(prod.head(20))
