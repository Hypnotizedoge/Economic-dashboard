"""Financial — BOP, FDI"""
import streamlit as st
import plotly.graph_objects as go
from data_loader import load, latest, fmt, BOP_ACCOUNTS, load_fx_rates, load_money_supply
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

    # ── Money Supply Section ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Monetary Aggregates (M1, M2 & M3)")
    st.caption("Broad and narrow money aggregates of the financial system in Malaysia. M1 represents narrow money (currency and demand deposits); M2 includes M1 and quasi-money (savings, fixed deposits, etc.); M3 includes M2 and deposits placed with other banking institutions.")

    try:
        df_ms = load_money_supply().sort_values("date").copy()
        
        # Calculate YoY growth
        df_ms["m1_yoy"] = df_ms["m1"].pct_change(12) * 100
        df_ms["m2_yoy"] = df_ms["m2"].pct_change(12) * 100
        df_ms["m3_yoy"] = df_ms["m3"].pct_change(12) * 100
        
        col_mode, col_sel = st.columns([1, 2])
        with col_mode:
            ms_mode = st.radio(
                "Value Mode",
                options=["Nominal Value", "YoY Growth (%)"],
                horizontal=True,
                key="ms_view_mode",
                label_visibility="collapsed"
            )
            
        with col_sel:
            ms_choices = ["M1", "M2", "M3"]
            sel_ms = st.multiselect(
                "Select Aggregates",
                options=ms_choices,
                default=ms_choices,
                key="ms_aggregates_sel",
                label_visibility="collapsed"
            )
            
        if sel_ms:
            fig_ms = go.Figure()
            ms_colors = {
                "M1": COLORS["primary"],
                "M2": COLORS["secondary"],
                "M3": COLORS["accent1"]
            }
            
            for agg in sel_ms:
                col_name = agg.lower()
                if ms_mode == "Nominal Value":
                    y_vals = df_ms[col_name] / 1000.0  # Convert RM million to RM billion
                    hover_fmt = f"<b>{agg}</b><br>%{{x|%b %Y}}<br>RM %{{y:,.2f}}B<extra></extra>"
                else:
                    col_yoy = f"{col_name}_yoy"
                    y_vals = df_ms[col_yoy]
                    hover_fmt = f"<b>{agg} (YoY)</b><br>%{{x|%b %Y}}<br>%{{y:.2f}}%<extra></extra>"
                
                valid_mask = y_vals.notna()
                if not valid_mask.any():
                    continue
                    
                fig_ms.add_trace(go.Scatter(
                    x=df_ms.loc[valid_mask, "date"],
                    y=y_vals.loc[valid_mask],
                    mode="lines",
                    name=agg,
                    line=dict(color=ms_colors[agg], width=2.5),
                    hovertemplate=hover_fmt
                ))
                
            fig_ms = style(fig_ms, 420)
            if ms_mode == "Nominal Value":
                fig_ms.update_layout(yaxis_title="RM billion")
            else:
                fig_ms.update_layout(yaxis_title="YoY Growth (%)")
                fig_ms.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.4)
                
            st.plotly_chart(fig_ms, use_container_width=True)
        else:
            st.info("Please select at least one aggregate to display.")
    except Exception as e:
        st.error(f"Error loading money supply: {e}")

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
        col_mode, col_year = st.columns([3, 1])
        with col_mode:
            fx_mode = st.radio(
                "View Mode",
                options=["Raw Rate", "Indexed (Base = 100 on start date)"],
                horizontal=True,
                key="fx_view_mode",
                label_visibility="collapsed"
            )
        
        fx_filtered = fx.copy()
        if "Indexed" in fx_mode:
            with col_year:
                min_yr = int(fx["date"].dt.year.min())
                max_yr = int(fx["date"].dt.year.max())
                base_year = st.number_input(
                    "Start Year",
                    min_value=min_yr,
                    max_value=max_yr,
                    value=min_yr,
                    step=1,
                    format="%d",
                    key="fx_base_year_input"
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
