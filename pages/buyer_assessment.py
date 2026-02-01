"""Buyer Assessment Tab - Calculate cash to close and monthly carry costs."""

from decimal import Decimal

import streamlit as st

from bc_real_estate import BuyerCalculator, HoldingCosts, MortgageDetails, PropertyDetails, RentalIncome


def render() -> None:
    """Render the buyer assessment tab."""
    st.header("💰 Buyer Assessment: Cash to Close")
    st.markdown("Calculate your total cash required to close and monthly carrying costs.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Property Details")
        purchase_price = st.number_input(
            "Purchase Price ($)",
            min_value=100000,
            max_value=10000000,
            value=800000,
            step=10000,
            help="Total purchase price of the property",
        )

        down_payment = st.number_input(
            "Down Payment ($)",
            min_value=5000,
            max_value=int(purchase_price),
            value=int(purchase_price * 0.2),
            step=5000,
            help="Cash down payment (minimum 5%-20% depending on price)",
        )

        is_first_time = st.checkbox(
            "First-Time Home Buyer",
            value=False,
            help="Qualify for first-time buyer PTT exemption (up to $500k)",
        )

        is_newly_built = st.checkbox(
            "Newly Built Property",
            value=False,
            help="Qualify for newly built PTT exemption (up to $1.1M)",
        )

        st.subheader("Mortgage Details")
        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=5.5,
            step=0.1,
            format="%.2f",
            help="Annual mortgage interest rate",
        )

        amortization = st.selectbox(
            "Amortization Period",
            options=[20, 25, 30],
            index=1,
            help="Mortgage amortization period in years",
        )

    with col2:
        st.subheader("Holding Costs")
        property_tax = st.number_input(
            "Annual Property Tax ($)",
            min_value=0,
            max_value=100000,
            value=3600,
            step=100,
            help="Annual property tax (before homeowner grant)",
        )

        strata_fee = st.number_input(
            "Monthly Strata Fee ($)",
            min_value=0,
            max_value=5000,
            value=300,
            step=50,
            help="Monthly strata/HOA fee",
        )

        insurance = st.number_input(
            "Annual Insurance ($)",
            min_value=0,
            max_value=10000,
            value=1200,
            step=100,
            help="Annual homeowner insurance premium",
        )

        utilities = st.number_input(
            "Monthly Utilities ($)",
            min_value=0,
            max_value=2000,
            value=150,
            step=50,
            help="Monthly utilities cost",
        )

        st.subheader("Rental Income (Optional)")
        include_rental = st.checkbox("Include Rental Income", value=False)

        if include_rental:
            monthly_rent = st.number_input(
                "Monthly Rent ($)",
                min_value=0,
                max_value=20000,
                value=3000,
                step=100,
                help="Expected monthly rental income",
            )

            vacancy_rate = st.number_input(
                "Vacancy Rate (%)",
                min_value=0.0,
                max_value=50.0,
                value=5.0,
                step=1.0,
                format="%.1f",
                help="Expected vacancy rate per year",
            )
        else:
            monthly_rent = 0
            vacancy_rate = 0

        include_inspection = st.checkbox("Include Home Inspection ($600)", value=True)

    # Calculate button
    if st.button("Calculate Buyer Costs", type="primary", use_container_width=True):
        try:
            # Create models
            property_details = PropertyDetails(
                purchase_price=Decimal(str(purchase_price)),
                is_newly_built=is_newly_built,
                is_first_time_buyer=is_first_time,
            )

            mortgage_details = MortgageDetails(
                down_payment=Decimal(str(down_payment)),
                interest_rate=Decimal(str(interest_rate)),
                amortization_years=amortization,
            )

            holding_costs = HoldingCosts(
                property_tax_annual=Decimal(str(property_tax)),
                strata_fee_monthly=Decimal(str(strata_fee)),
                insurance_annual=Decimal(str(insurance)),
                utilities_monthly=Decimal(str(utilities)),
            )

            rental_income = None
            if include_rental:
                rental_income = RentalIncome(
                    monthly_rent=Decimal(str(monthly_rent)),
                    vacancy_rate=Decimal(str(vacancy_rate)),
                )

            # Calculate
            calculator = BuyerCalculator()
            results = calculator.calculate_all(
                property_details,
                mortgage_details,
                holding_costs,
                rental_income,
                include_inspection,
            )

            # Store in session state for comparison tab
            st.session_state.buyer_results = results
            st.session_state.buyer_inputs = {
                "purchase_price": purchase_price,
                "down_payment": down_payment,
            }

            # Display results
            st.success("✅ Calculation Complete!")

            # Cash to Close
            st.subheader("💵 Cash to Close Breakdown")
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.metric("Down Payment", f"${results.down_payment:,.2f}")

            with col_b:
                ptt_label = "PTT (after exemption)" if results.ptt_exemption > 0 else "Property Transfer Tax"
                st.metric(ptt_label, f"${results.ptt_amount:,.2f}")
                if results.ptt_exemption > 0:
                    st.caption(f"✅ Exemption: ${results.ptt_exemption:,.2f}")

            with col_c:
                st.metric("Closing Costs", f"${results.closing_costs:,.2f}")

            st.divider()
            st.metric(
                "**Total Cash to Close**",
                f"${results.total_cash_to_close:,.2f}",
                help="Total cash required to complete purchase",
            )

            # Monthly Carry Costs
            st.subheader("📆 Monthly Carry Costs")
            col_d, col_e, col_f = st.columns(3)

            with col_d:
                st.metric("Mortgage P&I", f"${results.monthly_mortgage_payment:,.2f}")
                st.metric("Property Tax", f"${results.monthly_property_tax:,.2f}")
                if results.homeowner_grant_applied:
                    st.caption("✅ Homeowner grant applied")

            with col_e:
                st.metric("Strata Fee", f"${results.monthly_strata_fee:,.2f}")
                st.metric("Insurance", f"${results.monthly_insurance:,.2f}")

            with col_f:
                st.metric("Utilities", f"${results.monthly_utilities:,.2f}")
                if results.monthly_rental_income > 0:
                    st.metric(
                        "Rental Income",
                        f"${results.monthly_rental_income:,.2f}",
                        delta="Income",
                        delta_color="normal",
                    )

            st.divider()
            col_g, col_h = st.columns(2)

            with col_g:
                st.metric(
                    "**Total Monthly Carry**",
                    f"${results.total_monthly_carry_costs:,.2f}",
                    help="Total monthly carrying costs",
                )

            with col_h:
                net_flow_color = "normal" if results.net_monthly_cash_flow >= 0 else "inverse"
                st.metric(
                    "**Net Monthly Cash Flow**",
                    f"${results.net_monthly_cash_flow:,.2f}",
                    delta="Positive" if results.net_monthly_cash_flow >= 0 else "Negative",
                    delta_color=net_flow_color,
                    help="Monthly income minus monthly costs",
                )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    render()
