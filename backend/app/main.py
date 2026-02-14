from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, articles, analytics, admin
from app.services.database import DatabaseService

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    await DatabaseService.initialize()
    yield
    await DatabaseService.shutdown()


app = FastAPI(
    title=settings.app_name,
    description="Translate and summarize PubMed articles using Claude AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
    }
