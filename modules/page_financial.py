"""Financial — BOP, FDI"""
import streamlit as st
import plotly.graph_objects as go
from data_loader import load, latest, fmt, BOP_ACCOUNTS
from theme import style, COLORS


def render():
    st.markdown("## Financial")
    st.caption("Balance of Payments & Foreign Direct Investment")

    fdi = load("fdi").sort_values("date").copy()
    bop = load("bop").sort_values("date").copy()
    
    fdi["quarter"] = fdi["date"].dt.year.astype(str) + " Q" + fdi["date"].dt.quarter.astype(str)
    bop["quarter"] = bop["date"].dt.year.astype(str) + " Q" + bop["date"].dt.quarter.astype(str)

    # KPIs
    nv, fd = latest(fdi, "net")
    inv, _ = latest(fdi, "inflow")
    outv, _ = latest(fdi, "outflow")
    ca = bop.query("account=='ca'").sort_values("date")
    cav, bd = latest(ca, "balance")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Net FDI ({fd.strftime('%b %Y') if fd else ''})", fmt(nv, "RM ", d=2))
    c2.metric("FDI Inflow", fmt(inv, "RM ", d=2))
    c3.metric("FDI Outflow", fmt(outv, "RM ", d=2))
    c4.metric(f"Current Account ({bd.strftime('%b %Y') if bd else ''})", fmt(cav, "RM ", d=2))
    st.divider()

    st.subheader("FDI Flows")
    fig_f = go.Figure()
    fig_f.add_trace(go.Bar(x=fdi["date"], y=fdi["inflow"], name="Inflow",
        marker_color=COLORS["primary"], customdata=fdi["quarter"],
        hovertemplate="<b>%{customdata}</b><br>Inflow: RM %{y:,.2f}B<extra></extra>"))
    fig_f.add_trace(go.Bar(x=fdi["date"], y=fdi["outflow"], name="Outflow",
        marker_color=COLORS["accent1"], customdata=fdi["quarter"],
        hovertemplate="<b>%{customdata}</b><br>Outflow: RM %{y:,.2f}B<extra></extra>"))
    fig_f.add_trace(go.Scatter(x=fdi["date"], y=fdi["net"], mode="lines+markers",
        name="Net FDI", line=dict(color=COLORS["accent2"], width=2.5), marker=dict(size=5),
        customdata=fdi["quarter"],
        hovertemplate="<b>%{customdata}</b><br>Net: RM %{y:,.2f}B<extra></extra>"))
    fig_f = style(fig_f, 420)
    fig_f.update_layout(barmode="group", yaxis_title="RM billion")
    st.plotly_chart(fig_f, use_container_width=True)

    st.subheader("Balance of Payments")
    sel_bop = st.multiselect(
        "Filter Accounts",
        options=list(BOP_ACCOUNTS.keys()),
        default=list(BOP_ACCOUNTS.keys()),
        format_func=lambda x: BOP_ACCOUNTS[x],
        key="bop_accts_sel"
    )
    fig_b = go.Figure()
    for acct in sel_bop:
        lbl = BOP_ACCOUNTS[acct]
        ad = bop.query(f"account=='{acct}'").copy()
        if ad.empty: continue
        fig_b.add_trace(go.Scatter(x=ad["date"], y=ad["balance"], mode="lines+markers",
            name=lbl, marker=dict(size=4), customdata=ad["quarter"],
            hovertemplate=f"<b>{lbl}</b><br>%{{customdata}}<br>RM %{{y:,.1f}}M<extra></extra>"))
    fig_b.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
    fig_b = style(fig_b, 420)
    fig_b.update_layout(yaxis_title="RM million")
    st.plotly_chart(fig_b, use_container_width=True)
