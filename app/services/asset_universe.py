from app.config import settings
from app.models.asset import Asset, AssetClass, TaxBenefit


def get_default_universe(eligible_youth_savings: bool = False) -> list[Asset]:
    """Phase 3: 사회초년생이 접근 가능한 자산 유니버스를 반환한다."""
    assets: list[Asset] = [
        Asset(
            name="파킹통장/CMA",
            asset_class=AssetClass.PARKING,
            gross_return=0.030,
            duration=0.0,
            tax_benefit=TaxBenefit.NONE,
        ),
        Asset(
            name="ISA 내 예금",
            asset_class=AssetClass.ISA_DEPOSIT,
            gross_return=0.035,
            duration=1.0,
            tax_benefit=TaxBenefit.SEPARATE_TAX,
            annual_limit=settings.isa_annual_limit,
        ),
        Asset(
            name="정기예금 (1년)",
            asset_class=AssetClass.TIME_DEPOSIT,
            gross_return=0.033,
            duration=1.0,
            tax_benefit=TaxBenefit.NONE,
        ),
        Asset(
            name="KODEX 국고채 3년 ETF",
            asset_class=AssetClass.BOND_ETF_3Y,
            gross_return=0.038,
            duration=2.7,
            tax_benefit=TaxBenefit.NONE,
        ),
        Asset(
            name="KODEX 국고채 10년 ETF",
            asset_class=AssetClass.BOND_ETF_10Y,
            gross_return=0.042,
            duration=7.8,
            tax_benefit=TaxBenefit.NONE,
        ),
    ]

    if eligible_youth_savings:
        assets.insert(
            1,
            Asset(
                name="청년도약저축",
                asset_class=AssetClass.YOUTH_SAVINGS,
                gross_return=0.06 + settings.youth_savings_gov_contribution_rate,
                duration=2.5,
                tax_benefit=TaxBenefit.TAX_FREE,
                monthly_limit=settings.youth_savings_monthly_limit,
            ),
        )

    return assets
