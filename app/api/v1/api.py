from fastapi import APIRouter
from app.api.routers import calls, health, metrics

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(calls.router, tags=["calls"])
