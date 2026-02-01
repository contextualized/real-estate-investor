"""Buyer acquisition cost calculations."""

from decimal import Decimal
from typing import Optional

from bc_real_estate.config import get_config
from bc_real_estate.models import (
    BuyerResults,
    HoldingCosts,
    MortgageDetails,
    PropertyDetails,
    RentalIncome,
)
from bc_real_estate.utils import (
    apply_homeowner_grant,
    calculate_mortgage_payment,
)


class BuyerCalculator:
    """Calculate buyer acquisition costs and monthly carrying costs."""

    def __init__(self) -> None:
        """Initialize calculator with configuration."""
        self.config = get_config()

    def calculate_ptt(self, property_details: PropertyDetails) -> tuple[Decimal, Decimal]:
        """Calculate Property Transfer Tax with applicable exemptions.

        Args:
            property_details: Property acquisition details

        Returns:
            Tuple of (ptt_amount, ptt_exemption)
        """
        price = property_details.purchase_price

        # Calculate base PTT using tiered structure
        base_ptt = self._calculate_base_ptt(price)

        # Calculate applicable exemptions
        exemption = Decimal("0")

        if property_details.is_first_time_buyer:
            first_time_exemption = self._calculate_first_time_buyer_exemption(price)
            exemption = max(exemption, first_time_exemption)

        if property_details.is_newly_built:
            newly_built_exemption = self._calculate_newly_built_exemption(price)
            exemption = max(exemption, newly_built_exemption)

        ptt_amount = max(Decimal("0"), base_ptt - exemption)

        return ptt_amount, exemption

    def _calculate_base_ptt(self, price: Decimal) -> Decimal:
        """Calculate base PTT using BC tiered structure."""
        ptt = Decimal("0")
        remaining = price
        previous_threshold = Decimal("0")

        for threshold, rate in self.config.ptt_tiers:
            if remaining <= 0:
                break

            taxable_amount = min(remaining, threshold - previous_threshold)
            ptt += taxable_amount * rate
            remaining -= taxable_amount
            previous_threshold = threshold

        # Apply luxury rate to amount above $3M
        if remaining > 0:
            ptt += remaining * self.config.ptt_luxury_rate

        return ptt.quantize(Decimal("0.01"))

    def _calculate_first_time_buyer_exemption(self, price: Decimal) -> Decimal:
        """Calculate first-time home buyer PTT exemption.

        Full exemption if price <= $500k
        Partial exemption ($8,000) if $500k < price <= $835k
        Phase-out between $835k-$860k
        """
        if price <= self.config.first_time_buyer_full_exemption_threshold:
            # Full exemption - return the full PTT amount
            return self._calculate_base_ptt(price)

        if price <= self.config.first_time_buyer_partial_exemption_threshold:
            # Partial exemption of $8,000
            return self.config.first_time_buyer_partial_exemption_amount

        if price <= self.config.first_time_buyer_phase_out_end:
            # Phase-out zone: linear reduction from $8,000 to $0
            phase_out_range = (
                self.config.first_time_buyer_phase_out_end
                - self.config.first_time_buyer_phase_out_start
            )
            price_into_phase_out = price - self.config.first_time_buyer_phase_out_start

            # Linear interpolation
            reduction_factor = Decimal("1") - (price_into_phase_out / phase_out_range)
            exemption = self.config.first_time_buyer_partial_exemption_amount * reduction_factor

            return exemption.quantize(Decimal("0.01"))

        # No exemption above phase-out end
        return Decimal("0")

    def _calculate_newly_built_exemption(self, price: Decimal) -> Decimal:
        """Calculate newly built home PTT exemption.

        Full exemption if price <= $1.1M
        Phase-out between $1.1M-$1.15M
        """
        if price <= self.config.newly_built_full_exemption_threshold:
            # Full exemption
            return self._calculate_base_ptt(price)

        if price <= self.config.newly_built_phase_out_end:
            # Phase-out zone: linear reduction from full PTT to $0
            full_ptt = self._calculate_base_ptt(price)
            phase_out_range = (
                self.config.newly_built_phase_out_end
                - self.config.newly_built_phase_out_start
            )
            price_into_phase_out = price - self.config.newly_built_phase_out_start

            # Linear interpolation
            reduction_factor = Decimal("1") - (price_into_phase_out / phase_out_range)
            exemption = full_ptt * reduction_factor

            return exemption.quantize(Decimal("0.01"))

        # No exemption above phase-out end
        return Decimal("0")

    def calculate_closing_costs(self, include_inspection: bool = True) -> Decimal:
        """Calculate closing costs.

        Args:
            include_inspection: Whether to include home inspection cost

        Returns:
            Total closing costs
        """
        costs = (
            self.config.legal_fees
            + self.config.title_insurance
            + self.config.appraisal_fee
        )

        if include_inspection:
            costs += self.config.home_inspection

        return costs

    def calculate_monthly_carry_costs(
        self,
        mortgage_details: MortgageDetails,
        holding_costs: HoldingCosts,
        purchase_price: Decimal,
    ) -> tuple[Decimal, Decimal, bool]:
        """Calculate total monthly carrying costs.

        Args:
            mortgage_details: Mortgage financing details
            holding_costs: Annual and monthly holding costs
            purchase_price: Property purchase price (for homeowner grant)

        Returns:
            Tuple of (total_monthly_carry, monthly_mortgage_payment, grant_applied)
        """
        # Calculate mortgage principal
        mortgage_principal = purchase_price - mortgage_details.down_payment

        # Calculate monthly mortgage payment
        monthly_mortgage = calculate_mortgage_payment(
            principal=mortgage_principal,
            annual_rate=mortgage_details.interest_rate,
            amortization_years=mortgage_details.amortization_years,
            frequency="monthly",
        )

        # Apply homeowner grant to property tax
        monthly_property_tax_before_grant = holding_costs.property_tax_annual / Decimal("12")
        annual_property_tax_after_grant, grant_applied = apply_homeowner_grant(
            holding_costs.property_tax_annual,
            purchase_price,  # Use purchase price as assessed value proxy
        )
        monthly_property_tax = annual_property_tax_after_grant / Decimal("12")

        # Calculate monthly insurance
        monthly_insurance = holding_costs.insurance_annual / Decimal("12")

        # Total monthly carry
        total_monthly_carry = (
            monthly_mortgage
            + monthly_property_tax
            + holding_costs.strata_fee_monthly
            + monthly_insurance
            + holding_costs.utilities_monthly
        )

        return (
            total_monthly_carry.quantize(Decimal("0.01")),
            monthly_mortgage.quantize(Decimal("0.01")),
            grant_applied,
        )

    def calculate_net_cash_flow(
        self,
        monthly_carry_costs: Decimal,
        rental_income: Optional[RentalIncome],
    ) -> Decimal:
        """Calculate net monthly cash flow.

        Args:
            monthly_carry_costs: Total monthly carrying costs
            rental_income: Optional rental income details

        Returns:
            Net monthly cash flow (positive if income exceeds costs)
        """
        if rental_income is None:
            return -monthly_carry_costs

        # Adjust for vacancy
        effective_rent = rental_income.monthly_rent * (
            Decimal("1") - rental_income.vacancy_rate / Decimal("100")
        )

        net_flow = effective_rent - monthly_carry_costs

        return net_flow.quantize(Decimal("0.01"))

    def calculate_all(
        self,
        property_details: PropertyDetails,
        mortgage_details: MortgageDetails,
        holding_costs: HoldingCosts,
        rental_income: Optional[RentalIncome] = None,
        include_inspection: bool = True,
    ) -> BuyerResults:
        """Calculate all buyer costs and returns comprehensive results.

        Args:
            property_details: Property acquisition details
            mortgage_details: Mortgage financing details
            holding_costs: Annual and monthly holding costs
            rental_income: Optional rental income details
            include_inspection: Whether to include home inspection in closing costs

        Returns:
            BuyerResults with all calculated values
        """
        # PTT calculation
        ptt_amount, ptt_exemption = self.calculate_ptt(property_details)

        # Closing costs
        closing_costs = self.calculate_closing_costs(include_inspection)

        # Cash to close
        total_cash_to_close = (
            mortgage_details.down_payment + ptt_amount + closing_costs
        )

        # Monthly carry costs
        (
            total_monthly_carry,
            monthly_mortgage_payment,
            grant_applied,
        ) = self.calculate_monthly_carry_costs(
            mortgage_details, holding_costs, property_details.purchase_price
        )

        # Net cash flow
        net_monthly_cash_flow = self.calculate_net_cash_flow(
            total_monthly_carry, rental_income
        )

        # Calculate individual monthly costs for detailed breakdown
        annual_property_tax_after_grant, _ = apply_homeowner_grant(
            holding_costs.property_tax_annual,
            property_details.purchase_price,
        )
        monthly_property_tax = (annual_property_tax_after_grant / Decimal("12")).quantize(
            Decimal("0.01")
        )
        monthly_insurance = (holding_costs.insurance_annual / Decimal("12")).quantize(
            Decimal("0.01")
        )

        # Monthly rental income
        monthly_rental_income = Decimal("0")
        if rental_income is not None:
            monthly_rental_income = (
                rental_income.monthly_rent
                * (Decimal("1") - rental_income.vacancy_rate / Decimal("100"))
            ).quantize(Decimal("0.01"))

        return BuyerResults(
            down_payment=mortgage_details.down_payment,
            ptt_amount=ptt_amount,
            ptt_exemption=ptt_exemption,
            closing_costs=closing_costs,
            total_cash_to_close=total_cash_to_close,
            mortgage_amount=property_details.purchase_price - mortgage_details.down_payment,
            monthly_mortgage_payment=monthly_mortgage_payment,
            monthly_property_tax=monthly_property_tax,
            monthly_strata_fee=holding_costs.strata_fee_monthly,
            monthly_insurance=monthly_insurance,
            monthly_utilities=holding_costs.utilities_monthly,
            total_monthly_carry_costs=total_monthly_carry,
            monthly_rental_income=monthly_rental_income,
            net_monthly_cash_flow=net_monthly_cash_flow,
            homeowner_grant_applied=grant_applied,
        )
