from pydantic import BaseModel, Field


class GoalInput(BaseModel):
    goal_amount: float = Field(..., gt=0, description="목표 금액 (원)")
    time_horizon_months: int = Field(..., gt=0, description="목표 기간 (개월)")
    monthly_contribution: float = Field(..., gt=0, description="월 저축 가능액 (원)")
    initial_principal: float = Field(default=0, ge=0, description="초기 자본 (원)")
    eligible_youth_savings: bool = Field(default=False, description="청년도약저축 가입 자격 여부")
