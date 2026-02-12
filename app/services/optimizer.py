import numpy as np
from scipy.optimize import linprog

from app.config import settings
from app.models.asset import Asset, AssetClass
from app.models.goal import GoalInput
from app.models.portfolio import AllocationItem, OptimizationResult
from app.services.gap_analyzer import _future_value
from app.services.tax import after_tax_return


def optimize_portfolio(
    assets: list[Asset],
    goal: GoalInput,
    required_return: float | None = None,
    epsilon: float | None = None,
) -> OptimizationResult:
    """Phase 4: LP 솔버로 최적 포트폴리오를 산출한다.

    목적함수: Maximize Σ(w_i × after_tax_return_i)
    제약조건:
      1. 듀레이션 매칭: |Σ(w_i × D_i) - T_years| ≤ ε
      2. 최소 수익률: Σ(w_i × R_i) ≥ r_target (있을 경우)
      3. 예산: Σw_i = 1
      4. 공매도 금지: w_i ≥ 0
      5. 청년도약저축 한도: w_youth × C ≤ 70만
      6. ISA 한도: w_isa × 12C ≤ 2000만
    """
    if epsilon is None:
        epsilon = settings.duration_epsilon

    n = len(assets)
    T_years = goal.time_horizon_months / 12
    C = goal.monthly_contribution

    # 세후 수익률 벡터
    returns = np.array([after_tax_return(a.gross_return, a.tax_benefit) for a in assets])
    durations = np.array([a.duration for a in assets])

    # 목적함수: linprog는 minimize이므로 부호 반전
    c = -returns

    # 부등식 제약 (A_ub @ x <= b_ub)
    A_ub: list[list[float]] = []
    b_ub: list[float] = []

    # 1. 듀레이션 매칭: Σ(w_i × D_i) ≤ T + ε
    A_ub.append(durations.tolist())
    b_ub.append(T_years + epsilon)

    # 듀레이션 매칭: -Σ(w_i × D_i) ≤ -(T - ε)
    A_ub.append((-durations).tolist())
    b_ub.append(-(T_years - epsilon))

    # 2. 최소 수익률: -Σ(w_i × R_i) ≤ -r_target
    if required_return is not None:
        A_ub.append((-returns).tolist())
        b_ub.append(-required_return)

    # 5. 청년도약저축 한도: w_youth × C ≤ 70만
    for i, asset in enumerate(assets):
        if asset.asset_class == AssetClass.YOUTH_SAVINGS:
            row = [0.0] * n
            row[i] = C
            A_ub.append(row)
            b_ub.append(settings.youth_savings_monthly_limit)

    # 6. ISA 한도: w_isa × 12C ≤ 2000만
    for i, asset in enumerate(assets):
        if asset.asset_class == AssetClass.ISA_DEPOSIT:
            row = [0.0] * n
            row[i] = 12 * C
            A_ub.append(row)
            b_ub.append(settings.isa_annual_limit)

    # 등식 제약: Σw_i = 1
    A_eq = [np.ones(n).tolist()]
    b_eq = [1.0]

    # 범위: 0 ≤ w_i ≤ 1
    bounds = [(0.0, 1.0)] * n

    result = linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        return OptimizationResult(
            success=False,
            allocations=[],
            portfolio_duration=0.0,
            portfolio_return=0.0,
            expected_future_value=0.0,
            message=f"최적화 실패: {result.message}",
        )

    weights = result.x

    # 결과 구성
    allocations: list[AllocationItem] = []
    for i, asset in enumerate(assets):
        w = weights[i]
        if w < 1e-6:
            continue
        allocations.append(
            AllocationItem(
                asset_class=asset.asset_class,
                name=asset.name,
                weight=round(w, 4),
                monthly_amount=round(w * C, 0),
                duration_contribution=round(w * asset.duration, 4),
                after_tax_return=round(returns[i], 6),
            )
        )

    portfolio_duration = float(weights @ durations)
    portfolio_return = float(weights @ returns)

    expected_fv = _future_value(
        goal.initial_principal,
        goal.monthly_contribution,
        portfolio_return,
        goal.time_horizon_months,
    )

    return OptimizationResult(
        success=True,
        allocations=allocations,
        portfolio_duration=round(portfolio_duration, 4),
        portfolio_return=round(portfolio_return, 6),
        expected_future_value=round(expected_fv, 0),
        message="최적화 완료",
    )
