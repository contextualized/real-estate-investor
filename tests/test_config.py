"""Tests for configuration loader."""

from decimal import Decimal
from pathlib import Path

import pytest

from bc_real_estate.config import Config, get_config


def test_config_loads_successfully(test_config_path: Path) -> None:
    """Test that configuration loads from TOML file."""
    Config._instance = None
    config = Config(test_config_path)

    assert config is not None
    assert len(config.ptt_tiers) == 3


def test_config_missing_file() -> None:
    """Test error handling for missing config file."""
    Config._instance = None
    with pytest.raises(FileNotFoundError):
        Config(Path("/nonexistent/path/config.toml"))


def test_config_singleton_pattern(test_config_path: Path) -> None:
    """Test that Config follows singleton pattern."""
    Config._instance = None
    config1 = Config(test_config_path)
    config2 = Config()

    assert config1 is config2


def test_get_config_function(test_config_path: Path) -> None:
    """Test get_config() function."""
    Config._instance = None
    config = get_config(test_config_path)

    assert config is not None
    assert isinstance(config, Config)


def test_ptt_tiers_property(config: Config) -> None:
    """Test PTT tiers property access."""
    tiers = config.ptt_tiers

    assert len(tiers) == 3
    assert tiers[0] == (Decimal("200000"), Decimal("0.01"))
    assert tiers[1] == (Decimal("2000000"), Decimal("0.02"))
    assert tiers[2] == (Decimal("3000000"), Decimal("0.03"))


def test_ptt_luxury_rate_property(config: Config) -> None:
    """Test PTT luxury rate property."""
    assert config.ptt_luxury_rate == Decimal("0.05")


def test_first_time_buyer_properties(config: Config) -> None:
    """Test first-time buyer exemption properties."""
    assert config.first_time_buyer_full_exemption_threshold == Decimal("500000")
    assert config.first_time_buyer_partial_exemption_threshold == Decimal("835000")
    assert config.first_time_buyer_partial_exemption_amount == Decimal("8000")
    assert config.first_time_buyer_phase_out_start == Decimal("835000")
    assert config.first_time_buyer_phase_out_end == Decimal("860000")


def test_newly_built_properties(config: Config) -> None:
    """Test newly built exemption properties."""
    assert config.newly_built_full_exemption_threshold == Decimal("1100000")
    assert config.newly_built_phase_out_start == Decimal("1100000")
    assert config.newly_built_phase_out_end == Decimal("1150000")


def test_speculation_tax_properties(config: Config) -> None:
    """Test speculation tax properties."""
    assert config.speculation_tax_resident == Decimal("0.01")
    assert config.speculation_tax_foreign == Decimal("0.03")


def test_homeowner_grant_properties(config: Config) -> None:
    """Test homeowner grant properties."""
    assert config.homeowner_grant_threshold == Decimal("2075000")
    assert config.homeowner_grant_amount == Decimal("570")


def test_capital_gains_properties(config: Config) -> None:
    """Test capital gains properties."""
    assert config.capital_gains_inclusion == Decimal("0.50")
    assert config.capital_gains_inclusion_high == Decimal("0.6667")


def test_realtor_commission_structure(config: Config) -> None:
    """Test realtor commission structure."""
    structure = config.realtor_commission_structure

    assert len(structure) == 2
    assert structure[0] == (Decimal("100000"), Decimal("0.07"))
    assert structure[1] == (Decimal("999999999"), Decimal("0.025"))


def test_closing_costs_properties(config: Config) -> None:
    """Test closing costs properties."""
    assert config.legal_fees == Decimal("1750")
    assert config.title_insurance == Decimal("300")
    assert config.appraisal_fee == Decimal("400")
    assert config.home_inspection == Decimal("600")
    assert config.legal_fees_sale == Decimal("1500")


def test_config_reload(test_config_path: Path) -> None:
    """Test configuration reload functionality."""
    Config._instance = None
    config = Config(test_config_path)

    original_value = config.legal_fees
    assert original_value == Decimal("1750")

    # Reload should work without error
    config.reload()

    # Value should remain the same after reload
    assert config.legal_fees == original_value
