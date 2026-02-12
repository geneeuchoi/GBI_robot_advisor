from pydantic import BaseModel, Field

from app.models.asset import AssetClass


class AllocationItem(BaseModel):
    asset_class: AssetClass
    name: str
    weight: float = Field(..., ge=0, le=1, description="투자 비중")
    monthly_amount: float = Field(..., ge=0, description="월 투입액 (원)")
    duration_contribution: float = Field(..., description="듀레이션 기여 (년)")
    after_tax_return: float = Field(..., description="세후 수익률")


class OptimizationResult(BaseModel):
    success: bool
    allocations: list[AllocationItem]
    portfolio_duration: float = Field(..., description="포트폴리오 듀레이션 (년)")
    portfolio_return: float = Field(..., description="포트폴리오 가중 세후 수익률")
    expected_future_value: float = Field(..., description="예상 미래가치 (원)")
    message: str = Field(default="", description="결과 메시지")
