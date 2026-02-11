"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import ai, applications, jobs, profile, sources, stats

app = FastAPI(
    title="JobHunter Pro",
    description="AI-powered remote job search automation API",
    version="0.1.0",
)

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


# Serve frontend static files in production
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="spa")
