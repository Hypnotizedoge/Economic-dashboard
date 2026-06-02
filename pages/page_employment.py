"""Employment — Labour force, unemployment, youth unemployment"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_loader import load, latest, delta, fmt
from theme import style, COLORS


def render():
    st.markdown("# 👷 Employment")
    st.caption("Monthly labour force statistics")

    lfs = load("lfs_sa").sort_values("date")
    youth = load("lfs_youth").sort_values("date")
    dur = load("lfs_duration").sort_values("date")

    # KPIs
    ur, d = latest(lfs, "u_rate")
    lf, _ = latest(lfs, "lf")
    pr, _ = latest(lfs, "p_rate")
    emp, _ = latest(lfs, "lf_employed")
    dur_ = delta(lfs, "u_rate")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Unemployment Rate ({d.strftime('%b %Y') if d else ''})", f"{ur:.1f}%" if ur else "N/A",
              f"{dur_:+.1f}pp" if dur_ else None, delta_color="inverse")
    c2.metric("Labour Force", fmt(lf * 1000) if lf else "N/A")
    c3.metric("Employed", fmt(emp * 1000) if emp else "N/A")
    c4.metric("Participation Rate", f"{pr:.1f}%" if pr else "N/A")
    st.divider()

    # Dual-axis: Labour Force + Unemployment Rate
    st.subheader("Labour Force & Unemployment Rate")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=lfs["date"], y=lfs["lf"], mode="lines", name="Labour Force ('000)",
        fill="tozeroy", line=dict(color=COLORS["primary"], width=2), fillcolor="rgba(0,212,170,0.08)",
        hovertemplate="<b>%{x|%b %Y}</b><br>LF: %{y:,.1f}K<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=lfs["date"], y=lfs["u_rate"], mode="lines+markers",
        name="Unemployment Rate (%)", line=dict(color=COLORS["accent1"], width=2.5), marker=dict(size=3),
        hovertemplate="<b>%{x|%b %Y}</b><br>U-Rate: %{y:.1f}%<extra></extra>"), secondary_y=True)
    fig = style(fig, 420)
    fig.update_yaxes(title_text="Labour Force ('000)", secondary_y=False, gridcolor=COLORS["grid"])
    fig.update_yaxes(title_text="Unemployment Rate (%)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Youth Unemployment Rate")
        fig_y = go.Figure()
        fig_y.add_trace(go.Scatter(x=youth["date"], y=youth["u_rate_15_24"], mode="lines",
            name="Age 15–24", line=dict(color=COLORS["accent2"], width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>15-24: %{y:.1f}%<extra></extra>"))
        fig_y.add_trace(go.Scatter(x=youth["date"], y=youth["u_rate_15_30"], mode="lines",
            name="Age 15–30", line=dict(color=COLORS["accent5"], width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>15-30: %{y:.1f}%<extra></extra>"))
        fig_y = style(fig_y, 380)
        fig_y.update_layout(yaxis_title="Unemployment Rate (%)")
        st.plotly_chart(fig_y, use_container_width=True)

    with col2:
        st.subheader("Unemployment by Duration")
        dur_cols = [c for c in dur.columns if c != "date"]
        fig_d = go.Figure()
        for col in dur_cols:
            fig_d.add_trace(go.Scatter(x=dur["date"], y=dur[col], mode="lines", stackgroup="one",
                name=col.replace("_", " ").title(), line=dict(width=0.5)))
        fig_d = style(fig_d, 380)
        fig_d.update_layout(yaxis_title="Persons ('000)")
        st.plotly_chart(fig_d, use_container_width=True)

    # Employed vs Unemployed stacked
    st.subheader("Employment Composition")
    fig_e = go.Figure()
    fig_e.add_trace(go.Bar(x=lfs["date"], y=lfs["lf_employed"], name="Employed ('000)",
        marker_color=COLORS["primary"], hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.1f}K<extra></extra>"))
    fig_e.add_trace(go.Bar(x=lfs["date"], y=lfs["lf_unemployed"], name="Unemployed ('000)",
        marker_color=COLORS["accent1"], hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.1f}K<extra></extra>"))
    fig_e = style(fig_e, 350)
    fig_e.update_layout(barmode="stack", yaxis_title="Persons ('000)")
    st.plotly_chart(fig_e, use_container_width=True)
