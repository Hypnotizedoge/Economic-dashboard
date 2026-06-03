"""Financial — BOP, FDI"""
import streamlit as st
import plotly.graph_objects as go
from data_loader import load, latest, fmt, BOP_ACCOUNTS, load_fx_rates
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
        fig_b.add_trace(go.Bar(
            x=ad["date"],
            y=ad["balance"],
            name=lbl,
            customdata=ad["quarter"],
            hovertemplate=f"<b>{lbl}</b><br>%{{customdata}}<br>RM %{{y:,.1f}}M<extra></extra>"
        ))
    fig_b.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
    fig_b = style(fig_b, 420)
    fig_b.update_layout(barmode="relative", yaxis_title="RM million")
    st.plotly_chart(fig_b, use_container_width=True)

    # ── Exchange Rates Section ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Exchange Rates (MYR per Foreign Currency)")
    st.caption("Historical exchange rates of major currencies against the Malaysian Ringgit (MYR). A lower rate indicates MYR strength; a higher rate indicates MYR weakness.")

    try:
        fx = load_fx_rates().sort_values("date").copy()
        
        # Get list of all available currencies
        all_currencies = [col for col in fx.columns if col not in ["date", "rate_type"]]
        
        # Multiselect for currencies
        sel_currencies = st.multiselect(
            "Select Currencies",
            options=all_currencies,
            default=["USD", "EUR", "SGD", "GBP", "JPY"],
            key="fx_currencies_sel"
        )
        
        # Toggle between raw rate and indexed rate (base = 100)
        fx_mode = st.radio(
            "View Mode",
            options=["Raw Rate", "Indexed (Base = 100 on start date)"],
            horizontal=True,
            key="fx_view_mode",
            label_visibility="collapsed"
        )
        
        fx_filtered = fx.copy()
        if "Indexed" in fx_mode:
            unique_years = sorted(list(fx["date"].dt.year.unique()))
            base_year = st.selectbox(
                "Select Indexing Start Year",
                options=unique_years,
                index=0,
                key="fx_base_year_sel"
            )
            fx_filtered = fx[fx["date"].dt.year >= base_year].copy()
        
        if sel_currencies:
            fig_x = go.Figure()
            for col in sel_currencies:
                fx_sub = fx_filtered[["date", col]].dropna()
                if fx_sub.empty: continue
                
                if "Indexed" in fx_mode:
                    first_val = fx_sub[col].iloc[0]
                    y_vals = (fx_sub[col] / first_val) * 100
                    hover_fmt = "<b>{name} (Indexed)</b><br>%{x|%d %b %Y}<br>Index: %{y:.2f} (Base=100)<extra></extra>"
                else:
                    y_vals = fx_sub[col]
                    hover_fmt = "<b>{name}</b><br>%{x|%d %b %Y}<br>Rate: %{y:.4f}<extra></extra>"
                    
                fig_x.add_trace(go.Scatter(
                    x=fx_sub["date"],
                    y=y_vals,
                    mode="lines",
                    name=col,
                    hovertemplate=hover_fmt.replace("{name}", col)
                ))
            
            fig_x = style(fig_x, 420)
            if "Indexed" in fx_mode:
                fig_x.update_layout(yaxis_title="Index (Base = 100)")
            else:
                fig_x.update_layout(yaxis_title="MYR per unit of foreign currency")
            st.plotly_chart(fig_x, use_container_width=True)
        else:
            st.info("Please select at least one currency to display.")
    except Exception as e:
        st.error(f"Error loading exchange rates: {e}")
