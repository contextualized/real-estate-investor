# BC Real Estate Investment Analyzer

A modular Python package with Streamlit UI for analyzing British Columbia property investments. Calculate acquisition costs, holding expenses, exit proceeds, and investment returns (ROCI, IRR).

## Features

- **Buyer Assessment**: Calculate cash to close including BC Property Transfer Tax (PTT) with first-time buyer and newly built exemptions
- **Seller Forecast**: Calculate net proceeds including realtor commission and capital gains tax
- **Investment Analysis**: Compare scenarios with ROCI and IRR calculations

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for package management.

```bash
# Install dependencies
uv sync

# Install with development dependencies
uv sync --dev
```

## Usage

### Running the Streamlit App

```bash
uv run streamlit run streamlit_app/app.py
```

### Using as a Python Package

```python
from decimal import Decimal
from bc_real_estate import (
    BuyerCalculator,
    PropertyDetails,
    MortgageDetails,
    HoldingCosts,
)

# Define property details
property_details = PropertyDetails(
    purchase_price=Decimal("800000"),
    is_first_time_buyer=True,
    is_newly_built=False,
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

# Calculate buyer costs
calculator = BuyerCalculator()
results = calculator.calculate_all(
    property_details,
    mortgage_details,
    holding_costs,
    rental_income=None,
    include_inspection=True,
)

print(f"Total Cash to Close: ${results.total_cash_to_close:,.2f}")
print(f"PTT Amount: ${results.ptt_amount:,.2f}")
print(f"PTT Exemption: ${results.ptt_exemption:,.2f}")
```

## Testing

The project has **100% test coverage** with 113 comprehensive tests.

Run the full test suite with coverage:

```bash
uv run pytest -v --cov=src/bc_real_estate --cov-report=term-missing
```

Run specific test files:

```bash
uv run pytest tests/test_buyer.py -v       # PTT calculations
uv run pytest tests/test_seller.py -v      # Commission & capital gains
uv run pytest tests/test_comparison.py -v  # ROCI & IRR
uv run pytest tests/test_utils.py -v       # Mortgage & utilities
uv run pytest tests/test_config.py -v      # Configuration loader
```

## Configuration

BC tax rates and assumptions are stored in `defaults.toml`. You can customize these values or provide an alternative configuration file.

### Key Configuration Values (2026)

- **PTT Tiers**: 1% on first $200k, 2% up to $2M, 3% up to $3M, 5% above $3M
- **First-Time Buyer Exemption**: Full exemption up to $500k, partial up to $835k
- **Newly Built Exemption**: Full exemption up to $1.1M
- **Realtor Commission**: 7% on first $100k, 2.5% on remainder
- **Capital Gains Inclusion**: 50% (default) or 66.67%

## Project Structure

```
├── src/bc_real_estate/     # Core calculation package
│   ├── models.py           # Pydantic models
│   ├── config.py           # TOML configuration loader
│   ├── utils.py            # Mortgage & formatting helpers
│   ├── buyer.py            # Acquisition calculations
│   ├── seller.py           # Exit calculations
│   └── comparison.py       # Investment analysis
├── streamlit_app/          # Streamlit UI
│   ├── app.py              # Main entrypoint
│   └── pages/              # Tab pages
├── tests/                  # Test suite
└── defaults.toml           # BC tax rates & assumptions
```

## Development

This project uses:
- **uv**: Package management
- **pytest**: Testing with 100% coverage requirement
- **ruff**: Linting and formatting
- **mypy**: Type checking
- **pydantic**: Input validation

## License

MIT
