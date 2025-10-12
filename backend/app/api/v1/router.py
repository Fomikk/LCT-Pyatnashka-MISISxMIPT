from fastapi import APIRouter
from app.api.v1 import routes_analysis, routes_recommend, routes_ddl, routes_pipelines, routes_health


api_router = APIRouter()

api_router.include_router(routes_health.router, prefix="/health", tags=["health"])
api_router.include_router(routes_analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(routes_recommend.router, prefix="/recommend", tags=["recommend"])
api_router.include_router(routes_ddl.router, prefix="/ddl", tags=["ddl"])
api_router.include_router(routes_pipelines.router, prefix="/pipelines", tags=["pipelines"])


