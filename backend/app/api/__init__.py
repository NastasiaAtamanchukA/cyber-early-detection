from fastapi import APIRouter

from app.api import alerts, collectors, dashboard, events, health, incidents

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(events.router)
api_router.include_router(alerts.router)
api_router.include_router(incidents.router)
api_router.include_router(collectors.router)
