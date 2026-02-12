from app.config import settings
from app.models.asset import TaxBenefit


def after_tax_return(gross_return: float, tax_benefit: TaxBenefit) -> float:
    """세후 수익률을 계산한다.

    - 비과세(TAX_FREE): 세금 없음
    - 분리과세(SEPARATE_TAX): ISA 분리과세율 적용
    - 일반(NONE): 이자소득세율 적용
    """
    if tax_benefit == TaxBenefit.TAX_FREE:
        return gross_return
    if tax_benefit == TaxBenefit.SEPARATE_TAX:
        return gross_return * (1 - settings.isa_separate_tax_rate)
    return gross_return * (1 - settings.interest_income_tax_rate)
