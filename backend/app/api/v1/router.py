"""
API v1 Router - aggregates all v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import auth, projects, images, analysis

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["Projects"],
)

api_router.include_router(
    images.router,
    prefix="/projects/{project_id}/images",
    tags=["Images"],
)

api_router.include_router(
    analysis.router,
    prefix="/projects/{project_id}/analysis",
    tags=["Analysis"],
)
