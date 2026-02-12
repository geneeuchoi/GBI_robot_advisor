from pydantic import BaseModel, Field


class GapAnalysisResult(BaseModel):
    future_value_safe: float = Field(..., description="안전자산 적금 미래가치 (원)")
    goal_amount: float = Field(..., description="목표 금액 (원)")
    gap: float = Field(..., description="부족액 (원), 0이면 달성 가능")
    optimization_needed: bool = Field(..., description="최적화 필요 여부")
    required_annual_return: float | None = Field(
        default=None, description="목표 달성 최소 연 수익률"
    )
    goal_achievable: bool = Field(
        default=True,
        description="목표 달성 가능 여부 (100% 수익률로도 불가능하면 False)",
    )
