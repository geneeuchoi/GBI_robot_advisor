import pytest

from app.models.asset import TaxBenefit
from app.services.tax import after_tax_return


class TestAfterTaxReturn:
    def test_tax_free(self):
        result = after_tax_return(0.06, TaxBenefit.TAX_FREE)
        assert result == 0.06

    def test_separate_tax(self):
        result = after_tax_return(0.035, TaxBenefit.SEPARATE_TAX)
        expected = 0.035 * (1 - 0.099)
        assert abs(result - expected) < 1e-10

    def test_normal_tax(self):
        result = after_tax_return(0.033, TaxBenefit.NONE)
        expected = 0.033 * (1 - 0.154)
        assert abs(result - expected) < 1e-10

    def test_zero_return(self):
        assert after_tax_return(0.0, TaxBenefit.NONE) == 0.0
