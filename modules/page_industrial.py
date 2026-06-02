"""Industrial & Retail — IPI, IOWRT"""
import streamlit as st
import plotly.graph_objects as go
from data_loader import load, fseries, latest, fmt, IPI_SECTIONS, IOWRT_DIVISIONS
from theme import style, COLORS


def render():
    st.markdown("## 🏭 Industrial & Retail")
    st.caption("Industrial Production Index & Wholesale/Retail Trade")

    ipi = load("ipi")
    ipi_1d = load("ipi_1d")
    iowrt = load("iowrt")
    iowrt_2d = load("iowrt_2d")

    ipi_abs = fseries(ipi, "abs").sort_values("date")
    iowrt_abs = fseries(iowrt, "abs").sort_values("date")

    # KPIs
    iv, id_ = latest(ipi_abs, "index")
    isv, _ = latest(ipi_abs, "index_sa")
    wv, wd = latest(iowrt_abs, "volume")
    sv, _ = latest(iowrt_abs, "sales")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"IPI ({id_.strftime('%b %Y') if id_ else ''})", f"{iv:.1f}" if iv else "N/A")
    c2.metric("IPI (SA)", f"{isv:.1f}" if isv else "N/A")
    c3.metric(f"IOWRT Volume ({wd.strftime('%b %Y') if wd else ''})", f"{wv:.1f}" if wv else "N/A")
    c4.metric("IOWRT Sales (RM mn)", fmt(sv))
    st.divider()

    tab_ipi, tab_iowrt = st.tabs(["🏭 Industrial Production", "🛒 Wholesale & Retail"])

    with tab_ipi:
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
