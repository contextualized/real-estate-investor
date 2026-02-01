"""Scenario Comparison Tab - Investment analysis with ROCI and IRR."""

from decimal import Decimal

import plotly.graph_objects as go
import streamlit as st

from bc_real_estate import InvestmentAnalyzer


def render() -> None:
    """Render the scenario comparison tab."""
    st.header("📈 Scenario Comparison: Investment Analysis")
    st.markdown("Analyze investment returns with ROCI and IRR calculations.")

    # Validate prerequisite data
    if "buyer_results" not in st.session_state or "seller_results" not in st.session_state:
        st.warning(
            """
            ⚠️ **Missing Data**

            Please complete both:
            1. **Buyer Assessment** tab
            2. **Seller Forecast** tab

            Then return here to view investment analysis.
            """
        )
        return

    buyer_results = st.session_state.buyer_results
    seller_results = st.session_state.seller_results

    # Get holding period from seller inputs
    holding_period = Decimal(str(st.session_state.seller_inputs["holding_period"]))

    # Calculate investment metrics
    comparison_results = InvestmentAnalyzer.calculate_all(
        buyer_results,
        seller_results,
        holding_period,
    )

    # Display key metrics
    st.subheader("🎯 Key Investment Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Cash Invested",
            f"${comparison_results.total_cash_invested:,.0f}",
            help="Initial cash to close + cumulative negative cash flow",
        )

    with col2:
        profit_label = "Net Profit" if comparison_results.net_profit >= 0 else "Net Loss"
        st.metric(
            profit_label,
            f"${abs(comparison_results.net_profit):,.0f}",
            delta="Profit" if comparison_results.net_profit >= 0 else "Loss",
            delta_color="normal" if comparison_results.net_profit >= 0 else "inverse",
            help="Total return from investment",
        )

    with col3:
        st.metric(
            "ROCI",
            f"{comparison_results.roci_percent:.2f}%",
            help="Return on Cash Invested",
        )

    with col4:
        st.metric(
            "IRR (Annual)",
            f"{comparison_results.irr_percent:.2f}%",
            help="Internal Rate of Return (annualized)",
        )

    # Detailed breakdown
    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("💵 Cash Invested")
        st.metric("Initial Cash to Close", f"${buyer_results.total_cash_to_close:,.2f}")
        st.metric(
            "Cumulative Cash Flow",
            f"${comparison_results.cumulative_cash_flow:,.2f}",
            delta="Positive" if comparison_results.cumulative_cash_flow >= 0 else "Negative",
            delta_color="normal" if comparison_results.cumulative_cash_flow >= 0 else "inverse",
            help=f"Net cash flow over {comparison_results.holding_period_months} months",
        )
        st.metric(
            "**Total Invested**",
            f"${comparison_results.total_cash_invested:,.2f}",
            help="Sum of initial cash and negative cash flows",
        )

    with col_b:
        st.subheader("💰 Returns")
        st.metric("Net Proceeds from Sale", f"${seller_results.net_proceeds:,.2f}")
        st.metric(
            "Less: Total Cash Invested",
            f"-${comparison_results.total_cash_invested:,.2f}",
        )
        if comparison_results.cumulative_cash_flow > 0:
            st.metric(
                "Plus: Positive Cash Flow",
                f"+${comparison_results.cumulative_cash_flow:,.2f}",
            )
        st.metric(
            "**Total Return**",
            f"${comparison_results.total_return:,.2f}",
            delta="Profit" if comparison_results.total_return >= 0 else "Loss",
            delta_color="normal" if comparison_results.total_return >= 0 else "inverse",
        )

    # Break-even chart
    st.divider()
    st.subheader("📉 Break-Even Analysis")

    # Get purchase price from buyer inputs
    purchase_price = st.session_state.buyer_inputs["purchase_price"]

    # Calculate ROCI for various sale prices
    sale_price_scenarios = []
    roci_scenarios = []
    current_sale_price = st.session_state.seller_inputs["sale_price"]

    for multiplier in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]:
        scenario_sale_price = purchase_price * multiplier
        sale_price_scenarios.append(scenario_sale_price)

        # Simple ROCI approximation
        # Net proceeds ~= sale_price - commission - acquisition_costs
        commission = scenario_sale_price * 0.03  # Approximate
        net_proceeds = scenario_sale_price - commission - 1500
        total_return = net_proceeds - float(comparison_results.total_cash_invested)
        if comparison_results.cumulative_cash_flow > 0:
            total_return += float(comparison_results.cumulative_cash_flow)

        roci = (total_return / float(comparison_results.total_cash_invested)) * 100
        roci_scenarios.append(roci)

    # Create plotly chart
    fig = go.Figure()

    # ROCI line
    fig.add_trace(
        go.Scatter(
            x=sale_price_scenarios,
            y=roci_scenarios,
            mode="lines+markers",
            name="ROCI",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6),
        )
    )

    # Break-even line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Break-Even",
        annotation_position="right",
    )

    # Current scenario marker
    current_roci = float(comparison_results.roci_percent)
    fig.add_trace(
        go.Scatter(
            x=[current_sale_price],
            y=[current_roci],
            mode="markers",
            name="Current Scenario",
            marker=dict(size=15, color="red", symbol="star"),
        )
    )

    fig.update_layout(
        title="ROCI by Sale Price",
        xaxis_title="Sale Price ($)",
        yaxis_title="ROCI (%)",
        hovermode="x unified",
        height=400,
    )

    fig.update_xaxes(tickformat="$,.0f")
    fig.update_yaxes(tickformat=".1f")

    st.plotly_chart(fig, use_container_width=True)

    # Interpretation
    # Find break-even price (ROCI closest to 0)
    min_diff = float("inf")
    break_even_price = sale_price_scenarios[0]
    for price, roci in zip(sale_price_scenarios, roci_scenarios):
        if abs(roci) < abs(min_diff):
            min_diff = roci
            break_even_price = price

    st.info(
        f"""
        **Interpretation:**

        - **Current Sale Price:** ${current_sale_price:,.0f}
        - **Current ROCI:** {current_roci:.2f}%
        - **Break-Even Price:** ~${break_even_price:,.0f}

        To break even on this investment, you would need to sell at approximately ${break_even_price:,.0f}.
        """
    )


if __name__ == "__main__":
    render()
