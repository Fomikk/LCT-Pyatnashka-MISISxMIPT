# backend/app/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.router import api_router
from ml.api.service import router as ml_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ETL AI Assistant Backend",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,   # или settings.cors_origins (есть совместимостьное свойство)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- STATIC (опционально) ---
    # Статика ожидается в backend/static (рядом с backend/app)
    base_dir = Path(__file__).resolve().parent.parent      # backend/
    static_dir = base_dir / "static"                       # backend/static
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    # иначе просто не монтируем — и не падаем

    # API
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(ml_router, prefix="/api/ml")

    @app.get("/")
    async def root():
        # ui откроется, только если статическая папка действительно смонтирована
        return {"message": "ETL AI Assistant Backend", "docs": "/api/docs", "ui": "/static/index.html"}

    return app


app = create_app()
