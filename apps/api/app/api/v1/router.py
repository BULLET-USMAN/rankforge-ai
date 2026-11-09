from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_recommendations,
    audits,
    crawls,
    google_oauth,
    invitations,
    me,
    members,
    organizations,
    projects,
    seo_audits,
    verification,
    websites,
    worker,
)

api_router = APIRouter()

# Authenticated profile
api_router.include_router(me.router, prefix="/me", tags=["Profile"])

# Organizations
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])

# Organization-scoped resources (Members, Websites, Invitations, Verification, Crawls, SEO Audits, AI)
api_router.include_router(members.router, tags=["Workspace Members"])
api_router.include_router(websites.router, tags=["Website Projects"])
api_router.include_router(invitations.router, tags=["Invitations"])
api_router.include_router(verification.router, tags=["Domain Verification"])
api_router.include_router(crawls.router, tags=["Website Crawler"])
api_router.include_router(seo_audits.router, tags=["SEO Technical Audits"])
api_router.include_router(ai_recommendations.router, tags=["AI Optimization"])

# Integrations (Google Search Console OAuth2)
api_router.include_router(google_oauth.router)

# Phase 1 Legacy routes (Projects, Audits, Worker) preserved for backward compatibility
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(audits.router, prefix="/audits", tags=["Audits"])
api_router.include_router(worker.router, prefix="/worker", tags=["Worker"])
