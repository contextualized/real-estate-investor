"""Seller Forecast Tab - Calculate net proceeds from sale."""

from decimal import Decimal

import streamlit as st

from bc_real_estate import SellerCalculator, get_config
from bc_real_estate.models import SaleDetails


def render() -> None:
    """Render the seller forecast tab."""
    st.header("📈 Seller Forecast: Net Proceeds")
    st.markdown("Calculate your net proceeds from selling the property.")

    # Config editor
    with st.expander("⚙️ Capital Gains Configuration"):
        config = get_config()
        inclusion_rate_option = st.radio(
            "Capital Gains Inclusion Rate",
            options=["50% (Default)", "66.67% (High Income)"],
            index=0,
            help="Taxable portion of capital gains",
        )
        inclusion_rate = Decimal("0.50") if "50%" in inclusion_rate_option else Decimal("0.6667")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sale Details")
        sale_price = st.number_input(
            "Sale Price ($)",
            min_value=100000,
            max_value=20000000,
            value=1000000,
            step=10000,
            help="Expected sale price",
        )

        holding_period = st.number_input(
            "Holding Period (years)",
            min_value=0.1,
            max_value=50.0,
            value=5.0,
            step=0.5,
            format="%.1f",
            help="Years between purchase and sale",
        )

        is_principal_residence = st.checkbox(
            "Principal Residence",
            value=False,
            help="Apply Principal Residence Exemption (PRE) - no capital gains tax",
        )

    with col2:
        st.subheader("Cost Information")

        # Auto-fill from buyer results if available
        if "buyer_results" in st.session_state:
            default_acq_costs = float(st.session_state.buyer_results.total_cash_to_close)
            st.info("✅ Acquisition costs auto-filled from Buyer Assessment")
        else:
            default_acq_costs = 177050.0
            st.warning("⚠️ Using example acquisition costs. Complete Buyer Assessment for accurate values.")

        acquisition_costs = st.number_input(
            "Acquisition Costs ($)",
            min_value=0,
            max_value=10000000,
            value=int(default_acq_costs),
            step=1000,
            help="Total cash to close from purchase (down payment + PTT + closing)",
        )

        capital_improvements = st.number_input(
            "Capital Improvements ($)",
            min_value=0,
            max_value=5000000,
            value=0,
            step=5000,
            help="Major renovations/improvements that increase property value",
        )

        st.info(
            """
            **BC Marginal Tax Rates 2026:**
            - Up to $55,867: 20.06%
            - $55,867 - $111,733: 28.20%
            - $111,733 - $127,299: 36.75%
            - $127,299 - $172,602: 40.70%
            - $172,602 - $246,752: 43.70%
            - Over $246,752: 49.80%
            """
        )

        marginal_tax_rate = st.number_input(
            "Marginal Tax Rate (%)",
            min_value=0.0,
            max_value=60.0,
            value=43.7,
            step=0.1,
            format="%.2f",
            help="Your marginal tax rate for capital gains",
        )

    # Calculate button
    if st.button("Calculate Sale Proceeds", type="primary", use_container_width=True):
        try:
            # Create models
            sale_details = SaleDetails(
                sale_price=Decimal(str(sale_price)),
                holding_period_years=Decimal(str(holding_period)),
                is_principal_residence=is_principal_residence,
                marginal_tax_rate=Decimal(str(marginal_tax_rate)),
                capital_improvements=Decimal(str(capital_improvements)),
            )

            # Calculate
            calculator = SellerCalculator()
            results = calculator.calculate_all(
                sale_details,
                Decimal(str(acquisition_costs)),
                inclusion_rate,
            )

            # Store in session state for comparison tab
            st.session_state.seller_results = results
            st.session_state.seller_inputs = {
                "sale_price": sale_price,
                "holding_period": holding_period,
            }

            # Display results
            st.success("✅ Calculation Complete!")

            # Sale Breakdown
            st.subheader("💰 Sale Breakdown")
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.metric("Gross Proceeds", f"${results.gross_proceeds:,.2f}")

            with col_b:
                st.metric("Realtor Commission", f"-${results.realtor_commission:,.2f}")

            with col_c:
                st.metric("Legal Fees", f"-${results.legal_fees:,.2f}")

            # Capital Gains
            st.subheader("📈 Capital Gains Analysis")
            col_d, col_e, col_f = st.columns(3)

            with col_d:
                st.metric("Adjusted Cost Base (ACB)", f"${results.adjusted_cost_base:,.2f}")
                st.caption(f"Acquisition: ${acquisition_costs:,.2f}")
                if capital_improvements > 0:
                    st.caption(f"Improvements: +${capital_improvements:,.2f}")

            with col_e:
                capital_gain_delta = "Profit" if results.capital_gain >= 0 else "Loss"
                st.metric(
                    "Capital Gain",
                    f"${results.capital_gain:,.2f}",
                    delta=capital_gain_delta,
                    delta_color="normal" if results.capital_gain >= 0 else "inverse",
                )

            with col_f:
                if results.principal_residence_exemption_applied:
                    st.metric("Taxable Capital Gain", "$0.00")
                    st.caption("✅ Principal Residence Exemption")
                else:
                    st.metric(
                        "Taxable Capital Gain",
                        f"${results.taxable_capital_gain:,.2f}",
                    )
                    st.caption(f"{float(inclusion_rate)*100:.1f}% inclusion rate")

            st.divider()
            col_g, col_h = st.columns(2)

            with col_g:
                st.metric("Capital Gains Tax", f"-${results.capital_gains_tax:,.2f}")

            with col_h:
                profit_delta = "Profit" if results.net_proceeds > acquisition_costs else "Loss"
                st.metric(
                    "**Net Proceeds**",
                    f"${results.net_proceeds:,.2f}",
                    delta=profit_delta,
                    delta_color="normal",
                    help="Amount you receive after all costs and taxes",
                )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    render()
