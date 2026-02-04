from fastapi import APIRouter, Depends, Query

from app.dependencies import require_analytics_api_key
from app.services.database import DatabaseService

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_analytics_api_key)],
)


@router.get("/popular-articles")
async def popular_articles(limit: int = Query(default=20, ge=1, le=100)):
    """Most frequently requested articles."""
    return await DatabaseService.get_most_popular_articles(limit)


@router.get("/option-usage")
async def option_usage():
    """Usage breakdown by event type, language, and knowledge level."""
    return await DatabaseService.get_option_usage_stats()


@router.get("/cache-stats")
async def cache_stats():
    """Cache hit/miss rates by event type."""
    return await DatabaseService.get_cache_hit_rates()


@router.get("/bad-reports")
async def bad_reports(limit: int = Query(default=50, ge=1, le=200)):
    """Recent bad output reports."""
    return await DatabaseService.get_recent_bad_reports(limit)


@router.get("/usage-over-time")
async def usage_over_time(days: int = Query(default=30, ge=1, le=365)):
    """Daily usage counts over the specified number of days."""
    return await DatabaseService.get_usage_over_time(days)


@router.get("/summary")
async def analytics_summary():
    """High-level statistics: cached items, total requests, etc."""
    return await DatabaseService.get_total_stats()
