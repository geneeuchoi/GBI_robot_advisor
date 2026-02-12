import pytest

from app.services.asset_universe import get_default_universe
from app.services.gap_analyzer import analyze_gap
from app.services.optimizer import optimize_portfolio
from app.services.simulator import simulate_scenarios


class TestSimulator:
    @pytest.fixture
    def noah_portfolio(self, noah_goal):
        gap = analyze_gap(noah_goal)
        assets = get_default_universe(noah_goal.eligible_youth_savings)
        portfolio = optimize_portfolio(
            assets=assets,
            goal=noah_goal,
            required_return=gap.required_annual_return,
        )
        return portfolio, assets

    def test_default_four_scenarios(self, noah_goal, noah_portfolio):
        portfolio, assets = noah_portfolio
        result = simulate_scenarios(noah_goal, portfolio, assets)
        assert len(result.results) == 4

    def test_portfolio_beats_simple_savings(self, noah_goal, noah_portfolio):
        portfolio, assets = noah_portfolio
        result = simulate_scenarios(noah_goal, portfolio, assets)
        for scenario in result.results:
            assert scenario.difference > 0

    def test_base_rate_matches(self, noah_goal, noah_portfolio):
        portfolio, assets = noah_portfolio
        result = simulate_scenarios(noah_goal, portfolio, assets)
        assert result.base_rate == 0.035

    def test_rate_shifts_applied(self, noah_goal, noah_portfolio):
        portfolio, assets = noah_portfolio
        result = simulate_scenarios(noah_goal, portfolio, assets)
        for scenario in result.results:
            expected_new_rate = round(0.035 + scenario.rate_shift, 4)
            assert scenario.new_rate == expected_new_rate
