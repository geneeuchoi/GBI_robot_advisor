from pydantic import BaseModel, Field


class RateScenario(BaseModel):
    label: str = Field(..., description="시나리오 이름")
    rate_shift: float = Field(..., description="금리 변동폭 (예: -0.015)")


class SimulationRequest(BaseModel):
    goal_amount: float = Field(..., gt=0)
    time_horizon_months: int = Field(..., gt=0)
    monthly_contribution: float = Field(..., gt=0)
    initial_principal: float = Field(default=0, ge=0)
    eligible_youth_savings: bool = Field(default=False)
    scenarios: list[RateScenario] | None = Field(
        default=None, description="커스텀 시나리오 (None이면 기본 4개)"
    )


class ScenarioResult(BaseModel):
    label: str
    rate_shift: float
    new_rate: float = Field(..., description="변동 후 금리")
    simple_savings_fv: float = Field(..., description="단순 적금 최종액")
    portfolio_fv: float = Field(..., description="GBI 포트폴리오 최종액")
    difference: float = Field(..., description="차이 (포트폴리오 - 적금)")


class SimulationResponse(BaseModel):
    base_rate: float
    results: list[ScenarioResult]
