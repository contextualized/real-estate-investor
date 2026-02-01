"""Investment comparison and analysis calculations."""

from decimal import Decimal

import numpy_financial as npf

from bc_real_estate.models import BuyerResults, ComparisonResults, SellerResults


class InvestmentAnalyzer:
    """Analyze investment returns with ROCI and IRR calculations."""

    @staticmethod
    def calculate_total_cash_invested(
        initial_cash_to_close: Decimal,
        cumulative_cash_flow: Decimal,
    ) -> Decimal:
        """Calculate total cash invested.

        Initial cash to close + cumulative negative cash flow (if any).

        Args:
            initial_cash_to_close: Initial cash required to close
            cumulative_cash_flow: Cumulative cash flow over holding period

        Returns:
            Total cash invested
        """
        # If cumulative cash flow is negative, it's additional cash invested
        if cumulative_cash_flow < 0:
            return initial_cash_to_close + abs(cumulative_cash_flow)
        else:
            # If positive, only initial cash was invested
            return initial_cash_to_close

    @staticmethod
    def calculate_roci(
        total_return: Decimal,
        total_cash_invested: Decimal,
    ) -> Decimal:
        """Calculate Return on Cash Invested (ROCI).

        ROCI = (total_return / total_cash_invested) × 100

        Args:
            total_return: Total return (net proceeds - total invested + cumulative flow)
            total_cash_invested: Total cash invested

        Returns:
            ROCI as percentage
        """
        if total_cash_invested <= 0:
            return Decimal("0")

        roci = (total_return / total_cash_invested) * Decimal("100")
        return roci.quantize(Decimal("0.01"))

    @staticmethod
    def calculate_irr(
        initial_investment: Decimal,
        monthly_cash_flow: Decimal,
        net_proceeds: Decimal,
        holding_period_years: Decimal,
    ) -> Decimal:
        """Calculate Internal Rate of Return (IRR).

        Uses monthly cash flows and converts to annualized IRR.

        Args:
            initial_investment: Initial cash to close (negative)
            monthly_cash_flow: Monthly net cash flow
            net_proceeds: Net proceeds from sale
            holding_period_years: Holding period in years

        Returns:
            Annualized IRR as percentage
        """
        try:
            # Build monthly cash flow array
            holding_period_months = int(holding_period_years * 12)

            # Initial investment (negative)
            cash_flows = [-float(initial_investment)]

            # Monthly cash flows
            for _ in range(holding_period_months - 1):
                cash_flows.append(float(monthly_cash_flow))

            # Final month includes net proceeds
            final_cash_flow = float(monthly_cash_flow) + float(net_proceeds)
            cash_flows.append(final_cash_flow)

            # Calculate monthly IRR
            monthly_irr = npf.irr(cash_flows)

            # Check if calculation failed
            import math
            if (
                monthly_irr is None
                or not isinstance(monthly_irr, (int, float))
                or math.isnan(monthly_irr)
                or math.isinf(monthly_irr)
            ):
                return Decimal("0")

            # Convert to annual IRR: (1 + monthly_irr)^12 - 1
            annual_irr = ((1 + monthly_irr) ** 12 - 1) * 100

            return Decimal(str(annual_irr)).quantize(Decimal("0.01"))

        except (ValueError, TypeError, OverflowError):  # pragma: no cover
            # IRR calculation failed - return 0%
            return Decimal("0")

    @staticmethod
    def calculate_all(
        buyer_results: BuyerResults,
        seller_results: SellerResults,
        holding_period_years: Decimal,
    ) -> ComparisonResults:
        """Calculate comprehensive investment analysis.

        Args:
            buyer_results: Results from buyer calculations
            seller_results: Results from seller calculations
            holding_period_years: Holding period in years

        Returns:
            ComparisonResults with all investment metrics
        """
        # Calculate cumulative cash flow
        holding_period_months = int(holding_period_years * 12)
        cumulative_cash_flow = (
            buyer_results.net_monthly_cash_flow * Decimal(holding_period_months)
        )

        # Total cash invested
        total_cash_invested = InvestmentAnalyzer.calculate_total_cash_invested(
            buyer_results.total_cash_to_close,
            cumulative_cash_flow,
        )

        # Total return = net proceeds - total invested + cumulative flow (if positive)
        if cumulative_cash_flow >= 0:
            total_return = (
                seller_results.net_proceeds - buyer_results.total_cash_to_close + cumulative_cash_flow
            )
        else:
            total_return = seller_results.net_proceeds - total_cash_invested

        # Net profit
        net_profit = total_return

        # ROCI
        roci = InvestmentAnalyzer.calculate_roci(total_return, total_cash_invested)

        # IRR
        irr = InvestmentAnalyzer.calculate_irr(
            buyer_results.total_cash_to_close,
            buyer_results.net_monthly_cash_flow,
            seller_results.net_proceeds,
            holding_period_years,
        )

        return ComparisonResults(
            total_cash_invested=total_cash_invested,
            total_return=total_return,
            net_profit=net_profit,
            roci_percent=roci,
            irr_percent=irr,
            holding_period_months=holding_period_months,
            cumulative_cash_flow=cumulative_cash_flow,
        )
