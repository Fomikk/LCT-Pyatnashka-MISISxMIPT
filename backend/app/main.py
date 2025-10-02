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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Статические файлы для простого UI
    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(api_router, prefix="/api/v1")

    app.include_router(ml_router, prefix="/ml")

    @app.get("/")
    async def root():
        return {"message": "ETL AI Assistant Backend", "docs": "/api/docs", "ui": "/static/index.html"}

    return app


app = create_app()


