"""엣지케이스 테스트: 극단적 입력값, 불가능한 목표, 수치 안정성 검증."""
import pytest

from app.models.asset import TaxBenefit
from app.models.goal import GoalInput
from app.services.asset_universe import get_default_universe
from app.services.duration import macaulay_duration
from app.services.gap_analyzer import _future_value, analyze_gap
from app.services.optimizer import optimize_portfolio
from app.services.simulator import simulate_scenarios
from app.services.tax import after_tax_return


# ============================================================
# 갭 분석 엣지케이스
# ============================================================

class TestGapAnalyzerEdgeCases:
    def test_impossible_goal_tiny_contribution(self):
        """월 10만원으로 1년 안에 10억은 불가능."""
        goal = GoalInput(
            goal_amount=10_0000_0000,
            time_horizon_months=12,
            monthly_contribution=10_0000,
        )
        result = analyze_gap(goal)
        assert result.optimization_needed is True
        assert result.goal_achievable is False
        assert result.required_annual_return is None

    def test_initial_principal_covers_goal(self):
        """초기자본이 목표를 이미 초과."""
        goal = GoalInput(
            goal_amount=1000_0000,
            time_horizon_months=60,
            monthly_contribution=100_0000,
            initial_principal=2000_0000,
        )
        result = analyze_gap(goal)
        assert result.optimization_needed is False
        assert result.gap == 0
        assert result.goal_achievable is True

    def test_short_horizon_achievable(self):
        """12개월로 약간 부족한 경우 → 달성 가능."""
        goal = GoalInput(
            goal_amount=1900_0000,
            time_horizon_months=12,
            monthly_contribution=150_0000,
        )
        result = analyze_gap(goal)
        assert result.optimization_needed is True
        assert result.goal_achievable is True
        assert result.required_annual_return is not None

    def test_one_month_horizon_too_much_gap(self):
        """1개월에 150만→200만은 연 400% 수익률 필요 → 불가능."""
        goal = GoalInput(
            goal_amount=200_0000,
            time_horizon_months=1,
            monthly_contribution=150_0000,
        )
        result = analyze_gap(goal)
        assert result.optimization_needed is True
        assert result.goal_achievable is False

    def test_one_month_impossible(self):
        """1개월로 100배 목표는 불가능."""
        goal = GoalInput(
            goal_amount=1_0000_0000,
            time_horizon_months=1,
            monthly_contribution=10_0000,
        )
        result = analyze_gap(goal)
        assert result.goal_achievable is False

    def test_zero_months_future_value(self):
        """0개월이면 초기자본만 반환."""
        fv = _future_value(500_0000, 100_0000, 0.05, 0)
        assert fv == 500_0000

    def test_very_high_rate_future_value(self):
        """극단적으로 높은 금리에서도 동작."""
        fv = _future_value(0, 100_0000, 0.99, 12)
        assert fv > 0
        assert fv > 100_0000 * 12  # 복리 효과

    def test_negative_rate_future_value(self):
        """음수 금리에서 FV가 단순 합산보다 작음."""
        fv_neg = _future_value(0, 100_0000, -0.02, 60)
        fv_zero = _future_value(0, 100_0000, 0.0, 60)
        assert fv_neg < fv_zero


# ============================================================
# 세금 계산 엣지케이스
# ============================================================

class TestTaxEdgeCases:
    def test_negative_return_no_tax(self):
        """음수 수익률에는 세금을 부과하지 않음."""
        result = after_tax_return(-0.05, TaxBenefit.NONE)
        assert result == -0.05

    def test_negative_return_isa(self):
        """ISA 손실에도 세금 없음."""
        result = after_tax_return(-0.02, TaxBenefit.SEPARATE_TAX)
        assert result == -0.02

    def test_very_small_return(self):
        """매우 작은 수익률."""
        result = after_tax_return(0.0001, TaxBenefit.NONE)
        assert result > 0
        assert result < 0.0001


# ============================================================
# 듀레이션 엣지케이스
# ============================================================

class TestDurationEdgeCases:
    def test_empty_cash_flows(self):
        assert macaulay_duration([], [], 0.05) == 0.0

    def test_single_cash_flow(self):
        d = macaulay_duration([100], [5.0], 0.05)
        assert d == 5.0  # 단일 현금흐름 → 듀레이션 = 해당 시점

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="길이가 다릅니다"):
            macaulay_duration([100, 200], [1.0], 0.05)

    def test_invalid_ytm_raises(self):
        with pytest.raises(ValueError, match="YTM"):
            macaulay_duration([100], [1.0], -1.0)


# ============================================================
# 옵티마이저 엣지케이스
# ============================================================

class TestOptimizerEdgeCases:
    def test_empty_assets(self):
        """빈 자산 유니버스."""
        goal = GoalInput(
            goal_amount=1_0000_0000,
            time_horizon_months=60,
            monthly_contribution=150_0000,
            eligible_youth_savings=True,
        )
        result = optimize_portfolio(assets=[], goal=goal)
        assert result.success is False
        assert "자산이 없습니다" in result.message

    def test_infeasible_required_return(self):
        """달성 불가능한 수익률 요구."""
        goal = GoalInput(
            goal_amount=1_0000_0000,
            time_horizon_months=60,
            monthly_contribution=150_0000,
        )
        assets = get_default_universe(eligible_youth_savings=False)
        result = optimize_portfolio(
            assets=assets,
            goal=goal,
            required_return=0.50,  # 50% 수익률 요구
        )
        assert result.success is False
        assert "수익률" in result.message or "실패" in result.message

    def test_without_youth_savings_still_works(self):
        """청년도약 없이도 최적화 가능."""
        goal = GoalInput(
            goal_amount=1_0000_0000,
            time_horizon_months=60,
            monthly_contribution=150_0000,
            eligible_youth_savings=False,
        )
        gap = analyze_gap(goal)
        assets = get_default_universe(eligible_youth_savings=False)
        result = optimize_portfolio(
            assets=assets,
            goal=goal,
            required_return=gap.required_annual_return,
        )
        # 수익률이 낮아 실패할 수도, 성공할 수도 있음
        assert isinstance(result.success, bool)
        if result.success:
            total = sum(a.weight for a in result.allocations)
            assert abs(total - 1.0) < 0.01

    def test_very_short_horizon(self):
        """3개월 목표 기간."""
        goal = GoalInput(
            goal_amount=500_0000,
            time_horizon_months=3,
            monthly_contribution=150_0000,
        )
        assets = get_default_universe(eligible_youth_savings=False)
        result = optimize_portfolio(assets=assets, goal=goal)
        # 듀레이션 매칭이 매우 짧은 목표에서도 실행됨
        assert isinstance(result.success, bool)


# ============================================================
# 시뮬레이터 엣지케이스
# ============================================================

class TestSimulatorEdgeCases:
    def test_extreme_negative_rate_shift(self):
        """기준금리보다 큰 하락 (음수 금리)."""
        goal = GoalInput(
            goal_amount=1_0000_0000,
            time_horizon_months=60,
            monthly_contribution=150_0000,
            eligible_youth_savings=True,
        )
        gap = analyze_gap(goal)
        assets = get_default_universe(True)
        portfolio = optimize_portfolio(assets=assets, goal=goal,
                                        required_return=gap.required_annual_return)

        from app.models.simulation import RateScenario
        extreme = [RateScenario(label="극단적 하락", rate_shift=-0.05)]
        result = simulate_scenarios(goal, portfolio, assets, scenarios=extreme)

        assert len(result.results) == 1
        # 음수 금리 클램프 → simple_savings_fv는 단순 합산에 가까움
        assert result.results[0].simple_savings_fv > 0

    def test_empty_portfolio_simulation(self):
        """빈 포트폴리오로 시뮬레이션."""
        from app.models.portfolio import OptimizationResult

        goal = GoalInput(
            goal_amount=1_0000_0000,
            time_horizon_months=60,
            monthly_contribution=150_0000,
        )
        empty_portfolio = OptimizationResult(
            success=False,
            allocations=[],
            portfolio_duration=0.0,
            portfolio_return=0.0,
            expected_future_value=0.0,
            message="빈 포트폴리오",
        )
        assets = get_default_universe(False)
        result = simulate_scenarios(goal, empty_portfolio, assets)

        assert len(result.results) == 4
        # 빈 포트폴리오 → 단순 합산
        for r in result.results:
            assert r.portfolio_fv > 0


# ============================================================
# API 엣지케이스
# ============================================================

class TestAPIEdgeCases:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_impossible_goal_returns_failure(self, client):
        """달성 불가능한 목표."""
        resp = client.post("/api/v1/optimize", json={
            "goal_amount": 10_0000_0000,
            "time_horizon_months": 6,
            "monthly_contribution": 10_0000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "불가능" in data["message"]

    def test_gap_analysis_shows_achievable_flag(self, client):
        """갭 분석에 goal_achievable 필드 반환."""
        resp = client.post("/api/v1/gap-analysis", json={
            "goal_amount": 10_0000_0000,
            "time_horizon_months": 6,
            "monthly_contribution": 10_0000,
        })
        data = resp.json()
        assert data["goal_achievable"] is False

    def test_simulate_impossible_goal(self, client):
        """불가능한 목표에서도 시뮬레이션은 반환."""
        resp = client.post("/api/v1/simulate", json={
            "goal_amount": 10_0000_0000,
            "time_horizon_months": 6,
            "monthly_contribution": 10_0000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 4

    def test_very_large_goal(self, client):
        """매우 큰 목표 (100억)."""
        resp = client.post("/api/v1/gap-analysis", json={
            "goal_amount": 100_0000_0000,
            "time_horizon_months": 60,
            "monthly_contribution": 150_0000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["goal_achievable"] is False

    def test_missing_required_field(self, client):
        """필수 필드 누락."""
        resp = client.post("/api/v1/optimize", json={
            "goal_amount": 1_0000_0000,
        })
        assert resp.status_code == 422
