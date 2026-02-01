"""Pydantic models for input validation and result structures."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PropertyDetails(BaseModel):
    """Property acquisition details."""

    purchase_price: Decimal = Field(gt=0, description="Property purchase price")
    is_newly_built: bool = Field(default=False, description="Is this a newly built property")
    is_first_time_buyer: bool = Field(
        default=False, description="Is this a first-time home buyer"
    )

    @field_validator("purchase_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | Decimal | int | str) -> Decimal:
        """Convert input to Decimal for precision."""
        return Decimal(str(v))


class MortgageDetails(BaseModel):
    """Mortgage financing details."""

    down_payment: Decimal = Field(gt=0, description="Down payment amount")
    interest_rate: Decimal = Field(ge=0, le=100, description="Annual interest rate (%)")
    amortization_years: int = Field(gt=0, le=30, description="Amortization period in years")

    @field_validator("down_payment", "interest_rate", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | Decimal | int | str) -> Decimal:
        """Convert input to Decimal for precision."""
        return Decimal(str(v))


class HoldingCosts(BaseModel):
    """Annual and monthly holding costs."""

    property_tax_annual: Decimal = Field(ge=0, description="Annual property tax")
    strata_fee_monthly: Decimal = Field(ge=0, description="Monthly strata fee")
    insurance_annual: Decimal = Field(ge=0, description="Annual insurance premium")
    utilities_monthly: Decimal = Field(ge=0, description="Monthly utilities cost")

    @field_validator(
        "property_tax_annual", "strata_fee_monthly", "insurance_annual", "utilities_monthly",
        mode="before"
    )
    @classmethod
    def convert_to_decimal(cls, v: float | Decimal | int | str) -> Decimal:
        """Convert input to Decimal for precision."""
        return Decimal(str(v))


class RentalIncome(BaseModel):
    """Rental income parameters."""

    monthly_rent: Decimal = Field(ge=0, description="Monthly rental income")
    vacancy_rate: Decimal = Field(ge=0, le=100, description="Vacancy rate (%)")

    @field_validator("monthly_rent", "vacancy_rate", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | Decimal | int | str) -> Decimal:
        """Convert input to Decimal for precision."""
        return Decimal(str(v))


class SaleDetails(BaseModel):
    """Property sale details."""

    sale_price: Decimal = Field(gt=0, description="Property sale price")
    holding_period_years: Decimal = Field(gt=0, description="Holding period in years")
    is_principal_residence: bool = Field(
        default=False, description="Is this a principal residence (PRE)"
    )
    marginal_tax_rate: Decimal = Field(
        ge=0, le=100, description="Marginal tax rate for capital gains (%)"
    )
    capital_improvements: Decimal = Field(
        ge=0, default=Decimal("0"), description="Capital improvements to property"
    )

    @field_validator(
        "sale_price", "holding_period_years", "marginal_tax_rate", "capital_improvements",
        mode="before"
    )
    @classmethod
    def convert_to_decimal(cls, v: float | Decimal | int | str) -> Decimal:
        """Convert input to Decimal for precision."""
        return Decimal(str(v))


@dataclass
class BuyerResults:
    """Results from buyer calculations."""

    down_payment: Decimal
    ptt_amount: Decimal
    ptt_exemption: Decimal
    closing_costs: Decimal
    total_cash_to_close: Decimal
    mortgage_amount: Decimal
    monthly_mortgage_payment: Decimal
    monthly_property_tax: Decimal
    monthly_strata_fee: Decimal
    monthly_insurance: Decimal
    monthly_utilities: Decimal
    total_monthly_carry_costs: Decimal
    monthly_rental_income: Decimal
    net_monthly_cash_flow: Decimal
    homeowner_grant_applied: bool


@dataclass
class SellerResults:
    """Results from seller calculations."""

    gross_proceeds: Decimal
    realtor_commission: Decimal
    legal_fees: Decimal
    adjusted_cost_base: Decimal
    capital_gain: Decimal
    taxable_capital_gain: Decimal
    capital_gains_tax: Decimal
    net_proceeds: Decimal
    principal_residence_exemption_applied: bool


@dataclass
class ComparisonResults:
    """Results from investment comparison analysis."""

    total_cash_invested: Decimal
    total_return: Decimal
    net_profit: Decimal
    roci_percent: Decimal
    irr_percent: Decimal
    holding_period_months: int
    cumulative_cash_flow: Decimal
