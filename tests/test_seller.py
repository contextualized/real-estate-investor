"""Tests for seller exit calculations."""

from decimal import Decimal

import pytest

from bc_real_estate.config import Config
from bc_real_estate.models import SaleDetails
from bc_real_estate.seller import SellerCalculator


@pytest.fixture
def calculator(config: Config) -> SellerCalculator:
    """Seller calculator instance."""
    return SellerCalculator()


class TestRealtorCommission:
    """Test realtor commission calculations."""

    @pytest.mark.parametrize(
        "sale_price,expected_commission",
        [
            (Decimal("100000"), Decimal("7000.00")),  # 7% on $100k
            (Decimal("200000"), Decimal("9500.00")),  # $7k + 2.5% on $100k
            (Decimal("500000"), Decimal("17000.00")),  # $7k + 2.5% on $400k
            (Decimal("1000000"), Decimal("29500.00")),  # $7k + 2.5% on $900k
            (Decimal("50000"), Decimal("3500.00")),  # 7% on $50k
        ],
    )
    def test_commission_tiers(
        self, calculator: SellerCalculator, sale_price: Decimal, expected_commission: Decimal
    ) -> None:
        """Test commission calculation at various price points."""
        commission = calculator.calculate_realtor_commission(sale_price)
        assert commission == expected_commission

    def test_commission_at_100k_boundary(self, calculator: SellerCalculator) -> None:
        """Test commission at $100k boundary."""
        commission = calculator.calculate_realtor_commission(Decimal("100000"))
        # 7% on $100k = $7,000
        assert commission == Decimal("7000.00")

    def test_commission_above_100k(self, calculator: SellerCalculator) -> None:
        """Test commission just above $100k."""
        commission = calculator.calculate_realtor_commission(Decimal("100001"))
        # $7k + 2.5% on $1 = $7,000.025 rounded to $7,000.02
        assert commission == Decimal("7000.02")


class TestCapitalGain:
    """Test capital gain calculations."""

    def test_capital_gain_with_profit(self, calculator: SellerCalculator) -> None:
        """Test capital gain calculation with profit."""
        sale_price = Decimal("1000000")
        adjusted_cost_base = Decimal("800000")
        inclusion_rate = Decimal("0.50")

        capital_gain, taxable_gain = calculator.calculate_capital_gain(
            sale_price,
            adjusted_cost_base,
            is_principal_residence=False,
            capital_gains_inclusion_rate=inclusion_rate,
        )

        # Capital gain: $1M - $800k = $200k
        assert capital_gain == Decimal("200000.00")
        # Taxable gain: $200k * 0.50 = $100k
        assert taxable_gain == Decimal("100000.00")

    def test_capital_gain_with_principal_residence(self, calculator: SellerCalculator) -> None:
        """Test capital gain with principal residence exemption."""
        sale_price = Decimal("1000000")
        adjusted_cost_base = Decimal("800000")
        inclusion_rate = Decimal("0.50")

        capital_gain, taxable_gain = calculator.calculate_capital_gain(
            sale_price,
            adjusted_cost_base,
            is_principal_residence=True,
            capital_gains_inclusion_rate=inclusion_rate,
        )

        # Capital gain: $1M - $800k = $200k
        assert capital_gain == Decimal("200000.00")
        # Taxable gain: $0 (PRE applied)
        assert taxable_gain == Decimal("0.00")

    def test_capital_gain_with_loss(self, calculator: SellerCalculator) -> None:
        """Test capital gain calculation with loss."""
        sale_price = Decimal("700000")
        adjusted_cost_base = Decimal("800000")
        inclusion_rate = Decimal("0.50")

        capital_gain, taxable_gain = calculator.calculate_capital_gain(
            sale_price,
            adjusted_cost_base,
            is_principal_residence=False,
            capital_gains_inclusion_rate=inclusion_rate,
        )

        # Capital gain: $700k - $800k = -$100k
        assert capital_gain == Decimal("-100000.00")
        # Taxable gain: $0 (capital loss)
        assert taxable_gain == Decimal("0.00")

    def test_capital_gain_high_inclusion_rate(self, calculator: SellerCalculator) -> None:
        """Test capital gain with 66.67% inclusion rate."""
        sale_price = Decimal("1000000")
        adjusted_cost_base = Decimal("700000")
        inclusion_rate = Decimal("0.6667")

        capital_gain, taxable_gain = calculator.calculate_capital_gain(
            sale_price,
            adjusted_cost_base,
            is_principal_residence=False,
            capital_gains_inclusion_rate=inclusion_rate,
        )

        # Capital gain: $1M - $700k = $300k
        assert capital_gain == Decimal("300000.00")
        # Taxable gain: $300k * 0.6667 = $200,010
        assert taxable_gain == Decimal("200010.00")


class TestCapitalGainsTax:
    """Test capital gains tax calculations."""

    def test_capital_gains_tax(self, calculator: SellerCalculator) -> None:
        """Test capital gains tax calculation."""
        taxable_gain = Decimal("100000")
        marginal_rate = Decimal("43.7")

        tax = calculator.calculate_capital_gains_tax(taxable_gain, marginal_rate)

        # Tax: $100k * 43.7% = $43,700
        assert tax == Decimal("43700.00")

    def test_capital_gains_tax_zero_gain(self, calculator: SellerCalculator) -> None:
        """Test capital gains tax with zero taxable gain."""
        taxable_gain = Decimal("0")
        marginal_rate = Decimal("43.7")

        tax = calculator.calculate_capital_gains_tax(taxable_gain, marginal_rate)

        assert tax == Decimal("0.00")

    def test_capital_gains_tax_different_rate(self, calculator: SellerCalculator) -> None:
        """Test capital gains tax with different marginal rate."""
        taxable_gain = Decimal("50000")
        marginal_rate = Decimal("30.0")

        tax = calculator.calculate_capital_gains_tax(taxable_gain, marginal_rate)

        # Tax: $50k * 30% = $15,000
        assert tax == Decimal("15000.00")


class TestCalculateAll:
    """Test comprehensive seller calculations."""

    def test_full_calculation_no_pre(self, calculator: SellerCalculator) -> None:
        """Test complete seller calculation without PRE."""
        sale_details = SaleDetails(
            sale_price=Decimal("1000000"),
            holding_period_years=Decimal("5"),
            is_principal_residence=False,
            marginal_tax_rate=Decimal("43.7"),
            capital_improvements=Decimal("20000"),
        )
        acquisition_costs = Decimal("177050")  # From buyer example

        results = calculator.calculate_all(
            sale_details,
            acquisition_costs,
            capital_gains_inclusion_rate=Decimal("0.50"),
        )

        # Commission: $7k + $22.5k = $29.5k
        assert results.realtor_commission == Decimal("29500.00")

        # Legal fees
        assert results.legal_fees == Decimal("1500")

        # ACB: $177,050 + $20,000 = $197,050
        assert results.adjusted_cost_base == Decimal("197050")

        # Capital gain: $1M - $197,050 = $802,950
        assert results.capital_gain == Decimal("802950.00")

        # Taxable gain: $802,950 * 0.50 = $401,475
        assert results.taxable_capital_gain == Decimal("401475.00")

        # Tax: $401,475 * 43.7% = $175,444.58
        assert results.capital_gains_tax == Decimal("175444.58")

        # PRE not applied
        assert results.principal_residence_exemption_applied is False

        # Net proceeds: $1M - $29.5k - $1.5k - $175,444.58 = $793,555.42
        assert results.net_proceeds == Decimal("793555.42")

    def test_full_calculation_with_pre(self, calculator: SellerCalculator) -> None:
        """Test complete seller calculation with PRE."""
        sale_details = SaleDetails(
            sale_price=Decimal("1000000"),
            holding_period_years=Decimal("5"),
            is_principal_residence=True,
            marginal_tax_rate=Decimal("43.7"),
            capital_improvements=Decimal("0"),
        )
        acquisition_costs = Decimal("177050")

        results = calculator.calculate_all(
            sale_details,
            acquisition_costs,
            capital_gains_inclusion_rate=Decimal("0.50"),
        )

        # Commission: $29.5k
        assert results.realtor_commission == Decimal("29500.00")

        # Legal fees
        assert results.legal_fees == Decimal("1500")

        # ACB: $177,050
        assert results.adjusted_cost_base == Decimal("177050")

        # Capital gain: $1M - $177,050 = $822,950
        assert results.capital_gain == Decimal("822950.00")

        # Taxable gain: $0 (PRE)
        assert results.taxable_capital_gain == Decimal("0.00")

        # Tax: $0 (PRE)
        assert results.capital_gains_tax == Decimal("0.00")

        # PRE applied
        assert results.principal_residence_exemption_applied is True

        # Net proceeds: $1M - $29.5k - $1.5k = $969,000
        assert results.net_proceeds == Decimal("969000.00")

    def test_full_calculation_with_loss(self, calculator: SellerCalculator) -> None:
        """Test complete seller calculation with capital loss."""
        sale_details = SaleDetails(
            sale_price=Decimal("700000"),
            holding_period_years=Decimal("3"),
            is_principal_residence=False,
            marginal_tax_rate=Decimal("43.7"),
            capital_improvements=Decimal("0"),
        )
        acquisition_costs = Decimal("800000")

        results = calculator.calculate_all(
            sale_details,
            acquisition_costs,
            capital_gains_inclusion_rate=Decimal("0.50"),
        )

        # Commission: $7k + $15k = $22k
        assert results.realtor_commission == Decimal("22000.00")

        # Capital gain: $700k - $800k = -$100k
        assert results.capital_gain == Decimal("-100000.00")

        # Taxable gain: $0 (loss)
        assert results.taxable_capital_gain == Decimal("0.00")

        # Tax: $0 (loss)
        assert results.capital_gains_tax == Decimal("0.00")

        # Net proceeds: $700k - $22k - $1.5k = $676.5k
        assert results.net_proceeds == Decimal("676500.00")

    def test_default_inclusion_rate(self, calculator: SellerCalculator) -> None:
        """Test that default inclusion rate is used when not specified."""
        sale_details = SaleDetails(
            sale_price=Decimal("1000000"),
            holding_period_years=Decimal("5"),
            is_principal_residence=False,
            marginal_tax_rate=Decimal("43.7"),
            capital_improvements=Decimal("0"),
        )
        acquisition_costs = Decimal("800000")

        results = calculator.calculate_all(
            sale_details,
            acquisition_costs,
            # capital_gains_inclusion_rate not specified - should use default 0.50
        )

        # Capital gain: $1M - $800k = $200k
        # Taxable gain with default 50%: $100k
        assert results.taxable_capital_gain == Decimal("100000.00")

    def test_high_inclusion_rate(self, calculator: SellerCalculator) -> None:
        """Test with high inclusion rate."""
        sale_details = SaleDetails(
            sale_price=Decimal("1000000"),
            holding_period_years=Decimal("5"),
            is_principal_residence=False,
            marginal_tax_rate=Decimal("43.7"),
            capital_improvements=Decimal("0"),
        )
        acquisition_costs = Decimal("800000")

        results = calculator.calculate_all(
            sale_details,
            acquisition_costs,
            capital_gains_inclusion_rate=Decimal("0.6667"),
        )

        # Capital gain: $200k
        # Taxable gain with 66.67%: $133,340
        assert results.taxable_capital_gain == Decimal("133340.00")
