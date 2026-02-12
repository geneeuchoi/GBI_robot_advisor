import numpy as np


def macaulay_duration(
    cash_flows: list[float], periods: list[float], ytm: float
) -> float:
    """매콜리 듀레이션을 계산한다.

    D_mac = Σ(t × CF_t / (1+y)^t) / Σ(CF_t / (1+y)^t)

    Args:
        cash_flows: 각 시점의 현금 흐름
        periods: 각 현금 흐름의 시점 (년)
        ytm: 만기 수익률 (연율)

    Returns:
        매콜리 듀레이션 (년)

    Raises:
        ValueError: 유효하지 않은 입력값인 경우
    """
    if not cash_flows or not periods:
        return 0.0

    if len(cash_flows) != len(periods):
        raise ValueError("cash_flows와 periods의 길이가 다릅니다.")

    if ytm <= -1:
        raise ValueError(f"YTM({ytm})이 -1 이하입니다. 할인율을 확인하세요.")

    cf = np.array(cash_flows)
    t = np.array(periods)

    discount_factors = (1 + ytm) ** t
    pv = cf / discount_factors

    total_pv = pv.sum()
    if total_pv == 0:
        return 0.0

    return float((t * pv).sum() / total_pv)
