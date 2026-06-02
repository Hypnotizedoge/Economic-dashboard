"""Prices & Production — CPI, PPI, SPPI, IPI, IOWRT"""
import streamlit as st
import plotly.graph_objects as go
from data_loader import load, fseries, latest, CPI_DIVISIONS, PPI_SECTIONS, IPI_SECTIONS, IOWRT_DIVISIONS, fmt
from theme import style, COLORS


def render():
    st.markdown("## Prices")
    st.caption("Consumer Price Index, Producer Price Index, Services PPI, Industrial Production, and Wholesale & Retail Trade")

    cpi = load("cpi")
    cpi_inf = load("cpi_inflation")
    ppi_raw = load("ppi")
    ppi_1d = load("ppi_1d")
    cpi_st = load("cpi_state")
    sppi = load("sppi")
    ipi = load("ipi")
    ipi_1d = load("ipi_1d")
    iowrt = load("iowrt")
    iowrt_2d = load("iowrt_2d")

    # KPIs
    cpi_ov = cpi.query("division=='overall'").sort_values("date")
    cv, cd = latest(cpi_ov, "index")
    inf_ov = cpi_inf.query("division=='overall'").sort_values("date")
    yoy_v, _ = latest(inf_ov, "inflation_yoy")
    mom_v, _ = latest(inf_ov, "inflation_mom")
    ppi_abs = fseries(ppi_raw, "abs").sort_values("date")
    pv, pd_ = latest(ppi_abs, "index")

    ipi_abs = fseries(ipi, "abs").sort_values("date")
    iowrt_abs = fseries(iowrt, "abs").sort_values("date")

    # KPIs for IPI and IOWRT
    iv, id_ = latest(ipi_abs, "index")
    isv, _ = latest(ipi_abs, "index_sa")
    wv, wd = latest(iowrt_abs, "volume")
    sv, _ = latest(iowrt_abs, "sales")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"CPI ({cd.strftime('%b %Y') if cd else ''})", f"{cv:.1f}" if cv else "N/A")
    c2.metric("CPI YoY Inflation", f"{yoy_v:.1f}%" if yoy_v is not None else "N/A")
    c3.metric("CPI MoM Change", f"{mom_v:.1f}%" if mom_v is not None else "N/A")
    c4.metric(f"PPI ({pd_.strftime('%b %Y') if pd_ else ''})", f"{pv:.1f}" if pv else "N/A")
    st.divider()

    tab_cpi, tab_ppi, tab_state, tab_ipi, tab_iowrt = st.tabs([
        "CPI", "PPI", "CPI by State", "Industrial Production", "Wholesale & Retail"
    ])

    with tab_cpi:
        st.subheader("CPI Index (2010 = 100)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cpi_ov["date"], y=cpi_ov["index"], mode="lines", fill="tozeroy",
            line=dict(color=COLORS["primary"], width=2), fillcolor="rgba(0,212,170,0.08)",
            hovertemplate="<b>%{x|%b %Y}</b><br>CPI: %{y:.1f}<extra></extra>"))
        st.plotly_chart(style(fig, 380), use_container_width=True)

        st.subheader("YoY Inflation by Category")
        divs = {k: v for k, v in CPI_DIVISIONS.items() if k != "overall"}
        sel = st.multiselect("Select categories", list(divs.keys()), default=["01", "04", "07"],
            format_func=lambda x: divs[x], key="cpi_cat")
        fig_i = go.Figure()
        for code in sel:
            lbl = divs[code]
            dd = cpi_inf.query(f"division=='{code}'").sort_values("date")
            if dd.empty: continue
            fig_i.add_trace(go.Scatter(x=dd["date"], y=dd["inflation_yoy"], mode="lines", name=lbl,
                hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}%<extra></extra>"))
        fig_i.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
        fig_i = style(fig_i, 400)
        fig_i.update_layout(yaxis_title="YoY Inflation (%)")
        st.plotly_chart(fig_i, use_container_width=True)

    with tab_ppi:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("PPI Headline (2010 = 100)")
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=ppi_abs["date"], y=ppi_abs["index"], mode="lines",
                name="PPI", line=dict(color=COLORS["secondary"], width=2.5),
                hovertemplate="<b>%{x|%b %Y}</b><br>PPI: %{y:.1f}<extra></extra>"))
            if "index_sa" in ppi_abs.columns:
                fig_p.add_trace(go.Scatter(x=ppi_abs["date"], y=ppi_abs["index_sa"], mode="lines",
                    name="PPI (SA)", line=dict(color=COLORS["accent3"], width=2, dash="dot"),
                    hovertemplate="<b>%{x|%b %Y}</b><br>SA: %{y:.1f}<extra></extra>"))
            st.plotly_chart(style(fig_p, 380), use_container_width=True)

        with col2:
            st.subheader("PPI by Industry")
            sel_ppi_sec = st.multiselect(
                "Filter Industries",
                options=list(PPI_SECTIONS.keys()),
                default=list(PPI_SECTIONS.keys()),
                format_func=lambda x: PPI_SECTIONS[x],
                key="ppi_sec_sel"
            )
            pabs = fseries(ppi_1d, "abs")
            fig_pi = go.Figure()
            for code in sel_ppi_sec:
                lbl = PPI_SECTIONS[code]
                sd = pabs.query(f"section=='{code}'").sort_values("date")
                if sd.empty: continue
                fig_pi.add_trace(go.Scatter(x=sd["date"], y=sd["index"], mode="lines", name=lbl,
                    hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}<extra></extra>"))
            st.plotly_chart(style(fig_pi, 380), use_container_width=True)

        # SPPI
        st.subheader("Services PPI (Quarterly)")
        sppi_abs = fseries(sppi, "abs").sort_values("date") if "series" in sppi.columns else sppi.sort_values("date")
        sppi_abs = sppi_abs.copy()
        sppi_abs["quarter"] = sppi_abs["date"].dt.year.astype(str) + " Q" + sppi_abs["date"].dt.quarter.astype(str)
        idx_col = "index" if "index" in sppi_abs.columns else sppi_abs.columns[-1]
        fig_sp = go.Figure()
        fig_sp.add_trace(go.Scatter(x=sppi_abs["date"], y=sppi_abs[idx_col], mode="lines+markers",
            line=dict(color=COLORS["accent4"], width=2.5), marker=dict(size=5),
            customdata=sppi_abs["quarter"],
            hovertemplate="<b>%{customdata}</b><br>SPPI: %{y:.1f}<extra></extra>"))
        st.plotly_chart(style(fig_sp, 350), use_container_width=True)

    with tab_state:
        st.subheader("CPI by State")
        cs = cpi_st.query("division=='overall'").sort_values("date")
        states = sorted(cs["state"].unique())
        sel_st = st.multiselect("Select states", states, default=states[:5], key="st_sel")
        fig_st = go.Figure()
        for s in sel_st:
            sd = cs.query(f"state=='{s}'")
            fig_st.add_trace(go.Scatter(x=sd["date"], y=sd["index"], mode="lines", name=s,
                hovertemplate=f"<b>{s}</b><br>%{{x|%b %Y}}<br>CPI: %{{y:.1f}}<extra></extra>"))
        fig_st = style(fig_st, 420)
        fig_st.update_layout(yaxis_title="CPI (2010=100)")
        st.plotly_chart(fig_st, use_container_width=True)

    with tab_ipi:
        c_ipi_1, c_ipi_2 = st.columns(2)
        c_ipi_1.metric(f"IPI ({id_.strftime('%b %Y') if id_ else ''})", f"{iv:.1f}" if iv else "N/A")
        c_ipi_2.metric("IPI (SA)", f"{isv:.1f}" if isv else "N/A")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("IPI Headline")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ipi_abs["date"], y=ipi_abs["index"], mode="lines",
                name="IPI", line=dict(color=COLORS["primary"], width=2.5),
                hovertemplate="<b>%{x|%b %Y}</b><br>IPI: %{y:.1f}<extra></extra>"))
            fig.add_trace(go.Scatter(x=ipi_abs["date"], y=ipi_abs["index_sa"], mode="lines",
                name="IPI (SA)", line=dict(color=COLORS["accent3"], width=2, dash="dot"),
                hovertemplate="<b>%{x|%b %Y}</b><br>SA: %{y:.1f}<extra></extra>"))
            st.plotly_chart(style(fig, 380), use_container_width=True)

        with col2:
            st.subheader("IPI by Section")
            sel_ipi_sec = st.multiselect(
                "Filter Sections",
                options=list(IPI_SECTIONS.keys()),
                default=list(IPI_SECTIONS.keys()),
                format_func=lambda x: IPI_SECTIONS[x],
                key="ipi_sec_sel"
            )
            iabs = fseries(ipi_1d, "abs")
            fig_s = go.Figure()
            for code in sel_ipi_sec:
                lbl = IPI_SECTIONS[code]
                sd = iabs.query(f"section=='{code}'").sort_values("date")
                if sd.empty: continue
                fig_s.add_trace(go.Scatter(x=sd["date"], y=sd["index"], mode="lines", name=lbl,
                    hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>%{{y:.1f}}<extra></extra>"))
            st.plotly_chart(style(fig_s, 380), use_container_width=True)

        # IPI Growth
        st.subheader("IPI Growth (YoY %)")
        ipi_yoy = fseries(ipi, "growth_yoy").sort_values("date")
        fig_g = go.Figure()
        fig_g.add_trace(go.Bar(x=ipi_yoy["date"], y=ipi_yoy["index"],
            marker_color=[COLORS["pos"] if v >= 0 else COLORS["neg"] for v in ipi_yoy["index"].fillna(0)],
            hovertemplate="<b>%{x|%b %Y}</b><br>YoY: %{y:.1f}%<extra></extra>"))
        fig_g.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
        fig_g = style(fig_g, 320)
        fig_g.update_layout(showlegend=False, yaxis_title="YoY Growth (%)")
        st.plotly_chart(fig_g, use_container_width=True)

    with tab_iowrt:
        c_iowrt_1, c_iowrt_2 = st.columns(2)
        c_iowrt_1.metric(f"IOWRT Volume ({wd.strftime('%b %Y') if wd else ''})", f"{wv:.1f}" if wv else "N/A")
        c_iowrt_2.metric("IOWRT Sales (RM mn)", fmt(sv))
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("IOWRT Volume Index")
            fig_w = go.Figure()
            fig_w.add_trace(go.Scatter(x=iowrt_abs["date"], y=iowrt_abs["volume"], mode="lines",
                name="Volume", line=dict(color=COLORS["secondary"], width=2.5),
                hovertemplate="<b>%{x|%b %Y}</b><br>Vol: %{y:.1f}<extra></extra>"))
            if "volume_sa" in iowrt_abs.columns:
                fig_w.add_trace(go.Scatter(x=iowrt_abs["date"], y=iowrt_abs["volume_sa"], mode="lines",
                    name="Volume (SA)", line=dict(color=COLORS["accent5"], width=2, dash="dot"),
                    hovertemplate="<b>%{x|%b %Y}</b><br>SA: %{y:.1f}<extra></extra>"))
            st.plotly_chart(style(fig_w, 380), use_container_width=True)

        with col2:
            st.subheader("Sales by Division")
            wabs = fseries(iowrt_2d, "abs")
            fig_div = go.Figure()
            for code, lbl in IOWRT_DIVISIONS.items():
                sd = wabs.query(f"division=='{code}'").sort_values("date")
                if sd.empty: continue
                fig_div.add_trace(go.Bar(x=sd["date"], y=sd["sales"], name=lbl,
                    hovertemplate=f"<b>{lbl}</b><br>%{{x|%b %Y}}<br>RM %{{y:,.0f}}M<extra></extra>"))
            fig_div = style(fig_div, 380)
            fig_div.update_layout(barmode="group", yaxis_title="Sales (RM mn)")
            st.plotly_chart(fig_div, use_container_width=True)
