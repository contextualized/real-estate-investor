"""Seller exit cost calculations."""

from decimal import Decimal

from bc_real_estate.config import get_config
from bc_real_estate.models import SaleDetails, SellerResults


class SellerCalculator:
    """Calculate seller exit costs and net proceeds."""

    def __init__(self) -> None:
        """Initialize calculator with configuration."""
        self.config = get_config()

    def calculate_realtor_commission(self, sale_price: Decimal) -> Decimal:
        """Calculate realtor commission using BC tiered structure.

        7% on first $100k, 2.5% on remainder.

        Args:
            sale_price: Property sale price

        Returns:
            Total realtor commission
        """
        commission = Decimal("0")
        remaining = sale_price
        previous_threshold = Decimal("0")

        for threshold, rate in self.config.realtor_commission_structure:
            if remaining <= 0:
                break

            taxable_amount = min(remaining, threshold - previous_threshold)
            commission += taxable_amount * rate
            remaining -= taxable_amount
            previous_threshold = threshold

        return commission.quantize(Decimal("0.01"))

    def calculate_capital_gain(
        self,
        sale_price: Decimal,
        adjusted_cost_base: Decimal,
        is_principal_residence: bool,
        capital_gains_inclusion_rate: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Calculate capital gain and taxable portion.

        Args:
            sale_price: Property sale price
            adjusted_cost_base: ACB (purchase price + acquisition costs + improvements)
            is_principal_residence: Whether PRE applies
            capital_gains_inclusion_rate: Inclusion rate (0.50 or 0.6667)

        Returns:
            Tuple of (capital_gain, taxable_capital_gain)
        """
        capital_gain = sale_price - adjusted_cost_base

        if is_principal_residence:
            # Principal Residence Exemption - no taxable gain
            taxable_gain = Decimal("0")
        else:
            # Apply inclusion rate
            if capital_gain > 0:
                taxable_gain = capital_gain * capital_gains_inclusion_rate
            else:
                # Capital loss
                taxable_gain = Decimal("0")

        return capital_gain.quantize(Decimal("0.01")), taxable_gain.quantize(Decimal("0.01"))

    def calculate_capital_gains_tax(
        self,
        taxable_capital_gain: Decimal,
        marginal_tax_rate: Decimal,
    ) -> Decimal:
        """Calculate capital gains tax.

        Args:
            taxable_capital_gain: Taxable portion of capital gain
            marginal_tax_rate: Marginal tax rate (as percentage)

        Returns:
            Capital gains tax amount
        """
        tax = taxable_capital_gain * (marginal_tax_rate / Decimal("100"))
        return tax.quantize(Decimal("0.01"))

    def calculate_all(
        self,
        sale_details: SaleDetails,
        acquisition_costs: Decimal,
        capital_gains_inclusion_rate: Decimal | None = None,
    ) -> SellerResults:
        """Calculate all seller costs and returns comprehensive results.

        Args:
            sale_details: Property sale details
            acquisition_costs: Total acquisition costs (down payment + PTT + closing)
            capital_gains_inclusion_rate: Override default inclusion rate

        Returns:
            SellerResults with all calculated values
        """
        # Use default inclusion rate if not provided
        if capital_gains_inclusion_rate is None:
            capital_gains_inclusion_rate = self.config.capital_gains_inclusion

        # Realtor commission
        commission = self.calculate_realtor_commission(sale_details.sale_price)

        # Legal fees
        legal_fees = self.config.legal_fees_sale

        # Adjusted cost base (ACB)
        adjusted_cost_base = acquisition_costs + sale_details.capital_improvements

        # Capital gain
        capital_gain, taxable_capital_gain = self.calculate_capital_gain(
            sale_details.sale_price,
            adjusted_cost_base,
            sale_details.is_principal_residence,
            capital_gains_inclusion_rate,
        )

        # Capital gains tax
        capital_gains_tax = self.calculate_capital_gains_tax(
            taxable_capital_gain,
            sale_details.marginal_tax_rate,
        )

        # Net proceeds
        gross_proceeds = sale_details.sale_price
        net_proceeds = (
            gross_proceeds - commission - legal_fees - capital_gains_tax
        )

        return SellerResults(
            gross_proceeds=gross_proceeds,
            realtor_commission=commission,
            legal_fees=legal_fees,
            adjusted_cost_base=adjusted_cost_base,
            capital_gain=capital_gain,
            taxable_capital_gain=taxable_capital_gain,
            capital_gains_tax=capital_gains_tax,
            net_proceeds=net_proceeds,
            principal_residence_exemption_applied=sale_details.is_principal_residence,
        )
