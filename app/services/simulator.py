from app.config import settings
from app.models.asset import Asset
from app.models.goal import GoalInput
from app.models.portfolio import AllocationItem, OptimizationResult
from app.models.simulation import (
    RateScenario,
    ScenarioResult,
    SimulationResponse,
)
from app.services.gap_analyzer import _future_value
from app.services.tax import after_tax_return

DEFAULT_SCENARIOS = [
    RateScenario(label="금리 급락 (-1.5%)", rate_shift=-0.015),
    RateScenario(label="금리 소폭 하락 (-0.5%)", rate_shift=-0.005),
    RateScenario(label="금리 변동 없음", rate_shift=0.0),
    RateScenario(label="금리 상승 (+1.0%)", rate_shift=0.01),
]


def _portfolio_fv_under_shift(
    goal: GoalInput,
    portfolio: OptimizationResult,
    assets: list[Asset],
    rate_shift: float,
) -> float:
    """금리 변동 시 포트폴리오의 미래가치를 계산한다.

    듀레이션 매칭 면역화 효과:
    - 가격 변동 효과: ΔP ≈ -D × Δy × PV (금리 상승 시 가격 하락)
    - 재투자 효과: 금리 상승 시 재투자 수익 증가
    - 듀레이션 매칭 시 두 효과가 상쇄
    - 잔여 효과는 (D_portfolio - T)^2 × convexity 에 비례 (2차 효과)
    """
    asset_map = {a.asset_class: a for a in assets}
    total_fv = 0.0

    for alloc in portfolio.allocations:
        asset = asset_map.get(alloc.asset_class)
        if asset is None:
            continue

        # 기본 수익률에 금리 변동 반영
        shifted_gross = asset.gross_return + rate_shift
        shifted_after_tax = after_tax_return(max(shifted_gross, 0.0), asset.tax_benefit)

        monthly_amount = alloc.monthly_amount
        weight_principal = alloc.weight * goal.initial_principal

        asset_fv = _future_value(
            weight_principal,
            monthly_amount,
            shifted_after_tax,
            goal.time_horizon_months,
        )

        # 듀레이션 매칭 면역화 보정
        # 듀레이션이 목표와 일치하면 금리 변동의 1차 효과가 상쇄됨
        # 잔여 2차 효과만 남음 (convexity bonus)
        T_years = goal.time_horizon_months / 12
        duration_gap = asset.duration - T_years
        # 면역화 보정: 듀레이션 갭이 작을수록 금리 변동 영향 감소
        immunization_factor = 1.0 - abs(duration_gap) * abs(rate_shift) * 0.5
        immunization_factor = max(0.8, min(1.2, immunization_factor))

        total_fv += asset_fv * immunization_factor

    return total_fv


def simulate_scenarios(
    goal: GoalInput,
    portfolio: OptimizationResult,
    assets: list[Asset],
    base_rate: float | None = None,
    scenarios: list[RateScenario] | None = None,
) -> SimulationResponse:
    """Section 5: 금리 변동 시뮬레이션을 수행한다."""
    if base_rate is None:
        base_rate = settings.base_interest_rate
    if scenarios is None:
        scenarios = DEFAULT_SCENARIOS

    results: list[ScenarioResult] = []

    for scenario in scenarios:
        new_rate = base_rate + scenario.rate_shift

        # (A) 단순 적금
        safe_after_tax = new_rate * (1 - settings.interest_income_tax_rate)
        simple_fv = _future_value(
            goal.initial_principal,
            goal.monthly_contribution,
            safe_after_tax,
            goal.time_horizon_months,
        )

        # (B) GBI 포트폴리오
        portfolio_fv = _portfolio_fv_under_shift(
            goal, portfolio, assets, scenario.rate_shift
        )

        results.append(
            ScenarioResult(
                label=scenario.label,
                rate_shift=scenario.rate_shift,
                new_rate=round(new_rate, 4),
                simple_savings_fv=round(simple_fv, 0),
                portfolio_fv=round(portfolio_fv, 0),
                difference=round(portfolio_fv - simple_fv, 0),
            )
        )

    return SimulationResponse(base_rate=base_rate, results=results)
