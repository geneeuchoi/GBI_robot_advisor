import pytest

from app.models.goal import GoalInput
from app.services.gap_analyzer import analyze_gap, _future_value


class TestFutureValue:
    def test_zero_rate(self):
        fv = _future_value(0, 100_0000, 0.0, 60)
        assert fv == 6000_0000

    def test_with_rate(self):
        fv = _future_value(0, 150_0000, 0.035, 60)
        assert fv > 150_0000 * 60  # 복리로 단순 합보다 큼

    def test_with_principal(self):
        fv_no_p = _future_value(0, 100_0000, 0.03, 12)
        fv_with_p = _future_value(1000_0000, 100_0000, 0.03, 12)
        assert fv_with_p > fv_no_p


class TestGapAnalyzer:
    def test_noah_needs_optimization(self, noah_goal):
        result = analyze_gap(noah_goal)
        assert result.optimization_needed is True
        assert result.gap > 0
        assert result.required_annual_return is not None
        assert result.required_annual_return > 0.035

    def test_easy_goal_no_optimization(self):
        easy = GoalInput(
            goal_amount=1000_0000,
            time_horizon_months=60,
            monthly_contribution=150_0000,
            initial_principal=0,
            eligible_youth_savings=False,
        )
        result = analyze_gap(easy)
        assert result.optimization_needed is False
        assert result.gap == 0
        assert result.required_annual_return is None

    def test_required_return_achieves_goal(self, noah_goal):
        result = analyze_gap(noah_goal)
        if result.required_annual_return is not None:
            fv = _future_value(
                noah_goal.initial_principal,
                noah_goal.monthly_contribution,
                result.required_annual_return,
                noah_goal.time_horizon_months,
            )
            assert abs(fv - noah_goal.goal_amount) < 1.0  # 1원 이내 오차
