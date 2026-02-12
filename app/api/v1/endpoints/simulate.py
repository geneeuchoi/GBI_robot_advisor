from fastapi import APIRouter

from app.models.goal import GoalInput
from app.models.simulation import SimulationRequest, SimulationResponse
from app.services.asset_universe import get_default_universe
from app.services.gap_analyzer import analyze_gap
from app.services.optimizer import optimize_portfolio
from app.services.simulator import simulate_scenarios

router = APIRouter()


@router.post("/simulate", response_model=SimulationResponse)
def simulate(req: SimulationRequest) -> SimulationResponse:
    """Section 5: 금리 변동 시뮬레이션을 수행한다."""
    goal = GoalInput(
        goal_amount=req.goal_amount,
        time_horizon_months=req.time_horizon_months,
        monthly_contribution=req.monthly_contribution,
        initial_principal=req.initial_principal,
        eligible_youth_savings=req.eligible_youth_savings,
    )

    gap_result = analyze_gap(goal)
    assets = get_default_universe(goal.eligible_youth_savings)
    portfolio = optimize_portfolio(
        assets=assets,
        goal=goal,
        required_return=gap_result.required_annual_return,
    )

    return simulate_scenarios(
        goal=goal,
        portfolio=portfolio,
        assets=assets,
        scenarios=req.scenarios,
    )
