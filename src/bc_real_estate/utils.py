"""Utility functions for mortgage calculations and formatting."""

from decimal import Decimal
from typing import Literal

from bc_real_estate.config import get_config


def calculate_mortgage_payment(
    principal: Decimal,
    annual_rate: Decimal,
    amortization_years: int,
    frequency: Literal["monthly", "biweekly", "weekly"] = "monthly",
) -> Decimal:
    """Calculate mortgage payment using standard amortization formula.

    Args:
        principal: Mortgage principal amount
        annual_rate: Annual interest rate (as percentage, e.g., 5.5 for 5.5%)
        amortization_years: Amortization period in years
        frequency: Payment frequency (monthly, biweekly, or weekly)

    Returns:
        Payment amount per frequency period
    """
    if principal <= 0:
        return Decimal("0")

    if annual_rate == 0:
        # No interest - simple division
        if frequency == "monthly":
            return principal / Decimal(amortization_years * 12)
        elif frequency == "biweekly":
            return principal / Decimal(amortization_years * 26)
        else:  # weekly
            return principal / Decimal(amortization_years * 52)

    # Convert annual rate to decimal (e.g., 5.5% -> 0.055)
    annual_rate_decimal = annual_rate / Decimal("100")

    # Calculate periodic rate and number of payments based on frequency
    if frequency == "monthly":
        periodic_rate = annual_rate_decimal / Decimal("12")
        num_payments = amortization_years * 12
    elif frequency == "biweekly":
        periodic_rate = annual_rate_decimal / Decimal("26")
        num_payments = amortization_years * 26
    else:  # weekly
        periodic_rate = annual_rate_decimal / Decimal("52")
        num_payments = amortization_years * 52

    # Standard mortgage payment formula: P * [r(1+r)^n] / [(1+r)^n - 1]
    one_plus_rate = Decimal("1") + periodic_rate
    power_term = one_plus_rate ** num_payments

    payment = principal * (periodic_rate * power_term) / (power_term - Decimal("1"))

    return payment.quantize(Decimal("0.01"))


def apply_homeowner_grant(
    annual_property_tax: Decimal,
    assessed_value: Decimal,
) -> tuple[Decimal, bool]:
    """Apply BC homeowner grant if eligible.

    Args:
        annual_property_tax: Annual property tax amount
        assessed_value: Property assessed value

    Returns:
        Tuple of (adjusted_tax, grant_applied)
    """
    config = get_config()

    if assessed_value < config.homeowner_grant_threshold:
        adjusted_tax = max(
            Decimal("0"), annual_property_tax - config.homeowner_grant_amount
        )
        return adjusted_tax, True

    return annual_property_tax, False


def validate_mortgage_down_payment(
    purchase_price: Decimal,
    down_payment: Decimal,
) -> tuple[bool, str]:
    """Validate down payment meets CMHC requirements.

    Args:
        purchase_price: Property purchase price
        down_payment: Proposed down payment

    Returns:
        Tuple of (is_valid, error_message)
    """
    if down_payment <= 0:
        return False, "Down payment must be greater than $0"

    if down_payment >= purchase_price:
        return False, "Down payment cannot be greater than or equal to purchase price"

    down_payment_percent = (down_payment / purchase_price) * Decimal("100")

    # CMHC minimum down payment rules
    if purchase_price <= Decimal("500000"):
        min_down_payment_percent = Decimal("5")
    elif purchase_price <= Decimal("1000000"):
        # 5% on first $500k, 10% on remainder
        min_down_500k = Decimal("500000") * Decimal("0.05")
        min_down_remainder = (purchase_price - Decimal("500000")) * Decimal("0.10")
        min_down_payment = min_down_500k + min_down_remainder
        min_down_payment_percent = (min_down_payment / purchase_price) * Decimal("100")
    else:
        # Properties over $1M require 20% down
        min_down_payment_percent = Decimal("20")

    if down_payment_percent < min_down_payment_percent:
        return False, (
            f"Down payment must be at least {min_down_payment_percent:.1f}% "
            f"for a property priced at ${purchase_price:,.2f}"
        )

    return True, ""


def format_currency(amount: Decimal, include_cents: bool = True) -> str:
    """Format a Decimal amount as currency.

    Args:
        amount: Amount to format
        include_cents: Whether to include cents in output

    Returns:
        Formatted currency string (e.g., "$1,234.56" or "$1,234")
    """
    if include_cents:
        return f"${amount:,.2f}"
    else:
        return f"${amount:,.0f}"


def format_percentage(rate: Decimal, decimals: int = 2) -> str:
    """Format a Decimal rate as percentage.

    Args:
        rate: Rate to format (e.g., 5.5 for 5.5%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string (e.g., "5.50%")
    """
    format_str = f"{{:.{decimals}f}}%"
    return format_str.format(rate)
