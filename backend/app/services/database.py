import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite

from app.config import get_settings


class DatabaseService:
    """SQLite database service for caching and analytics."""

    _db_path: str | None = None

    @classmethod
    def _get_db_path(cls) -> str:
        if cls._db_path is None:
            cls._db_path = get_settings().database_path
        return cls._db_path

    @classmethod
    async def _get_db(cls) -> aiosqlite.Connection:
        db = await aiosqlite.connect(cls._get_db_path())
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        return db

    @classmethod
    async def initialize(cls) -> None:
        """Create tables on app startup."""
        db_path = Path(cls._get_db_path())
        db_path.parent.mkdir(parents=True, exist_ok=True)

        db = await cls._get_db()
        try:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS articles (
                    pmid TEXT PRIMARY KEY,
                    pmcid TEXT,
                    doi TEXT,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL DEFAULT '',
                    authors TEXT NOT NULL DEFAULT '[]',
                    journal TEXT NOT NULL DEFAULT '',
                    pub_date TEXT NOT NULL DEFAULT '',
                    full_text TEXT,
                    has_full_text INTEGER NOT NULL DEFAULT 0,
                    cached_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS citation_metrics (
                    pmid TEXT PRIMARY KEY,
                    citation_count INTEGER NOT NULL DEFAULT 0,
                    citations_per_year REAL,
                    relative_citation_ratio REAL,
                    nih_percentile REAL,
                    expected_citations REAL,
                    field_citation_rate REAL,
                    cached_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS translations (
                    id TEXT PRIMARY KEY,
                    pmid TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    translated_title TEXT NOT NULL DEFAULT '',
                    translated_abstract TEXT NOT NULL DEFAULT '',
                    cached_at TEXT NOT NULL,
                    UNIQUE(pmid, target_language)
                );

                CREATE TABLE IF NOT EXISTS summaries (
                    id TEXT PRIMARY KEY,
                    pmid TEXT NOT NULL,
                    knowledge_level TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    key_findings TEXT NOT NULL DEFAULT '[]',
                    context TEXT NOT NULL DEFAULT '',
                    acronyms TEXT NOT NULL DEFAULT '[]',
                    cached_at TEXT NOT NULL,
                    UNIQUE(pmid, knowledge_level)
                );

                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    pmid TEXT,
                    options TEXT,
                    cache_hit INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bad_output_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pmid TEXT NOT NULL,
                    result_type TEXT NOT NULL,
                    result_id TEXT,
                    target_language TEXT,
                    knowledge_level TEXT,
                    comment TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_usage_log_event_type ON usage_log(event_type);
                CREATE INDEX IF NOT EXISTS idx_usage_log_created_at ON usage_log(created_at);
                CREATE INDEX IF NOT EXISTS idx_usage_log_pmid ON usage_log(pmid);
                CREATE INDEX IF NOT EXISTS idx_bad_output_reports_pmid ON bad_output_reports(pmid);
            """)
            await db.commit()
        finally:
            await db.close()

    # ---- Article cache ----

    @classmethod
    async def get_cached_article(cls, pmid: str) -> dict | None:
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM articles WHERE pmid = ?", (pmid,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "pmid": row["pmid"],
                "pmcid": row["pmcid"],
                "doi": row["doi"],
                "title": row["title"],
                "abstract": row["abstract"],
                "authors": json.loads(row["authors"]),
                "journal": row["journal"],
                "pub_date": row["pub_date"],
                "full_text": row["full_text"],
                "has_full_text": bool(row["has_full_text"]),
                "cached_at": row["cached_at"],
            }
        finally:
            await db.close()

    @classmethod
    async def cache_article(cls, article: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        db = await cls._get_db()
        try:
            await db.execute(
                """INSERT OR REPLACE INTO articles
                   (pmid, pmcid, doi, title, abstract, authors, journal, pub_date, full_text, has_full_text, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    article["pmid"],
                    article.get("pmcid"),
                    article.get("doi"),
                    article["title"],
                    article["abstract"],
                    json.dumps(article["authors"]),
                    article["journal"],
                    article["pub_date"],
                    article.get("full_text"),
                    1 if article.get("has_full_text") or article.get("full_text") else 0,
                    now,
                ),
            )
            await db.commit()
        finally:
            await db.close()

    # ---- Citation metrics cache ----

    @classmethod
    async def get_cached_citation_metrics(cls, pmid: str) -> dict | None:
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM citation_metrics WHERE pmid = ?", (pmid,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            # 30-day TTL check
            cached_at = datetime.fromisoformat(row["cached_at"])
            if datetime.now(timezone.utc) - cached_at > timedelta(days=30):
                await db.execute("DELETE FROM citation_metrics WHERE pmid = ?", (pmid,))
                await db.commit()
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
        finally:
            await db.close()

    @classmethod
    async def cache_citation_metrics(cls, pmid: str, metrics: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        db = await cls._get_db()
        try:
            await db.execute(
                """INSERT OR REPLACE INTO citation_metrics
                   (pmid, citation_count, citations_per_year, relative_citation_ratio,
                    nih_percentile, expected_citations, field_citation_rate, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pmid,
                    metrics.get("citation_count", 0),
                    metrics.get("citations_per_year"),
                    metrics.get("relative_citation_ratio"),
                    metrics.get("nih_percentile"),
                    metrics.get("expected_citations"),
                    metrics.get("field_citation_rate"),
                    now,
                ),
            )
            await db.commit()
        finally:
            await db.close()

    # ---- Translation cache ----

    @classmethod
    async def get_cached_translation(cls, pmid: str, target_language: str) -> dict | None:
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM translations WHERE pmid = ? AND target_language = ?",
                (pmid, target_language),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "pmid": row["pmid"],
                "target_language": row["target_language"],
                "translated_title": row["translated_title"],
                "translated_abstract": row["translated_abstract"],
                "cached_at": row["cached_at"],
            }
        finally:
            await db.close()

    @classmethod
    async def cache_translation(cls, pmid: str, target_language: str, result: dict) -> str:
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db = await cls._get_db()
        try:
            await db.execute(
                """INSERT OR REPLACE INTO translations
                   (id, pmid, target_language, translated_title, translated_abstract, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    result_id,
                    pmid,
                    target_language,
                    result.get("translated_title", ""),
                    result.get("translated_abstract", ""),
                    now,
                ),
            )
            await db.commit()
        finally:
            await db.close()
        return result_id

    # ---- Summary cache ----

    @classmethod
    async def get_cached_summary(cls, pmid: str, knowledge_level: str) -> dict | None:
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM summaries WHERE pmid = ? AND knowledge_level = ?",
                (pmid, knowledge_level),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "pmid": row["pmid"],
                "knowledge_level": row["knowledge_level"],
                "summary": row["summary"],
                "key_findings": json.loads(row["key_findings"]),
                "context": row["context"],
                "acronyms": json.loads(row["acronyms"]),
                "cached_at": row["cached_at"],
            }
        finally:
            await db.close()

    @classmethod
    async def cache_summary(cls, pmid: str, knowledge_level: str, result: dict) -> str:
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db = await cls._get_db()
        try:
            await db.execute(
                """INSERT OR REPLACE INTO summaries
                   (id, pmid, knowledge_level, summary, key_findings, context, acronyms, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result_id,
                    pmid,
                    knowledge_level,
                    result.get("summary", ""),
                    json.dumps(result.get("key_findings", [])),
                    result.get("context", ""),
                    json.dumps(result.get("acronyms", [])),
                    now,
                ),
            )
            await db.commit()
        finally:
            await db.close()
        return result_id

    # ---- Usage logging ----

    @classmethod
    async def log_usage(
        cls,
        event_type: str,
        pmid: str | None = None,
        options: dict | None = None,
        cache_hit: bool = False,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        db = await cls._get_db()
        try:
            await db.execute(
                """INSERT INTO usage_log (event_type, pmid, options, cache_hit, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    event_type,
                    pmid,
                    json.dumps(options) if options else None,
                    1 if cache_hit else 0,
                    now,
                ),
            )
            await db.commit()
        finally:
            await db.close()

    # ---- Bad output reports ----

    @classmethod
    async def report_bad_output(
        cls,
        pmid: str,
        result_type: str,
        result_id: str | None = None,
        target_language: str | None = None,
        knowledge_level: str | None = None,
        comment: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        db = await cls._get_db()
        try:
            await db.execute(
                """INSERT INTO bad_output_reports
                   (pmid, result_type, result_id, target_language, knowledge_level, comment, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (pmid, result_type, result_id, target_language, knowledge_level, comment, now),
            )
            await db.commit()
        finally:
            await db.close()

    @classmethod
    async def invalidate_translation(cls, pmid: str, target_language: str) -> None:
        db = await cls._get_db()
        try:
            await db.execute(
                "DELETE FROM translations WHERE pmid = ? AND target_language = ?",
                (pmid, target_language),
            )
            await db.commit()
        finally:
            await db.close()

    @classmethod
    async def invalidate_summary(cls, pmid: str, knowledge_level: str) -> None:
        db = await cls._get_db()
        try:
            await db.execute(
                "DELETE FROM summaries WHERE pmid = ? AND knowledge_level = ?",
                (pmid, knowledge_level),
            )
            await db.commit()
        finally:
            await db.close()

    # ---- Analytics queries ----

    @classmethod
    async def get_most_popular_articles(cls, limit: int = 20) -> list[dict]:
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                """SELECT pmid, COUNT(*) as request_count
                   FROM usage_log
                   WHERE pmid IS NOT NULL
                   GROUP BY pmid
                   ORDER BY request_count DESC
                   LIMIT ?""",
                (limit,),
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                # Fetch article title if cached
                art_cursor = await db.execute(
                    "SELECT title FROM articles WHERE pmid = ?", (row["pmid"],)
                )
                art_row = await art_cursor.fetchone()
                results.append({
                    "pmid": row["pmid"],
                    "title": art_row["title"] if art_row else None,
                    "request_count": row["request_count"],
                })
            return results
        finally:
            await db.close()

    @classmethod
    async def get_option_usage_stats(cls) -> dict:
        db = await cls._get_db()
        try:
            # Count by event type
            cursor = await db.execute(
                """SELECT event_type, COUNT(*) as count
                   FROM usage_log
                   GROUP BY event_type"""
            )
            event_counts = {row["event_type"]: row["count"] for row in await cursor.fetchall()}

            # Count translation languages
            cursor = await db.execute(
                """SELECT json_extract(options, '$.target_language') as lang, COUNT(*) as count
                   FROM usage_log
                   WHERE event_type = 'translate' AND options IS NOT NULL
                   GROUP BY lang
                   ORDER BY count DESC"""
            )
            language_counts = {
                row["lang"]: row["count"]
                for row in await cursor.fetchall()
                if row["lang"]
            }

            # Count knowledge levels
            cursor = await db.execute(
                """SELECT json_extract(options, '$.knowledge_level') as level, COUNT(*) as count
                   FROM usage_log
                   WHERE event_type = 'summarize' AND options IS NOT NULL
                   GROUP BY level
                   ORDER BY count DESC"""
            )
            level_counts = {
                row["level"]: row["count"]
                for row in await cursor.fetchall()
                if row["level"]
            }

            return {
                "event_types": event_counts,
                "languages": language_counts,
                "knowledge_levels": level_counts,
            }
        finally:
            await db.close()

    @classmethod
    async def get_cache_hit_rates(cls) -> dict:
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                """SELECT event_type,
                          COUNT(*) as total,
                          SUM(cache_hit) as hits
                   FROM usage_log
                   GROUP BY event_type"""
            )
            rates = {}
            for row in await cursor.fetchall():
                total = row["total"]
                hits = row["hits"] or 0
                rates[row["event_type"]] = {
                    "total": total,
                    "hits": hits,
                    "misses": total - hits,
                    "hit_rate": round(hits / total, 4) if total > 0 else 0,
                }
            return rates
        finally:
            await db.close()

    @classmethod
    async def get_recent_bad_reports(cls, limit: int = 50) -> list[dict]:
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                """SELECT * FROM bad_output_reports
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "pmid": row["pmid"],
                    "result_type": row["result_type"],
                    "result_id": row["result_id"],
                    "target_language": row["target_language"],
                    "knowledge_level": row["knowledge_level"],
                    "comment": row["comment"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        finally:
            await db.close()

    @classmethod
    async def get_usage_over_time(cls, days: int = 30) -> list[dict]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        db = await cls._get_db()
        try:
            cursor = await db.execute(
                """SELECT DATE(created_at) as date, event_type, COUNT(*) as count
                   FROM usage_log
                   WHERE created_at >= ?
                   GROUP BY date, event_type
                   ORDER BY date""",
                (cutoff,),
            )
            rows = await cursor.fetchall()
            return [
                {"date": row["date"], "event_type": row["event_type"], "count": row["count"]}
                for row in rows
            ]
        finally:
            await db.close()

    @classmethod
    async def get_total_stats(cls) -> dict:
        db = await cls._get_db()
        try:
            stats = {}

            cursor = await db.execute("SELECT COUNT(*) as c FROM articles")
            stats["cached_articles"] = (await cursor.fetchone())["c"]

            cursor = await db.execute("SELECT COUNT(*) as c FROM translations")
            stats["cached_translations"] = (await cursor.fetchone())["c"]

            cursor = await db.execute("SELECT COUNT(*) as c FROM summaries")
            stats["cached_summaries"] = (await cursor.fetchone())["c"]

            cursor = await db.execute("SELECT COUNT(*) as c FROM usage_log")
            stats["total_requests"] = (await cursor.fetchone())["c"]

            cursor = await db.execute("SELECT COUNT(*) as c FROM bad_output_reports")
            stats["total_bad_reports"] = (await cursor.fetchone())["c"]

            cursor = await db.execute(
                "SELECT COUNT(DISTINCT pmid) as c FROM usage_log WHERE pmid IS NOT NULL"
            )
            stats["unique_articles_requested"] = (await cursor.fetchone())["c"]

            return stats
        finally:
            await db.close()
