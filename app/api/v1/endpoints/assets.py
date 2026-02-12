from fastapi import APIRouter, Query

from app.models.asset import Asset
from app.services.asset_universe import get_default_universe

router = APIRouter()


@router.get("/assets", response_model=list[Asset])
def list_assets(
    eligible_youth_savings: bool = Query(default=False, description="청년도약저축 자격 여부"),
) -> list[Asset]:
    """Phase 3: 자산 유니버스를 조회한다."""
    return get_default_universe(eligible_youth_savings)
