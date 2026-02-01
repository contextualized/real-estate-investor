"""Pytest fixtures for BC Real Estate tests."""

from decimal import Decimal
from pathlib import Path

import pytest

from bc_real_estate.config import Config
from bc_real_estate.models import (
    HoldingCosts,
    MortgageDetails,
    PropertyDetails,
    RentalIncome,
    SaleDetails,
)


@pytest.fixture
def test_config_path() -> Path:
    """Path to test configuration file."""
    return Path(__file__).parent / "fixtures" / "test_config.toml"


@pytest.fixture
def config(test_config_path: Path) -> Config:
    """Load test configuration."""
    # Reset singleton for testing
    Config._instance = None
    return Config(test_config_path)


@pytest.fixture
def property_details() -> PropertyDetails:
    """Sample property details."""
    return PropertyDetails(
        purchase_price=Decimal("800000"),
        is_newly_built=False,
        is_first_time_buyer=False,
    )


@pytest.fixture
def property_details_first_time_buyer() -> PropertyDetails:
    """Property details for first-time buyer."""
    return PropertyDetails(
        purchase_price=Decimal("700000"),
        is_newly_built=False,
        is_first_time_buyer=True,
    )


@pytest.fixture
def property_details_newly_built() -> PropertyDetails:
    """Property details for newly built home."""
    return PropertyDetails(
        purchase_price=Decimal("1050000"),
        is_newly_built=True,
        is_first_time_buyer=False,
    )


@pytest.fixture
def mortgage_details() -> MortgageDetails:
    """Sample mortgage details."""
    return MortgageDetails(
        down_payment=Decimal("160000"),  # 20%
        interest_rate=Decimal("5.5"),
        amortization_years=25,
    )


@pytest.fixture
def holding_costs() -> HoldingCosts:
    """Sample holding costs."""
    return HoldingCosts(
        property_tax_annual=Decimal("3600"),
        strata_fee_monthly=Decimal("300"),
        insurance_annual=Decimal("1200"),
        utilities_monthly=Decimal("150"),
    )


@pytest.fixture
def rental_income() -> RentalIncome:
    """Sample rental income."""
    return RentalIncome(
        monthly_rent=Decimal("3000"),
        vacancy_rate=Decimal("5"),
    )


@pytest.fixture
def sale_details() -> SaleDetails:
    """Sample sale details."""
    return SaleDetails(
        sale_price=Decimal("1000000"),
        holding_period_years=Decimal("5"),
        is_principal_residence=False,
        marginal_tax_rate=Decimal("43.7"),
        capital_improvements=Decimal("0"),
    )


@pytest.fixture
def sale_details_principal_residence() -> SaleDetails:
    """Sale details with principal residence exemption."""
    return SaleDetails(
        sale_price=Decimal("1000000"),
        holding_period_years=Decimal("5"),
        is_principal_residence=True,
        marginal_tax_rate=Decimal("43.7"),
        capital_improvements=Decimal("0"),
    )
