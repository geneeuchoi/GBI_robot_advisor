from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 기준 금리
    base_interest_rate: float = 0.035  # 3.5%

    # 듀레이션 매칭 허용 오차 (년)
    duration_epsilon: float = 0.5

    # 세율
    interest_income_tax_rate: float = 0.154  # 이자소득세 15.4%
    isa_separate_tax_rate: float = 0.099  # ISA 분리과세 9.9%

    # 청년도약저축
    youth_savings_monthly_limit: float = 70_0000  # 월 70만원
    youth_savings_gov_contribution_rate: float = 0.06  # 정부 기여 6%
    youth_savings_maturity_months: int = 60  # 5년 만기

    # ISA
    isa_annual_limit: float = 2000_0000  # 연 2,000만원

    model_config = {"env_prefix": "GBI_"}


settings = Settings()
