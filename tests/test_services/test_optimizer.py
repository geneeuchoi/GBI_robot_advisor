import pytest

from app.services.asset_universe import get_default_universe
from app.services.gap_analyzer import analyze_gap
from app.services.optimizer import optimize_portfolio


class TestOptimizer:
    def test_noah_optimization_succeeds(self, noah_goal):
        gap = analyze_gap(noah_goal)
        assets = get_default_universe(noah_goal.eligible_youth_savings)
        result = optimize_portfolio(
            assets=assets,
            goal=noah_goal,
            required_return=gap.required_annual_return,
        )
        assert result.success is True
        assert len(result.allocations) > 0

    def test_weights_sum_to_one(self, noah_goal):
        gap = analyze_gap(noah_goal)
        assets = get_default_universe(noah_goal.eligible_youth_savings)
        result = optimize_portfolio(
            assets=assets,
            goal=noah_goal,
            required_return=gap.required_annual_return,
        )
        total_weight = sum(a.weight for a in result.allocations)
        assert abs(total_weight - 1.0) < 0.01

    def test_duration_within_epsilon(self, noah_goal):
        gap = analyze_gap(noah_goal)
        assets = get_default_universe(noah_goal.eligible_youth_savings)
        result = optimize_portfolio(
            assets=assets,
            goal=noah_goal,
            required_return=gap.required_annual_return,
        )
        T_years = noah_goal.time_horizon_months / 12
        assert abs(result.portfolio_duration - T_years) <= 0.5 + 0.01

    def test_youth_savings_within_limit(self, noah_goal):
        gap = analyze_gap(noah_goal)
        assets = get_default_universe(noah_goal.eligible_youth_savings)
        result = optimize_portfolio(
            assets=assets,
            goal=noah_goal,
            required_return=gap.required_annual_return,
        )
        for alloc in result.allocations:
            if alloc.asset_class == "youth_savings":
                assert alloc.monthly_amount <= 70_0000 + 1  # 반올림 허용

    def test_expected_fv_near_goal(self, noah_goal):
        gap = analyze_gap(noah_goal)
        assets = get_default_universe(noah_goal.eligible_youth_savings)
        result = optimize_portfolio(
            assets=assets,
            goal=noah_goal,
            required_return=gap.required_annual_return,
        )
        assert result.expected_future_value >= noah_goal.goal_amount * 0.95

    def test_no_negative_weights(self, noah_goal):
        gap = analyze_gap(noah_goal)
        assets = get_default_universe(noah_goal.eligible_youth_savings)
        result = optimize_portfolio(
            assets=assets,
            goal=noah_goal,
            required_return=gap.required_annual_return,
        )
        for alloc in result.allocations:
            assert alloc.weight >= 0
