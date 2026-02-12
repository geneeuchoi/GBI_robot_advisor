from fastapi import APIRouter

from app.models.goal import GoalInput
from app.models.portfolio import OptimizationResult
from app.services.asset_universe import get_default_universe
from app.services.gap_analyzer import analyze_gap
from app.services.optimizer import optimize_portfolio

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResult)
def optimize(goal: GoalInput) -> OptimizationResult:
    """Phase 1~4 전체 파이프라인: 목표를 입력하면 최적 포트폴리오를 반환한다."""
    gap_result = analyze_gap(goal)

    if not gap_result.optimization_needed:
        return OptimizationResult(
            success=True,
            allocations=[],
            portfolio_duration=0.0,
            portfolio_return=0.0,
            expected_future_value=gap_result.future_value_safe,
            message="안전자산만으로 목표 달성 가능합니다.",
        )

    assets = get_default_universe(goal.eligible_youth_savings)

    return optimize_portfolio(
        assets=assets,
        goal=goal,
        required_return=gap_result.required_annual_return,
    )
