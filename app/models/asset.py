from enum import Enum

from pydantic import BaseModel, Field


class TaxBenefit(str, Enum):
    NONE = "none"
    TAX_FREE = "tax_free"  # 비과세
    SEPARATE_TAX = "separate_tax"  # 분리과세 (ISA)


class AssetClass(str, Enum):
    PARKING = "parking"  # 파킹통장/CMA
    YOUTH_SAVINGS = "youth_savings"  # 청년도약저축
    ISA_DEPOSIT = "isa_deposit"  # ISA 내 예금
    TIME_DEPOSIT = "time_deposit"  # 정기예금
    BOND_ETF_3Y = "bond_etf_3y"  # 국고채 3년 ETF
    BOND_ETF_10Y = "bond_etf_10y"  # 국고채 10년 ETF


class Asset(BaseModel):
    name: str = Field(..., description="상품명")
    asset_class: AssetClass
    gross_return: float = Field(..., description="세전 기대 수익률")
    duration: float = Field(..., ge=0, description="매콜리 듀레이션 (년)")
    tax_benefit: TaxBenefit = Field(default=TaxBenefit.NONE)
    monthly_limit: float | None = Field(default=None, description="월 납입 한도 (원)")
    annual_limit: float | None = Field(default=None, description="연간 납입 한도 (원)")
