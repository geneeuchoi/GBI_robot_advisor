from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.router import router as v1_router

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI(
        title="GBI 로보 어드바이저",
        description="듀레이션 매칭 기반 사회초년생 맞춤 로보 어드바이저 엔진",
        version="0.1.0",
    )
    app.include_router(v1_router)
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    templates = Jinja2Templates(directory=BASE_DIR / "templates")

    @app.get("/", include_in_schema=False)
    def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    return app


app = create_app()
