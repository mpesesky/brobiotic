from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import require_analytics_api_key
from app.services.database import DatabaseService

router = APIRouter(prefix="/admin", tags=["admin"])


class QueryRequest(BaseModel):
    sql: str


@router.post("/query", dependencies=[Depends(require_analytics_api_key)])
async def run_query(request: QueryRequest):
    """Execute a read-only SQL query against the database."""
    pool = await DatabaseService._get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET TRANSACTION READ ONLY")
            try:
                stmt = await conn.prepare(request.sql)
                columns = [attr.name for attr in stmt.get_attributes()]
                rows = await stmt.fetch()
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    return {
        "columns": columns,
        "rows": [list(row.values()) for row in rows],
    }
