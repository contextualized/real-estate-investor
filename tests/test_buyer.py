"""Tests for buyer acquisition calculations."""

from decimal import Decimal

import pytest

from bc_real_estate.buyer import BuyerCalculator
from bc_real_estate.config import Config
from bc_real_estate.models import (
    HoldingCosts,
    MortgageDetails,
    PropertyDetails,
    RentalIncome,
)


@pytest.fixture
def calculator(config: Config) -> BuyerCalculator:
    """Buyer calculator instance."""
    return BuyerCalculator()


class TestPTTCalculation:
    """Test Property Transfer Tax calculations."""

    @pytest.mark.parametrize(
        "price,expected_ptt",
        [
            (Decimal("150000"), Decimal("1500.00")),  # 1% on first $200k
            (Decimal("200000"), Decimal("2000.00")),  # Boundary at $200k
            (Decimal("500000"), Decimal("8000.00")),  # $2k + $6k
            (Decimal("1500000"), Decimal("28000.00")),  # $2k + $26k
            (Decimal("2000000"), Decimal("38000.00")),  # $2k + $36k
            (Decimal("2500000"), Decimal("53000.00")),  # $2k + $36k + $15k
            (Decimal("3000000"), Decimal("68000.00")),  # $2k + $36k + $30k
            (Decimal("3500000"), Decimal("93000.00")),  # $2k + $36k + $30k + $25k (5%)
        ],
    )
    def test_base_ptt_tiers(
        self, calculator: BuyerCalculator, price: Decimal, expected_ptt: Decimal
    ) -> None:
        """Test PTT calculation at various price points."""
        property_details = PropertyDetails(
            purchase_price=price,
            is_newly_built=False,
            is_first_time_buyer=False,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        assert ptt_amount == expected_ptt
        assert ptt_exemption == Decimal("0")

    def test_ptt_tier_boundary_200k(self, calculator: BuyerCalculator) -> None:
        """Test PTT at $200k boundary."""
        property_details = PropertyDetails(
            purchase_price=Decimal("200000"),
            is_newly_built=False,
            is_first_time_buyer=False,
        )

        ptt_amount, _ = calculator.calculate_ptt(property_details)

        # 1% on $200k = $2,000
        assert ptt_amount == Decimal("2000.00")

    def test_ptt_tier_boundary_2m(self, calculator: BuyerCalculator) -> None:
        """Test PTT at $2M boundary."""
        property_details = PropertyDetails(
            purchase_price=Decimal("2000000"),
            is_newly_built=False,
            is_first_time_buyer=False,
        )

        ptt_amount, _ = calculator.calculate_ptt(property_details)

        # 1% on $200k + 2% on $1.8M = $2k + $36k = $38k
        assert ptt_amount == Decimal("38000.00")

    def test_ptt_tier_boundary_3m(self, calculator: BuyerCalculator) -> None:
        """Test PTT at $3M boundary."""
        property_details = PropertyDetails(
            purchase_price=Decimal("3000000"),
            is_newly_built=False,
            is_first_time_buyer=False,
        )

        ptt_amount, _ = calculator.calculate_ptt(property_details)

        # 1% on $200k + 2% on $1.8M + 3% on $1M = $2k + $36k + $30k = $68k
        assert ptt_amount == Decimal("68000.00")


class TestFirstTimeBuyerExemption:
    """Test first-time home buyer PTT exemption."""

    def test_full_exemption_below_500k(self, calculator: BuyerCalculator) -> None:
        """Test full exemption for price below $500k."""
        property_details = PropertyDetails(
            purchase_price=Decimal("450000"),
            is_newly_built=False,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # Full exemption - PTT should be $0
        assert ptt_amount == Decimal("0.00")
        # Exemption should equal the base PTT
        # Base PTT: 1% on $200k + 2% on $250k = $2k + $5k = $7k
        expected_base_ptt = Decimal("7000.00")
        assert ptt_exemption == expected_base_ptt

    def test_full_exemption_at_500k(self, calculator: BuyerCalculator) -> None:
        """Test full exemption at exactly $500k."""
        property_details = PropertyDetails(
            purchase_price=Decimal("500000"),
            is_newly_built=False,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        assert ptt_amount == Decimal("0.00")
        assert ptt_exemption == Decimal("8000.00")

    def test_partial_exemption_at_700k(self, calculator: BuyerCalculator) -> None:
        """Test partial exemption of $8,000 for price between $500k-$835k."""
        property_details = PropertyDetails(
            purchase_price=Decimal("700000"),
            is_newly_built=False,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # Base PTT: $2k + ($700k - $200k) * 2% = $2k + $10k = $12k
        # Exemption: $8,000
        # Net PTT: $12k - $8k = $4k
        assert ptt_exemption == Decimal("8000.00")
        assert ptt_amount == Decimal("4000.00")

    def test_partial_exemption_at_835k(self, calculator: BuyerCalculator) -> None:
        """Test partial exemption at phase-out start ($835k)."""
        property_details = PropertyDetails(
            purchase_price=Decimal("835000"),
            is_newly_built=False,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # At phase-out start, still get full $8,000
        assert ptt_exemption == Decimal("8000.00")

    def test_phase_out_at_850k(self, calculator: BuyerCalculator) -> None:
        """Test exemption phase-out at $850k (midpoint of $835k-$860k)."""
        property_details = PropertyDetails(
            purchase_price=Decimal("847500"),  # Midpoint
            is_newly_built=False,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # At midpoint, exemption should be ~$4,000
        # Phase-out range: $835k to $860k = $25k
        # Price into phase-out: $847.5k - $835k = $12.5k (50%)
        # Exemption: $8,000 * (1 - 0.5) = $4,000
        assert ptt_exemption == Decimal("4000.00")

    def test_no_exemption_above_860k(self, calculator: BuyerCalculator) -> None:
        """Test no exemption above $860k."""
        property_details = PropertyDetails(
            purchase_price=Decimal("900000"),
            is_newly_built=False,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # No exemption
        assert ptt_exemption == Decimal("0.00")
        # Base PTT: $2k + $14k = $16k
        assert ptt_amount == Decimal("16000.00")


class TestNewlyBuiltExemption:
    """Test newly built home PTT exemption."""

    def test_full_exemption_below_1_1m(self, calculator: BuyerCalculator) -> None:
        """Test full exemption for newly built below $1.1M."""
        property_details = PropertyDetails(
            purchase_price=Decimal("1000000"),
            is_newly_built=True,
            is_first_time_buyer=False,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # Full exemption
        assert ptt_amount == Decimal("0.00")
        # Exemption equals base PTT: $2k + $16k = $18k
        assert ptt_exemption == Decimal("18000.00")

    def test_full_exemption_at_1_1m(self, calculator: BuyerCalculator) -> None:
        """Test full exemption at exactly $1.1M."""
        property_details = PropertyDetails(
            purchase_price=Decimal("1100000"),
            is_newly_built=True,
            is_first_time_buyer=False,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        assert ptt_amount == Decimal("0.00")
        # Base PTT: $2k + $18k = $20k
        assert ptt_exemption == Decimal("20000.00")

    def test_phase_out_at_1_125m(self, calculator: BuyerCalculator) -> None:
        """Test exemption phase-out at $1.125M (midpoint of $1.1M-$1.15M)."""
        property_details = PropertyDetails(
            purchase_price=Decimal("1125000"),
            is_newly_built=True,
            is_first_time_buyer=False,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # Phase-out range: $1.1M to $1.15M = $50k
        # Price into phase-out: $1.125M - $1.1M = $25k (50%)
        # Base PTT at $1.125M: $2k + $18.5k = $20.5k
        # Exemption: $20.5k * (1 - 0.5) = $10.25k
        expected_exemption = Decimal("10250.00")
        assert ptt_exemption == expected_exemption

    def test_no_exemption_above_1_15m(self, calculator: BuyerCalculator) -> None:
        """Test no exemption above $1.15M."""
        property_details = PropertyDetails(
            purchase_price=Decimal("1200000"),
            is_newly_built=True,
            is_first_time_buyer=False,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # No exemption
        assert ptt_exemption == Decimal("0.00")
        # Base PTT: $2k + $20k = $22k
        assert ptt_amount == Decimal("22000.00")


class TestCombinedExemptions:
    """Test that only maximum exemption applies (not cumulative)."""

    def test_both_exemptions_apply_max(self, calculator: BuyerCalculator) -> None:
        """Test that maximum exemption applies when both qualify."""
        # At $450k, first-time buyer gets full exemption of $7k
        # Newly built also gets full exemption of $7k
        # Should apply max (both are same in this case)
        property_details = PropertyDetails(
            purchase_price=Decimal("450000"),
            is_newly_built=True,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # Should get full exemption (PTT = $0)
        assert ptt_amount == Decimal("0.00")
        # Exemption equals base PTT: $2k + $5k = $7k
        expected_base_ptt = Decimal("7000.00")
        assert ptt_exemption == expected_base_ptt

    def test_newly_built_exemption_higher(self, calculator: BuyerCalculator) -> None:
        """Test that newly built exemption is used when higher."""
        # At $1M, first-time buyer gets no exemption
        # Newly built gets full exemption of $18k
        property_details = PropertyDetails(
            purchase_price=Decimal("1000000"),
            is_newly_built=True,
            is_first_time_buyer=True,
        )

        ptt_amount, ptt_exemption = calculator.calculate_ptt(property_details)

        # Should use newly built exemption
        assert ptt_amount == Decimal("0.00")
        assert ptt_exemption == Decimal("18000.00")


class TestClosingCosts:
    """Test closing costs calculation."""

    def test_closing_costs_with_inspection(self, calculator: BuyerCalculator) -> None:
        """Test closing costs including home inspection."""
        costs = calculator.calculate_closing_costs(include_inspection=True)

        # $1,750 + $300 + $400 + $600 = $3,050
        assert costs == Decimal("3050")

    def test_closing_costs_without_inspection(self, calculator: BuyerCalculator) -> None:
        """Test closing costs without home inspection."""
        costs = calculator.calculate_closing_costs(include_inspection=False)

        # $1,750 + $300 + $400 = $2,450
        assert costs == Decimal("2450")


class TestMortgagePayment:
    """Test monthly mortgage payment calculations."""

    def test_monthly_payment_calculation(self, calculator: BuyerCalculator) -> None:
        """Test monthly mortgage payment."""
        property_details = PropertyDetails(
            purchase_price=Decimal("800000"),
            is_newly_built=False,
            is_first_time_buyer=False,
        )
        mortgage_details = MortgageDetails(
            down_payment=Decimal("160000"),
            interest_rate=Decimal("5.5"),
            amortization_years=25,
        )
        holding_costs = HoldingCosts(
            property_tax_annual=Decimal("3600"),
            strata_fee_monthly=Decimal("300"),
            insurance_annual=Decimal("1200"),
            utilities_monthly=Decimal("150"),
        )

        total_monthly, monthly_mortgage, _ = calculator.calculate_monthly_carry_costs(
            mortgage_details, holding_costs, property_details.purchase_price
        )

        # Mortgage principal: $800k - $160k = $640k
        # At 5.5% over 25 years, monthly payment should be ~$3,900
        assert monthly_mortgage > Decimal("3800")
        assert monthly_mortgage < Decimal("4000")

    def test_zero_interest_mortgage(self, calculator: BuyerCalculator) -> None:
        """Test mortgage calculation with zero interest."""
        property_details = PropertyDetails(
            purchase_price=Decimal("600000"),
            is_newly_built=False,
            is_first_time_buyer=False,
        )
        mortgage_details = MortgageDetails(
            down_payment=Decimal("120000"),
            interest_rate=Decimal("0"),
            amortization_years=25,
        )
        holding_costs = HoldingCosts(
            property_tax_annual=Decimal("3000"),
            strata_fee_monthly=Decimal("200"),
            insurance_annual=Decimal("1000"),
            utilities_monthly=Decimal("100"),
        )

        _, monthly_mortgage, _ = calculator.calculate_monthly_carry_costs(
            mortgage_details, holding_costs, property_details.purchase_price
        )

        # Simple division: $480k / (25 * 12) = $1,600
        expected_payment = Decimal("480000") / Decimal("300")
        assert monthly_mortgage == expected_payment.quantize(Decimal("0.01"))


class TestHomeownerGrant:
    """Test BC homeowner grant application."""

    def test_grant_applied_below_threshold(self, calculator: BuyerCalculator) -> None:
        """Test homeowner grant applied when below threshold."""
        property_details = PropertyDetails(
            purchase_price=Decimal("1000000"),  # Below $2.075M
            is_newly_built=False,
            is_first_time_buyer=False,
        )
        mortgage_details = MortgageDetails(
            down_payment=Decimal("200000"),
            interest_rate=Decimal("5.0"),
            amortization_years=25,
        )
        holding_costs = HoldingCosts(
            property_tax_annual=Decimal("6840"),  # $570 * 12 = $6,840
            strata_fee_monthly=Decimal("0"),
            insurance_annual=Decimal("0"),
            utilities_monthly=Decimal("0"),
        )

        _, _, grant_applied = calculator.calculate_monthly_carry_costs(
            mortgage_details, holding_costs, property_details.purchase_price
        )

        assert grant_applied is True

    def test_grant_not_applied_above_threshold(self, calculator: BuyerCalculator) -> None:
        """Test homeowner grant not applied when above threshold."""
        property_details = PropertyDetails(
            purchase_price=Decimal("2500000"),  # Above $2.075M
            is_newly_built=False,
            is_first_time_buyer=False,
        )
        mortgage_details = MortgageDetails(
            down_payment=Decimal("500000"),
            interest_rate=Decimal("5.0"),
            amortization_years=25,
        )
        holding_costs = HoldingCosts(
            property_tax_annual=Decimal("10000"),
            strata_fee_monthly=Decimal("0"),
            insurance_annual=Decimal("0"),
            utilities_monthly=Decimal("0"),
        )

        _, _, grant_applied = calculator.calculate_monthly_carry_costs(
            mortgage_details, holding_costs, property_details.purchase_price
        )

        assert grant_applied is False


class TestNetCashFlow:
    """Test net cash flow calculations."""

    def test_negative_cash_flow_no_rental(self, calculator: BuyerCalculator) -> None:
        """Test negative cash flow with no rental income."""
        monthly_carry = Decimal("4000")
        net_flow = calculator.calculate_net_cash_flow(monthly_carry, None)

        assert net_flow == Decimal("-4000.00")

    def test_positive_cash_flow_with_rental(self, calculator: BuyerCalculator) -> None:
        """Test positive cash flow with rental income."""
        monthly_carry = Decimal("3000")
        rental_income = RentalIncome(
            monthly_rent=Decimal("3500"),
            vacancy_rate=Decimal("5"),
        )

        net_flow = calculator.calculate_net_cash_flow(monthly_carry, rental_income)

        # Effective rent: $3,500 * 0.95 = $3,325
        # Net flow: $3,325 - $3,000 = $325
        assert net_flow == Decimal("325.00")

    def test_negative_cash_flow_with_rental(self, calculator: BuyerCalculator) -> None:
        """Test negative cash flow even with rental income."""
        monthly_carry = Decimal("4000")
        rental_income = RentalIncome(
            monthly_rent=Decimal("3000"),
            vacancy_rate=Decimal("10"),
        )

        net_flow = calculator.calculate_net_cash_flow(monthly_carry, rental_income)

        # Effective rent: $3,000 * 0.90 = $2,700
        # Net flow: $2,700 - $4,000 = -$1,300
        assert net_flow == Decimal("-1300.00")


class TestCalculateAll:
    """Test comprehensive buyer calculations."""

    def test_full_calculation(self, calculator: BuyerCalculator) -> None:
        """Test complete buyer calculation flow."""
        property_details = PropertyDetails(
            purchase_price=Decimal("800000"),
            is_newly_built=False,
            is_first_time_buyer=False,
        )
        mortgage_details = MortgageDetails(
            down_payment=Decimal("160000"),
            interest_rate=Decimal("5.5"),
            amortization_years=25,
        )
        holding_costs = HoldingCosts(
            property_tax_annual=Decimal("3600"),
            strata_fee_monthly=Decimal("300"),
            insurance_annual=Decimal("1200"),
            utilities_monthly=Decimal("150"),
        )

        results = calculator.calculate_all(
            property_details,
            mortgage_details,
            holding_costs,
            rental_income=None,
            include_inspection=True,
        )

        # Verify all results are calculated
        assert results.down_payment == Decimal("160000")
        assert results.ptt_amount == Decimal("14000.00")
        assert results.ptt_exemption == Decimal("0.00")
        assert results.closing_costs == Decimal("3050")
        assert results.total_cash_to_close == Decimal("177050")
        assert results.mortgage_amount == Decimal("640000")
        assert results.monthly_mortgage_payment > Decimal("0")
        assert results.total_monthly_carry_costs > Decimal("0")
        assert results.net_monthly_cash_flow < Decimal("0")

    def test_full_calculation_with_rental(self, calculator: BuyerCalculator) -> None:
        """Test complete buyer calculation with rental income."""
        property_details = PropertyDetails(
            purchase_price=Decimal("800000"),
            is_newly_built=False,
            is_first_time_buyer=False,
        )
        mortgage_details = MortgageDetails(
            down_payment=Decimal("160000"),
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

        results = calculator.calculate_all(
            property_details,
            mortgage_details,
            holding_costs,
            rental_income=rental_income,
            include_inspection=True,
        )

        # Verify rental income calculations
        assert results.monthly_rental_income == Decimal("3325.00")  # $3,500 * 0.95
        # Net cash flow might still be negative depending on total carry costs
        assert results.net_monthly_cash_flow != Decimal("0")
