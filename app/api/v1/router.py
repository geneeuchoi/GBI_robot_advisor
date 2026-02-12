from fastapi import APIRouter

from app.api.v1.endpoints import assets, gap, optimize, simulate

router = APIRouter(prefix="/api/v1")
router.include_router(gap.router, tags=["gap-analysis"])
router.include_router(assets.router, tags=["assets"])
router.include_router(optimize.router, tags=["optimize"])
router.include_router(simulate.router, tags=["simulate"])
