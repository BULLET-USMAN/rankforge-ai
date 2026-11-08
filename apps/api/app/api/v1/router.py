from fastapi import APIRouter

from app.api.v1.endpoints import audits, organizations, projects, worker

api_router = APIRouter()

# Health endpoints at root level (/health/live, /health/ready)
# Organizations
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
# Projects
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
# Audits
api_router.include_router(audits.router, prefix="/audits", tags=["Audits"])
# Worker
api_router.include_router(worker.router, prefix="/worker", tags=["Worker"])
