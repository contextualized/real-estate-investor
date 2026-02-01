"""Configuration loader for BC tax rates and assumptions."""

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        raise ImportError(
            "tomli is required for Python < 3.11. Install with: pip install tomli"
        )


class Config:
    """Singleton configuration loader for BC tax rates and assumptions."""

    _instance: "Config | None" = None
    _config_data: dict[str, Any]
    _config_path: Path

    def __new__(cls, config_path: Path | None = None) -> "Config":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: Path | None = None) -> None:
        """Load configuration from TOML file."""
        if config_path is None:
            # Default to defaults.toml in project root
            config_path = Path(__file__).parent.parent.parent / "defaults.toml"

        self._config_path = config_path

        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        with open(self._config_path, "rb") as f:
            self._config_data = tomllib.load(f)

    def reload(self, config_path: Path | None = None) -> None:
        """Reload configuration from file."""
        self._load_config(config_path)

    @property
    def ptt_tiers(self) -> list[tuple[Decimal, Decimal]]:
        """Property Transfer Tax tiers as [(threshold, rate), ...]."""
        tiers = self._config_data["bc_tax_rates"]["ptt_tiers"]
        return [(Decimal(str(t[0])), Decimal(str(t[1]))) for t in tiers]

    @property
    def ptt_luxury_rate(self) -> Decimal:
        """PTT rate above $3M."""
        return Decimal(str(self._config_data["bc_tax_rates"]["ptt_luxury_rate"]))

    @property
    def first_time_buyer_full_exemption_threshold(self) -> Decimal:
        """First-time buyer full exemption threshold."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["first_time_buyer_full_exemption_threshold"])
        )

    @property
    def first_time_buyer_partial_exemption_threshold(self) -> Decimal:
        """First-time buyer partial exemption threshold."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["first_time_buyer_partial_exemption_threshold"])
        )

    @property
    def first_time_buyer_partial_exemption_amount(self) -> Decimal:
        """First-time buyer partial exemption amount."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["first_time_buyer_partial_exemption_amount"])
        )

    @property
    def first_time_buyer_phase_out_start(self) -> Decimal:
        """First-time buyer phase-out start threshold."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["first_time_buyer_phase_out_start"])
        )

    @property
    def first_time_buyer_phase_out_end(self) -> Decimal:
        """First-time buyer phase-out end threshold."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["first_time_buyer_phase_out_end"])
        )

    @property
    def newly_built_full_exemption_threshold(self) -> Decimal:
        """Newly built home full exemption threshold."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["newly_built_full_exemption_threshold"])
        )

    @property
    def newly_built_phase_out_start(self) -> Decimal:
        """Newly built home phase-out start threshold."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["newly_built_phase_out_start"])
        )

    @property
    def newly_built_phase_out_end(self) -> Decimal:
        """Newly built home phase-out end threshold."""
        return Decimal(
            str(self._config_data["bc_tax_rates"]["newly_built_phase_out_end"])
        )

    @property
    def speculation_tax_resident(self) -> Decimal:
        """Speculation tax rate for BC residents."""
        return Decimal(str(self._config_data["bc_tax_rates"]["speculation_tax_resident"]))

    @property
    def speculation_tax_foreign(self) -> Decimal:
        """Speculation tax rate for foreign owners."""
        return Decimal(str(self._config_data["bc_tax_rates"]["speculation_tax_foreign"]))

    @property
    def homeowner_grant_threshold(self) -> Decimal:
        """BC homeowner grant assessed value threshold."""
        return Decimal(str(self._config_data["bc_tax_rates"]["homeowner_grant_threshold"]))

    @property
    def homeowner_grant_amount(self) -> Decimal:
        """BC homeowner grant annual amount."""
        return Decimal(str(self._config_data["bc_tax_rates"]["homeowner_grant_amount"]))

    @property
    def capital_gains_inclusion(self) -> Decimal:
        """Default capital gains inclusion rate."""
        return Decimal(str(self._config_data["assumptions"]["capital_gains_inclusion"]))

    @property
    def capital_gains_inclusion_high(self) -> Decimal:
        """Alternative high capital gains inclusion rate."""
        return Decimal(str(self._config_data["assumptions"]["capital_gains_inclusion_high"]))

    @property
    def realtor_commission_structure(self) -> list[tuple[Decimal, Decimal]]:
        """Realtor commission structure as [(threshold, rate), ...]."""
        structure = self._config_data["assumptions"]["realtor_commission_structure"]
        return [(Decimal(str(s[0])), Decimal(str(s[1]))) for s in structure]

    @property
    def legal_fees(self) -> Decimal:
        """Typical legal fees for purchase."""
        return Decimal(str(self._config_data["assumptions"]["legal_fees"]))

    @property
    def title_insurance(self) -> Decimal:
        """Typical title insurance cost."""
        return Decimal(str(self._config_data["assumptions"]["title_insurance"]))

    @property
    def appraisal_fee(self) -> Decimal:
        """Typical appraisal fee."""
        return Decimal(str(self._config_data["assumptions"]["appraisal_fee"]))

    @property
    def home_inspection(self) -> Decimal:
        """Typical home inspection cost."""
        return Decimal(str(self._config_data["assumptions"]["home_inspection"]))

    @property
    def legal_fees_sale(self) -> Decimal:
        """Typical legal fees for sale."""
        return Decimal(str(self._config_data["assumptions"]["legal_fees_sale"]))


def get_config(config_path: Path | None = None) -> Config:
    """Get the singleton configuration instance.

    Args:
        config_path: Optional path to configuration file. If None, uses defaults.toml.

    Returns:
        Config instance.
    """
    return Config(config_path)
