"""BC Real Estate Investment Analyzer.

A modular Python package for analyzing British Columbia property investments.
"""

__version__ = "0.1.0"

from bc_real_estate.buyer import BuyerCalculator
from bc_real_estate.comparison import InvestmentAnalyzer
from bc_real_estate.config import get_config
from bc_real_estate.models import (
    BuyerResults,
    ComparisonResults,
    HoldingCosts,
    MortgageDetails,
    PropertyDetails,
    RentalIncome,
    SaleDetails,
    SellerResults,
)
from bc_real_estate.seller import SellerCalculator

__all__ = [
    "BuyerCalculator",
    "BuyerResults",
    "ComparisonResults",
    "get_config",
    "HoldingCosts",
    "InvestmentAnalyzer",
    "MortgageDetails",
    "PropertyDetails",
    "RentalIncome",
    "SaleDetails",
    "SellerCalculator",
    "SellerResults",
]
