import numpy as np
from scipy.optimize import linprog

from app.config import settings
from app.models.asset import Asset, AssetClass
from app.models.goal import GoalInput
from app.models.portfolio import AllocationItem, OptimizationResult
from app.services.gap_analyzer import _future_value
from app.services.tax import after_tax_return


def _diagnose_infeasibility(
    assets: list[Asset],
    returns: np.ndarray,
    durations: np.ndarray,
    T_years: float,
    epsilon: float,
    required_return: float | None,
) -> str:
    """LP 솔버 실패 시 원인을 진단한다."""
    reasons: list[str] = []

    # 듀레이션 달성 가능 범위 확인
    d_min = float(durations.min())
    d_max = float(durations.max())
    target_low = T_years - epsilon
    target_high = T_years + epsilon

    if d_max < target_low:
        reasons.append(
            f"보유 자산의 최대 듀레이션({d_max:.1f}년)이 "
            f"목표 범위 하한({target_low:.1f}년)보다 짧습니다."
        )
    if d_min > target_high:
        reasons.append(
            f"보유 자산의 최소 듀레이션({d_min:.1f}년)이 "
            f"목표 범위 상한({target_high:.1f}년)보다 깁니다."
        )

    # 수익률 달성 가능 여부 확인
    if required_return is not None:
        max_return = float(returns.max())
        if max_return < required_return:
            reasons.append(
                f"최고 세후 수익률({max_return:.2%})이 "
                f"필요 수익률({required_return:.2%})에 미달합니다. "
                f"월 저축액을 늘리거나 목표 기간을 연장해보세요."
            )

    if not reasons:
        reasons.append("제약 조건 조합이 동시에 만족 불가합니다.")

    return "최적화 실패: " + " ".join(reasons)


def optimize_portfolio(
    assets: list[Asset],
    goal: GoalInput,
    required_return: float | None = None,
    epsilon: float | None = None,
) -> OptimizationResult:
    """Phase 4: LP 솔버로 최적 포트폴리오를 산출한다."""
    if epsilon is None:
        epsilon = settings.duration_epsilon

    n = len(assets)

    # 빈 자산 유니버스 방어
    if n == 0:
        return OptimizationResult(
            success=False,
            allocations=[],
            portfolio_duration=0.0,
            portfolio_return=0.0,
            expected_future_value=0.0,
            message="최적화 실패: 투자 가능한 자산이 없습니다.",
        )

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
        message = _diagnose_infeasibility(
            assets, returns, durations, T_years, epsilon, required_return
        )
        return OptimizationResult(
            success=False,
            allocations=[],
            portfolio_duration=0.0,
            portfolio_return=0.0,
            expected_future_value=0.0,
            message=message,
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

    # 듀레이션 매칭 사후 검증
    duration_gap = abs(portfolio_duration - T_years)
    if duration_gap > epsilon + 0.01:
        return OptimizationResult(
            success=False,
            allocations=allocations,
            portfolio_duration=round(portfolio_duration, 4),
            portfolio_return=round(portfolio_return, 6),
            expected_future_value=0.0,
            message=f"듀레이션 매칭 검증 실패: 갭 {duration_gap:.2f}년 (허용 {epsilon}년)",
        )

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
