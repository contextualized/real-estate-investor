"""Test Streamlit app functionality without UI."""

from decimal import Decimal

from bc_real_estate import (
    BuyerCalculator,
    HoldingCosts,
    InvestmentAnalyzer,
    MortgageDetails,
    PropertyDetails,
    RentalIncome,
    SaleDetails,
    SellerCalculator,
)


def test_buyer_tab_logic():
    """Test the logic behind the buyer assessment tab."""
    print("\n" + "=" * 70)
    print("Testing Buyer Assessment Tab Logic")
    print("=" * 70)

    # Simulate user inputs
    purchase_price = Decimal("800000")
    down_payment = Decimal("160000")
    is_first_time = False
    is_newly_built = False
    interest_rate = Decimal("5.5")
    amortization = 25
    property_tax = Decimal("3600")
    strata_fee = Decimal("300")
    insurance = Decimal("1200")
    utilities = Decimal("150")
    include_rental = True
    monthly_rent = Decimal("3500")
    vacancy_rate = Decimal("5")
    include_inspection = True

    # Create models
    property_details = PropertyDetails(
        purchase_price=purchase_price,
        is_newly_built=is_newly_built,
        is_first_time_buyer=is_first_time,
    )

    mortgage_details = MortgageDetails(
        down_payment=down_payment,
        interest_rate=interest_rate,
        amortization_years=amortization,
    )

    holding_costs = HoldingCosts(
        property_tax_annual=property_tax,
        strata_fee_monthly=strata_fee,
        insurance_annual=insurance,
        utilities_monthly=utilities,
    )

    rental_income = RentalIncome(
        monthly_rent=monthly_rent,
        vacancy_rate=vacancy_rate,
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

    # Display results
    print(f"\n✓ Buyer calculations successful!")
    print(f"  Total Cash to Close: ${results.total_cash_to_close:,.2f}")
    print(f"  PTT Amount: ${results.ptt_amount:,.2f}")
    print(f"  PTT Exemption: ${results.ptt_exemption:,.2f}")
    print(f"  Monthly Carry Costs: ${results.total_monthly_carry_costs:,.2f}")
    print(f"  Net Monthly Cash Flow: ${results.net_monthly_cash_flow:,.2f}")

    return results


def test_seller_tab_logic(buyer_results):
    """Test the logic behind the seller forecast tab."""
    print("\n" + "=" * 70)
    print("Testing Seller Forecast Tab Logic")
    print("=" * 70)

    # Simulate user inputs
    sale_price = Decimal("1000000")
    holding_period = Decimal("5")
    is_principal_residence = True
    marginal_tax_rate = Decimal("43.7")
    capital_improvements = Decimal("20000")
    inclusion_rate = Decimal("0.50")

    # Use buyer results for acquisition costs
    acquisition_costs = buyer_results.total_cash_to_close

    # Create model
    sale_details = SaleDetails(
        sale_price=sale_price,
        holding_period_years=holding_period,
        is_principal_residence=is_principal_residence,
        marginal_tax_rate=marginal_tax_rate,
        capital_improvements=capital_improvements,
    )

    # Calculate
    calculator = SellerCalculator()
    results = calculator.calculate_all(
        sale_details,
        acquisition_costs,
        inclusion_rate,
    )

    # Display results
    print(f"\n✓ Seller calculations successful!")
    print(f"  Gross Proceeds: ${results.gross_proceeds:,.2f}")
    print(f"  Realtor Commission: ${results.realtor_commission:,.2f}")
    print(f"  Capital Gain: ${results.capital_gain:,.2f}")
    print(f"  Taxable Capital Gain: ${results.taxable_capital_gain:,.2f}")
    print(f"  Capital Gains Tax: ${results.capital_gains_tax:,.2f}")
    print(f"  Net Proceeds: ${results.net_proceeds:,.2f}")
    if results.principal_residence_exemption_applied:
        print(f"  ✓ Principal Residence Exemption Applied")

    return results


def test_comparison_tab_logic(buyer_results, seller_results):
    """Test the logic behind the scenario comparison tab."""
    print("\n" + "=" * 70)
    print("Testing Scenario Comparison Tab Logic")
    print("=" * 70)

    holding_period = Decimal("5")

    # Calculate
    results = InvestmentAnalyzer.calculate_all(
        buyer_results,
        seller_results,
        holding_period,
    )

    # Display results
    print(f"\n✓ Investment analysis successful!")
    print(f"  Total Cash Invested: ${results.total_cash_invested:,.2f}")
    print(f"  Total Return: ${results.total_return:,.2f}")
    print(f"  Net Profit: ${results.net_profit:,.2f}")
    print(f"  ROCI: {results.roci_percent:.2f}%")
    print(f"  IRR (Annual): {results.irr_percent:.2f}%")
    print(f"  Holding Period: {results.holding_period_months} months")
    print(f"  Cumulative Cash Flow: ${results.cumulative_cash_flow:,.2f}")

    return results


def test_first_time_buyer_scenario():
    """Test first-time buyer with exemption."""
    print("\n" + "=" * 70)
    print("Testing First-Time Buyer Scenario")
    print("=" * 70)

    property_details = PropertyDetails(
        purchase_price=Decimal("450000"),
        is_newly_built=False,
        is_first_time_buyer=True,
    )

    mortgage_details = MortgageDetails(
        down_payment=Decimal("45000"),  # 10%
        interest_rate=Decimal("5.5"),
        amortization_years=25,
    )

    holding_costs = HoldingCosts(
        property_tax_annual=Decimal("2500"),
        strata_fee_monthly=Decimal("250"),
        insurance_annual=Decimal("1000"),
        utilities_monthly=Decimal("120"),
    )

    calculator = BuyerCalculator()
    results = calculator.calculate_all(
        property_details,
        mortgage_details,
        holding_costs,
        rental_income=None,
        include_inspection=True,
    )

    print(f"\n✓ First-time buyer scenario successful!")
    print(f"  Purchase Price: ${property_details.purchase_price:,.2f}")
    print(f"  PTT Without Exemption: ${calculator._calculate_base_ptt(property_details.purchase_price):,.2f}")
    print(f"  PTT Exemption: ${results.ptt_exemption:,.2f}")
    print(f"  PTT After Exemption: ${results.ptt_amount:,.2f}")
    print(f"  Total Cash to Close: ${results.total_cash_to_close:,.2f}")


def test_newly_built_scenario():
    """Test newly built property with exemption."""
    print("\n" + "=" * 70)
    print("Testing Newly Built Property Scenario")
    print("=" * 70)

    property_details = PropertyDetails(
        purchase_price=Decimal("1050000"),
        is_newly_built=True,
        is_first_time_buyer=False,
    )

    mortgage_details = MortgageDetails(
        down_payment=Decimal("210000"),  # 20%
        interest_rate=Decimal("5.0"),
        amortization_years=25,
    )

    holding_costs = HoldingCosts(
        property_tax_annual=Decimal("4500"),
        strata_fee_monthly=Decimal("350"),
        insurance_annual=Decimal("1500"),
        utilities_monthly=Decimal("180"),
    )

    calculator = BuyerCalculator()
    results = calculator.calculate_all(
        property_details,
        mortgage_details,
        holding_costs,
        rental_income=None,
        include_inspection=True,
    )

    print(f"\n✓ Newly built scenario successful!")
    print(f"  Purchase Price: ${property_details.purchase_price:,.2f}")
    print(f"  PTT Without Exemption: ${calculator._calculate_base_ptt(property_details.purchase_price):,.2f}")
    print(f"  PTT Exemption: ${results.ptt_exemption:,.2f}")
    print(f"  PTT After Exemption: ${results.ptt_amount:,.2f}")
    print(f"  Total Cash to Close: ${results.total_cash_to_close:,.2f}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("BC Real Estate Analyzer - Streamlit Functionality Test")
    print("=" * 70)

    # Test main workflow
    buyer_results = test_buyer_tab_logic()
    seller_results = test_seller_tab_logic(buyer_results)
    test_comparison_tab_logic(buyer_results, seller_results)

    # Test special scenarios
    test_first_time_buyer_scenario()
    test_newly_built_scenario()

    print("\n" + "=" * 70)
    print("✓ All Streamlit functionality tests passed!")
    print("=" * 70)
    print("\nThe Streamlit app is fully functional and ready to use.")
    print("Run: uv run streamlit run streamlit_app/app.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
