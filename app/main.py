from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1.router import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="GBI 로보 어드바이저",
        description="듀레이션 매칭 기반 사회초년생 맞춤 로보 어드바이저 엔진",
        version="0.1.0",
    )
    app.include_router(v1_router)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
