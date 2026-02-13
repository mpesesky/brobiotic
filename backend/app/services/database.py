import json
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg

from app.config import get_settings


class DatabaseService:
    """PostgreSQL database service for caching and analytics."""

    _pool: asyncpg.Pool | None = None

    @classmethod
    async def _get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            raise RuntimeError("DatabaseService not initialized — call initialize() first")
        return cls._pool

    @classmethod
    async def initialize(cls) -> None:
        """Create connection pool and tables on app startup."""
        settings = get_settings()
        cls._pool = await asyncpg.create_pool(settings.database_url)

        async with cls._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    article_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL DEFAULT 'pubmed',
                    pmcid TEXT,
                    doi TEXT,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL DEFAULT '',
                    authors JSONB NOT NULL DEFAULT '[]',
                    journal TEXT NOT NULL DEFAULT '',
                    pub_date TEXT NOT NULL DEFAULT '',
                    full_text TEXT,
                    has_full_text BOOLEAN NOT NULL DEFAULT FALSE,
                    cached_at TEXT NOT NULL
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS citation_metrics (
                    article_id TEXT PRIMARY KEY,
                    citation_count INTEGER NOT NULL DEFAULT 0,
                    citations_per_year DOUBLE PRECISION,
                    relative_citation_ratio DOUBLE PRECISION,
                    nih_percentile DOUBLE PRECISION,
                    expected_citations DOUBLE PRECISION,
                    field_citation_rate DOUBLE PRECISION,
                    cached_at TEXT NOT NULL
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id TEXT PRIMARY KEY,
                    article_id TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    translated_title TEXT NOT NULL DEFAULT '',
                    translated_abstract TEXT NOT NULL DEFAULT '',
                    cached_at TEXT NOT NULL,
                    UNIQUE(article_id, target_language)
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id TEXT PRIMARY KEY,
                    article_id TEXT NOT NULL,
                    knowledge_level TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    key_findings JSONB NOT NULL DEFAULT '[]',
                    context TEXT NOT NULL DEFAULT '',
                    acronyms JSONB NOT NULL DEFAULT '[]',
                    cached_at TEXT NOT NULL,
                    UNIQUE(article_id, knowledge_level)
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_log (
                    id SERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    article_id TEXT,
                    options JSONB,
                    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TEXT NOT NULL
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bad_output_reports (
                    id SERIAL PRIMARY KEY,
                    article_id TEXT NOT NULL,
                    result_type TEXT NOT NULL,
                    result_id TEXT,
                    target_language TEXT,
                    knowledge_level TEXT,
                    comment TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_usage_log_event_type ON usage_log(event_type)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_usage_log_created_at ON usage_log(created_at)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_usage_log_article_id ON usage_log(article_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_bad_output_reports_article_id ON bad_output_reports(article_id)"
            )

    @classmethod
    async def shutdown(cls) -> None:
        """Close the connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    # ---- Example articles ----

    @classmethod
    async def get_example_articles(cls, limit: int = 5) -> list[dict]:
        """Return random cached articles for the examples box."""
        pool = await cls._get_pool()
        rows = await pool.fetch(
            "SELECT article_id, title, source FROM articles ORDER BY RANDOM() LIMIT $1",
            limit,
        )
        return [
            {"article_id": row["article_id"], "title": row["title"], "source": row["source"]}
            for row in rows
        ]

    # ---- Article cache ----

    @classmethod
    async def get_cached_article(cls, article_id: str) -> dict | None:
        pool = await cls._get_pool()
        row = await pool.fetchrow(
            "SELECT * FROM articles WHERE article_id = $1", article_id
        )
        if row is None:
            return None
        return {
            "article_id": row["article_id"],
            "source": row["source"],
            "pmcid": row["pmcid"],
            "doi": row["doi"],
            "title": row["title"],
            "abstract": row["abstract"],
            "authors": json.loads(row["authors"]) if isinstance(row["authors"], str) else row["authors"],
            "journal": row["journal"],
            "pub_date": row["pub_date"],
            "full_text": row["full_text"],
            "has_full_text": row["has_full_text"],
            "cached_at": row["cached_at"],
        }

    @classmethod
    async def cache_article(cls, article: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        pool = await cls._get_pool()
        await pool.execute(
            """INSERT INTO articles
               (article_id, source, pmcid, doi, title, abstract, authors, journal, pub_date, full_text, has_full_text, cached_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
               ON CONFLICT (article_id) DO UPDATE SET
                   source = EXCLUDED.source,
                   pmcid = EXCLUDED.pmcid,
                   doi = EXCLUDED.doi,
                   title = EXCLUDED.title,
                   abstract = EXCLUDED.abstract,
                   authors = EXCLUDED.authors,
                   journal = EXCLUDED.journal,
                   pub_date = EXCLUDED.pub_date,
                   full_text = EXCLUDED.full_text,
                   has_full_text = EXCLUDED.has_full_text,
                   cached_at = EXCLUDED.cached_at""",
            article["article_id"],
            article.get("source", "pubmed"),
            article.get("pmcid"),
            article.get("doi"),
            article["title"],
            article["abstract"],
            json.dumps(article["authors"]),
            article["journal"],
            article["pub_date"],
            article.get("full_text"),
            bool(article.get("has_full_text") or article.get("full_text")),
            now,
        )

    # ---- Citation metrics cache ----

    @classmethod
    async def get_cached_citation_metrics(cls, article_id: str) -> dict | None:
        pool = await cls._get_pool()
        row = await pool.fetchrow(
            "SELECT * FROM citation_metrics WHERE article_id = $1", article_id
        )
        if row is None:
            return None
        # 30-day TTL check
        cached_at = datetime.fromisoformat(row["cached_at"])
        if datetime.now(timezone.utc) - cached_at > timedelta(days=30):
            await pool.execute("DELETE FROM citation_metrics WHERE article_id = $1", article_id)
            return None
        return {
            "citation_count": row["citation_count"],
            "citations_per_year": row["citations_per_year"],
            "relative_citation_ratio": row["relative_citation_ratio"],
            "nih_percentile": row["nih_percentile"],
            "expected_citations": row["expected_citations"],
            "field_citation_rate": row["field_citation_rate"],
            "cached_at": row["cached_at"],
        }

    @classmethod
    async def cache_citation_metrics(cls, article_id: str, metrics: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        pool = await cls._get_pool()
        await pool.execute(
            """INSERT INTO citation_metrics
               (article_id, citation_count, citations_per_year, relative_citation_ratio,
                nih_percentile, expected_citations, field_citation_rate, cached_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
               ON CONFLICT (article_id) DO UPDATE SET
                   citation_count = EXCLUDED.citation_count,
                   citations_per_year = EXCLUDED.citations_per_year,
                   relative_citation_ratio = EXCLUDED.relative_citation_ratio,
                   nih_percentile = EXCLUDED.nih_percentile,
                   expected_citations = EXCLUDED.expected_citations,
                   field_citation_rate = EXCLUDED.field_citation_rate,
                   cached_at = EXCLUDED.cached_at""",
            article_id,
            metrics.get("citation_count", 0),
            metrics.get("citations_per_year"),
            metrics.get("relative_citation_ratio"),
            metrics.get("nih_percentile"),
            metrics.get("expected_citations"),
            metrics.get("field_citation_rate"),
            now,
        )

    # ---- Translation cache ----

    @classmethod
    async def get_cached_translation(cls, article_id: str, target_language: str) -> dict | None:
        pool = await cls._get_pool()
        row = await pool.fetchrow(
            "SELECT * FROM translations WHERE article_id = $1 AND target_language = $2",
            article_id, target_language,
        )
        if row is None:
            return None
        return {
            "id": row["id"],
            "article_id": row["article_id"],
            "target_language": row["target_language"],
            "translated_title": row["translated_title"],
            "translated_abstract": row["translated_abstract"],
            "cached_at": row["cached_at"],
        }

    @classmethod
    async def cache_translation(cls, article_id: str, target_language: str, result: dict) -> str:
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        pool = await cls._get_pool()
        await pool.execute(
            """INSERT INTO translations
               (id, article_id, target_language, translated_title, translated_abstract, cached_at)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT (article_id, target_language) DO UPDATE SET
                   id = EXCLUDED.id,
                   translated_title = EXCLUDED.translated_title,
                   translated_abstract = EXCLUDED.translated_abstract,
                   cached_at = EXCLUDED.cached_at""",
            result_id,
            article_id,
            target_language,
            result.get("translated_title", ""),
            result.get("translated_abstract", ""),
            now,
        )
        return result_id

    # ---- Summary cache ----

    @classmethod
    async def get_cached_summary(cls, article_id: str, knowledge_level: str) -> dict | None:
        pool = await cls._get_pool()
        row = await pool.fetchrow(
            "SELECT * FROM summaries WHERE article_id = $1 AND knowledge_level = $2",
            article_id, knowledge_level,
        )
        if row is None:
            return None
        return {
            "id": row["id"],
            "article_id": row["article_id"],
            "knowledge_level": row["knowledge_level"],
            "summary": row["summary"],
            "key_findings": json.loads(row["key_findings"]) if isinstance(row["key_findings"], str) else row["key_findings"],
            "context": row["context"],
            "acronyms": json.loads(row["acronyms"]) if isinstance(row["acronyms"], str) else row["acronyms"],
            "cached_at": row["cached_at"],
        }

    @classmethod
    async def cache_summary(cls, article_id: str, knowledge_level: str, result: dict) -> str:
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        pool = await cls._get_pool()
        await pool.execute(
            """INSERT INTO summaries
               (id, article_id, knowledge_level, summary, key_findings, context, acronyms, cached_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
               ON CONFLICT (article_id, knowledge_level) DO UPDATE SET
                   id = EXCLUDED.id,
                   summary = EXCLUDED.summary,
                   key_findings = EXCLUDED.key_findings,
                   context = EXCLUDED.context,
                   acronyms = EXCLUDED.acronyms,
                   cached_at = EXCLUDED.cached_at""",
            result_id,
            article_id,
            knowledge_level,
            result.get("summary", ""),
            json.dumps(result.get("key_findings", [])),
            result.get("context", ""),
            json.dumps(result.get("acronyms", [])),
            now,
        )
        return result_id

    # ---- Usage logging ----

    @classmethod
    async def log_usage(
        cls,
        event_type: str,
        article_id: str | None = None,
        options: dict | None = None,
        cache_hit: bool = False,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        pool = await cls._get_pool()
        await pool.execute(
            """INSERT INTO usage_log (event_type, article_id, options, cache_hit, created_at)
               VALUES ($1, $2, $3, $4, $5)""",
            event_type,
            article_id,
            json.dumps(options) if options else None,
            cache_hit,
            now,
        )

    # ---- Bad output reports ----

    @classmethod
    async def report_bad_output(
        cls,
        article_id: str,
        result_type: str,
        result_id: str | None = None,
        target_language: str | None = None,
        knowledge_level: str | None = None,
        comment: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        pool = await cls._get_pool()
        await pool.execute(
            """INSERT INTO bad_output_reports
               (article_id, result_type, result_id, target_language, knowledge_level, comment, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            article_id, result_type, result_id, target_language, knowledge_level, comment, now,
        )

    @classmethod
    async def invalidate_translation(cls, article_id: str, target_language: str) -> None:
        pool = await cls._get_pool()
        await pool.execute(
            "DELETE FROM translations WHERE article_id = $1 AND target_language = $2",
            article_id, target_language,
        )

    @classmethod
    async def invalidate_summary(cls, article_id: str, knowledge_level: str) -> None:
        pool = await cls._get_pool()
        await pool.execute(
            "DELETE FROM summaries WHERE article_id = $1 AND knowledge_level = $2",
            article_id, knowledge_level,
        )

    # ---- Analytics queries ----

    @classmethod
    async def get_most_popular_articles(cls, limit: int = 20) -> list[dict]:
        pool = await cls._get_pool()
        rows = await pool.fetch(
            """SELECT u.article_id, COUNT(*) as request_count, a.title
               FROM usage_log u
               LEFT JOIN articles a ON a.article_id = u.article_id
               WHERE u.article_id IS NOT NULL
               GROUP BY u.article_id, a.title
               ORDER BY request_count DESC
               LIMIT $1""",
            limit,
        )
        return [
            {
                "article_id": row["article_id"],
                "title": row["title"],
                "request_count": row["request_count"],
            }
            for row in rows
        ]

    @classmethod
    async def get_option_usage_stats(cls) -> dict:
        pool = await cls._get_pool()

        # Count by event type
        rows = await pool.fetch(
            """SELECT event_type, COUNT(*) as count
               FROM usage_log
               GROUP BY event_type"""
        )
        event_counts = {row["event_type"]: row["count"] for row in rows}

        # Count translation languages
        rows = await pool.fetch(
            """SELECT options->>'target_language' as lang, COUNT(*) as count
               FROM usage_log
               WHERE event_type = 'translate' AND options IS NOT NULL
               GROUP BY lang
               ORDER BY count DESC"""
        )
        language_counts = {
            row["lang"]: row["count"]
            for row in rows
            if row["lang"]
        }

        # Count knowledge levels
        rows = await pool.fetch(
            """SELECT options->>'knowledge_level' as level, COUNT(*) as count
               FROM usage_log
               WHERE event_type = 'summarize' AND options IS NOT NULL
               GROUP BY level
               ORDER BY count DESC"""
        )
        level_counts = {
            row["level"]: row["count"]
            for row in rows
            if row["level"]
        }

        return {
            "event_types": event_counts,
            "languages": language_counts,
            "knowledge_levels": level_counts,
        }

    @classmethod
    async def get_cache_hit_rates(cls) -> dict:
        pool = await cls._get_pool()
        rows = await pool.fetch(
            """SELECT event_type,
                      COUNT(*) as total,
                      SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as hits
               FROM usage_log
               GROUP BY event_type"""
        )
        rates = {}
        for row in rows:
            total = row["total"]
            hits = row["hits"] or 0
            rates[row["event_type"]] = {
                "total": total,
                "hits": hits,
                "misses": total - hits,
                "hit_rate": round(hits / total, 4) if total > 0 else 0,
            }
        return rates

    @classmethod
    async def get_recent_bad_reports(cls, limit: int = 50) -> list[dict]:
        pool = await cls._get_pool()
        rows = await pool.fetch(
            """SELECT * FROM bad_output_reports
               ORDER BY created_at DESC
               LIMIT $1""",
            limit,
        )
        return [
            {
                "id": row["id"],
                "article_id": row["article_id"],
                "result_type": row["result_type"],
                "result_id": row["result_id"],
                "target_language": row["target_language"],
                "knowledge_level": row["knowledge_level"],
                "comment": row["comment"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    @classmethod
    async def get_usage_over_time(cls, days: int = 30) -> list[dict]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        pool = await cls._get_pool()
        rows = await pool.fetch(
            """SELECT DATE(created_at::timestamptz) as date, event_type, COUNT(*) as count
               FROM usage_log
               WHERE created_at >= $1
               GROUP BY date, event_type
               ORDER BY date""",
            cutoff,
        )
        return [
            {"date": str(row["date"]), "event_type": row["event_type"], "count": row["count"]}
            for row in rows
        ]

    @classmethod
    async def get_total_stats(cls) -> dict:
        pool = await cls._get_pool()
        stats = {}

        stats["cached_articles"] = await pool.fetchval("SELECT COUNT(*) FROM articles")
        stats["cached_translations"] = await pool.fetchval("SELECT COUNT(*) FROM translations")
        stats["cached_summaries"] = await pool.fetchval("SELECT COUNT(*) FROM summaries")
        stats["total_requests"] = await pool.fetchval("SELECT COUNT(*) FROM usage_log")
        stats["total_bad_reports"] = await pool.fetchval("SELECT COUNT(*) FROM bad_output_reports")
        stats["unique_articles_requested"] = await pool.fetchval(
            "SELECT COUNT(DISTINCT article_id) FROM usage_log WHERE article_id IS NOT NULL"
        )

        return stats
