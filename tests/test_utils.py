"""Tests for utility functions."""

from decimal import Decimal

import pytest

from bc_real_estate.config import Config
from bc_real_estate.utils import (
    apply_homeowner_grant,
    calculate_mortgage_payment,
    format_currency,
    format_percentage,
    validate_mortgage_down_payment,
)


class TestMortgagePayment:
    """Test mortgage payment calculations."""

    def test_monthly_payment(self) -> None:
        """Test standard monthly payment calculation."""
        principal = Decimal("500000")
        annual_rate = Decimal("5.0")
        amortization_years = 25

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="monthly"
        )

        # Should be around $2,900-$3,000/month
        assert payment > Decimal("2900")
        assert payment < Decimal("3000")

    def test_biweekly_payment(self) -> None:
        """Test biweekly payment calculation."""
        principal = Decimal("500000")
        annual_rate = Decimal("5.0")
        amortization_years = 25

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="biweekly"
        )

        # Biweekly should be roughly half of monthly
        monthly_payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="monthly"
        )
        assert payment < monthly_payment
        assert payment > Decimal("1300")

    def test_weekly_payment(self) -> None:
        """Test weekly payment calculation."""
        principal = Decimal("500000")
        annual_rate = Decimal("5.0")
        amortization_years = 25

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="weekly"
        )

        # Weekly should be roughly 1/4 of monthly
        assert payment > Decimal("600")
        assert payment < Decimal("700")

    def test_zero_interest(self) -> None:
        """Test mortgage payment with 0% interest."""
        principal = Decimal("600000")
        annual_rate = Decimal("0")
        amortization_years = 25

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="monthly"
        )

        # Simple division: $600k / (25 * 12) = $2,000
        expected = Decimal("600000") / Decimal("300")
        assert payment == expected

    def test_zero_interest_biweekly(self) -> None:
        """Test biweekly mortgage payment with 0% interest."""
        principal = Decimal("650000")
        annual_rate = Decimal("0")
        amortization_years = 25

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="biweekly"
        )

        # Simple division: $650k / (25 * 26)
        expected = Decimal("650000") / Decimal("650")
        assert payment == expected

    def test_zero_interest_weekly(self) -> None:
        """Test weekly mortgage payment with 0% interest."""
        principal = Decimal("520000")
        annual_rate = Decimal("0")
        amortization_years = 20

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="weekly"
        )

        # Simple division: $520k / (20 * 52)
        expected = Decimal("520000") / Decimal("1040")
        assert payment == expected

    def test_zero_principal(self) -> None:
        """Test mortgage payment with $0 principal."""
        principal = Decimal("0")
        annual_rate = Decimal("5.0")
        amortization_years = 25

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="monthly"
        )

        assert payment == Decimal("0")

    def test_negative_principal(self) -> None:
        """Test mortgage payment with negative principal (edge case)."""
        principal = Decimal("-100000")
        annual_rate = Decimal("5.0")
        amortization_years = 25

        payment = calculate_mortgage_payment(
            principal, annual_rate, amortization_years, frequency="monthly"
        )

        assert payment == Decimal("0")


class TestHomeownerGrant:
    """Test homeowner grant application."""

    def test_grant_applied_below_threshold(self, config: Config) -> None:
        """Test grant applied when below threshold."""
        annual_tax = Decimal("5000")
        assessed_value = Decimal("1000000")  # Below $2.075M

        adjusted_tax, grant_applied = apply_homeowner_grant(annual_tax, assessed_value)

        assert grant_applied is True
        assert adjusted_tax == Decimal("4430")  # $5,000 - $570

    def test_grant_not_applied_above_threshold(self, config: Config) -> None:
        """Test grant not applied when above threshold."""
        annual_tax = Decimal("10000")
        assessed_value = Decimal("3000000")  # Above $2.075M

        adjusted_tax, grant_applied = apply_homeowner_grant(annual_tax, assessed_value)

        assert grant_applied is False
        assert adjusted_tax == Decimal("10000")

    def test_grant_reduces_to_zero(self, config: Config) -> None:
        """Test grant doesn't create negative tax."""
        annual_tax = Decimal("400")  # Less than grant amount
        assessed_value = Decimal("1000000")

        adjusted_tax, grant_applied = apply_homeowner_grant(annual_tax, assessed_value)

        assert grant_applied is True
        assert adjusted_tax == Decimal("0")  # Can't go negative


class TestValidateDownPayment:
    """Test down payment validation."""

    def test_valid_20_percent_down(self) -> None:
        """Test valid 20% down payment."""
        purchase_price = Decimal("500000")
        down_payment = Decimal("100000")  # 20%

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is True
        assert error == ""

    def test_valid_5_percent_down_under_500k(self) -> None:
        """Test valid 5% down payment for property under $500k."""
        purchase_price = Decimal("400000")
        down_payment = Decimal("20000")  # 5%

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is True
        assert error == ""

    def test_invalid_too_low_under_500k(self) -> None:
        """Test invalid down payment below 5% for property under $500k."""
        purchase_price = Decimal("400000")
        down_payment = Decimal("15000")  # 3.75%

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is False
        assert "5.0%" in error

    def test_valid_hybrid_500k_to_1m(self) -> None:
        """Test valid down payment for property $500k-$1M."""
        purchase_price = Decimal("700000")
        # Required: 5% on first $500k + 10% on $200k = $25k + $20k = $45k
        down_payment = Decimal("45000")

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is True
        assert error == ""

    def test_invalid_hybrid_500k_to_1m(self) -> None:
        """Test invalid down payment for property $500k-$1M."""
        purchase_price = Decimal("700000")
        down_payment = Decimal("40000")  # Below required $45k

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is False
        assert error != ""

    def test_valid_20_percent_over_1m(self) -> None:
        """Test valid 20% down payment for property over $1M."""
        purchase_price = Decimal("1500000")
        down_payment = Decimal("300000")  # 20%

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is True
        assert error == ""

    def test_invalid_below_20_percent_over_1m(self) -> None:
        """Test invalid down payment below 20% for property over $1M."""
        purchase_price = Decimal("1500000")
        down_payment = Decimal("250000")  # 16.67%

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is False
        assert "20.0%" in error

    def test_zero_down_payment(self) -> None:
        """Test zero down payment."""
        purchase_price = Decimal("500000")
        down_payment = Decimal("0")

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is False
        assert "must be greater than $0" in error

    def test_down_payment_exceeds_price(self) -> None:
        """Test down payment greater than purchase price."""
        purchase_price = Decimal("500000")
        down_payment = Decimal("600000")

        is_valid, error = validate_mortgage_down_payment(purchase_price, down_payment)

        assert is_valid is False
        assert "cannot be greater than or equal to" in error


class TestFormatCurrency:
    """Test currency formatting."""

    def test_format_with_cents(self) -> None:
        """Test currency formatting with cents."""
        amount = Decimal("1234.56")
        formatted = format_currency(amount, include_cents=True)
        assert formatted == "$1,234.56"

    def test_format_without_cents(self) -> None:
        """Test currency formatting without cents."""
        amount = Decimal("1234.56")
        formatted = format_currency(amount, include_cents=False)
        assert formatted == "$1,235"

    def test_format_large_amount(self) -> None:
        """Test formatting large amounts."""
        amount = Decimal("1234567.89")
        formatted = format_currency(amount, include_cents=True)
        assert formatted == "$1,234,567.89"

    def test_format_zero(self) -> None:
        """Test formatting zero."""
        amount = Decimal("0")
        formatted = format_currency(amount, include_cents=True)
        assert formatted == "$0.00"


class TestFormatPercentage:
    """Test percentage formatting."""

    def test_format_default_decimals(self) -> None:
        """Test percentage formatting with default 2 decimals."""
        rate = Decimal("5.5")
        formatted = format_percentage(rate)
        assert formatted == "5.50%"

    def test_format_one_decimal(self) -> None:
        """Test percentage formatting with 1 decimal."""
        rate = Decimal("5.54")  # Rounds to 5.5
        formatted = format_percentage(rate, decimals=1)
        assert formatted == "5.5%"

    def test_format_zero_decimals(self) -> None:
        """Test percentage formatting with 0 decimals."""
        rate = Decimal("5.55")
        formatted = format_percentage(rate, decimals=0)
        assert formatted == "6%"

    def test_format_high_precision(self) -> None:
        """Test percentage formatting with high precision."""
        rate = Decimal("5.12344")  # Rounds to 5.1234
        formatted = format_percentage(rate, decimals=4)
        assert formatted == "5.1234%"
