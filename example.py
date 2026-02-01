#!/usr/bin/env python3
"""Example usage of BC Real Estate Investment Analyzer."""

from decimal import Decimal

from bc_real_estate import (
    BuyerCalculator,
    ComparisonResults,
    HoldingCosts,
    InvestmentAnalyzer,
    MortgageDetails,
    PropertyDetails,
    RentalIncome,
    SaleDetails,
    SellerCalculator,
)


def main() -> None:
    """Run example investment analysis."""
    print("=" * 70)
    print("BC Real Estate Investment Analyzer - Example")
    print("=" * 70)

    # Buyer Assessment
    print("\n💰 BUYER ASSESSMENT\n")
    print("Property: $800,000 purchase, 20% down, 5.5% interest")

    property_details = PropertyDetails(
        purchase_price=Decimal("800000"),
        is_first_time_buyer=False,
        is_newly_built=False,
    )

    mortgage_details = MortgageDetails(
        down_payment=Decimal("160000"),  # 20%
        interest_rate=Decimal("5.5"),
        amortization_years=25,
    )

    holding_costs = HoldingCosts(
        property_tax_annual=Decimal("3600"),
        strata_fee_monthly=Decimal("300"),
        insurance_annual=Decimal("1200"),
        utilities_monthly=Decimal("150"),
    )

    rental_income = RentalIncome(
        monthly_rent=Decimal("3500"),
        vacancy_rate=Decimal("5"),
    )

    buyer_calc = BuyerCalculator()
    buyer_results = buyer_calc.calculate_all(
        property_details,
        mortgage_details,
        holding_costs,
        rental_income,
        include_inspection=True,
    )

    print(f"  Down Payment:           ${buyer_results.down_payment:,.2f}")
    print(f"  Property Transfer Tax:  ${buyer_results.ptt_amount:,.2f}")
    print(f"  Closing Costs:          ${buyer_results.closing_costs:,.2f}")
    print(f"  ─────────────────────────────────────")
    print(f"  TOTAL CASH TO CLOSE:    ${buyer_results.total_cash_to_close:,.2f}")
    print()
    print(f"  Monthly Mortgage (P&I): ${buyer_results.monthly_mortgage_payment:,.2f}")
    print(f"  Monthly Carry Costs:    ${buyer_results.total_monthly_carry_costs:,.2f}")
    print(f"  Monthly Rental Income:  ${buyer_results.monthly_rental_income:,.2f}")
    print(f"  ─────────────────────────────────────")
    print(f"  NET MONTHLY CASH FLOW:  ${buyer_results.net_monthly_cash_flow:,.2f}")

    # Seller Forecast
    print("\n\n📈 SELLER FORECAST\n")
    print("Sale: $1,000,000 after 5 years (Principal Residence)")

    sale_details = SaleDetails(
        sale_price=Decimal("1000000"),
        holding_period_years=Decimal("5"),
        is_principal_residence=True,  # No capital gains tax
        marginal_tax_rate=Decimal("43.7"),
        capital_improvements=Decimal("20000"),
    )

    seller_calc = SellerCalculator()
    seller_results = seller_calc.calculate_all(
        sale_details,
        buyer_results.total_cash_to_close,  # Acquisition costs
        capital_gains_inclusion_rate=Decimal("0.50"),
    )

    print(f"  Sale Price:             ${seller_results.gross_proceeds:,.2f}")
    print(f"  Realtor Commission:     -${seller_results.realtor_commission:,.2f}")
    print(f"  Legal Fees:             -${seller_results.legal_fees:,.2f}")
    print(f"  Capital Gains Tax:      -${seller_results.capital_gains_tax:,.2f}")
    if seller_results.principal_residence_exemption_applied:
        print(f"    (PRE Applied ✓)")
    print(f"  ─────────────────────────────────────")
    print(f"  NET PROCEEDS:           ${seller_results.net_proceeds:,.2f}")

    # Investment Analysis
    print("\n\n📊 INVESTMENT ANALYSIS\n")

    comparison_results = InvestmentAnalyzer.calculate_all(
        buyer_results,
        seller_results,
        Decimal("5"),  # 5 years
    )

    print(f"  Total Cash Invested:    ${comparison_results.total_cash_invested:,.2f}")
    print(f"  Total Return:           ${comparison_results.total_return:,.2f}")
    print(f"  Net Profit:             ${comparison_results.net_profit:,.2f}")
    print(f"  ─────────────────────────────────────")
    print(f"  ROCI:                   {comparison_results.roci_percent:.2f}%")
    print(f"  IRR (Annual):           {comparison_results.irr_percent:.2f}%")

    print("\n" + "=" * 70)
    print("✓ Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
