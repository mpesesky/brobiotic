from fastapi import Header, HTTPException

from app.config import get_settings


async def require_analytics_api_key(x_api_key: str = Header(default="")) -> None:
    """Require a valid API key for analytics endpoints.

    If ANALYTICS_API_KEY is not configured (empty), all requests are allowed
    for local development convenience. When configured, the request must
    include a matching X-API-Key header.
    """
    settings = get_settings()
    if not settings.analytics_api_key:
        return
    if x_api_key != settings.analytics_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
