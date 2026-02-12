import math

from scipy.optimize import brentq

from app.config import settings
from app.models.gap import GapAnalysisResult
from app.models.goal import GoalInput


def _future_value(principal: float, monthly: float, annual_rate: float, months: int) -> float:
    """월복리 미래가치를 계산한다.

    FV = P0 × (1 + r_m)^n + C × [((1 + r_m)^n - 1) / r_m]
    """
    if months <= 0:
        return principal

    if annual_rate == 0:
        return principal + monthly * months

    r_m = annual_rate / 12

    # r_m이 -1에 가까우면 수치 불안정 → 단순 합산으로 대체
    if r_m <= -1:
        return principal + monthly * months

    try:
        compound = (1 + r_m) ** months
    except OverflowError:
        return math.inf

    fv_principal = principal * compound
    fv_annuity = monthly * ((compound - 1) / r_m)
    return fv_principal + fv_annuity


def analyze_gap(
    goal: GoalInput, safe_rate: float | None = None
) -> GapAnalysisResult:
    """Phase 2: 갭 분석 및 필요 수익률을 산출한다."""
    if safe_rate is None:
        safe_rate = settings.base_interest_rate

    fv_safe = _future_value(
        goal.initial_principal,
        goal.monthly_contribution,
        safe_rate,
        goal.time_horizon_months,
    )

    gap = max(0, goal.goal_amount - fv_safe)
    optimization_needed = gap > 0

    required_return: float | None = None
    goal_achievable = True

    if optimization_needed:
        def _fv_diff(r: float) -> float:
            return (
                _future_value(
                    goal.initial_principal,
                    goal.monthly_contribution,
                    r,
                    goal.time_horizon_months,
                )
                - goal.goal_amount
            )

        # brentq 호출 전에 구간 양 끝값의 부호가 다른지 확인
        f_low = _fv_diff(0.0)
        f_high = _fv_diff(1.0)  # 100% 수익률

        if f_low >= 0:
            # 0% 수익률로도 달성 가능 (초기자본이 충분한 경우)
            required_return = 0.0
        elif f_high < 0:
            # 100% 수익률로도 목표 미달 → 달성 불가능
            goal_achievable = False
            required_return = None
        else:
            try:
                required_return = brentq(_fv_diff, 0.0, 1.0, xtol=1e-8)
            except ValueError:
                goal_achievable = False
                required_return = None

    return GapAnalysisResult(
        future_value_safe=round(fv_safe, 0),
        goal_amount=goal.goal_amount,
        gap=round(gap, 0),
        optimization_needed=optimization_needed,
        required_annual_return=required_return,
        goal_achievable=goal_achievable,
    )
