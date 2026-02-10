from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ArticleFetchRequest,
    ArticleFetchResponse,
    CitationMetricsResponse,
    KnowledgeLevel,
    ProcessRequest,
    ProcessResponse,
    ReportBadOutputRequest,
    ReportBadOutputResponse,
)
from app.services.identifier import parse_identifier, IdentifierType
from app.services.pubmed import PubMedClient, ArticleMetadata, CitationMetrics
from app.services.preprint import PreprintClient
from app.services.claude import ClaudeService
from app.services.database import DatabaseService

router = APIRouter(prefix="/articles", tags=["articles"])

# Identifier types that route to the preprint client
_PREPRINT_TYPES = {IdentifierType.ARXIV, IdentifierType.BIORXIV, IdentifierType.MEDRXIV}


def _is_preprint(identifier_type: IdentifierType) -> bool:
    return identifier_type in _PREPRINT_TYPES


def _build_article_metadata_from_cache(cached: dict) -> ArticleMetadata:
    """Reconstruct an ArticleMetadata from a cached article dict."""
    return ArticleMetadata(
        article_id=cached["article_id"],
        source=cached.get("source", "pubmed"),
        pmcid=cached.get("pmcid"),
        doi=cached.get("doi"),
        title=cached["title"],
        abstract=cached["abstract"],
        authors=cached["authors"],
        journal=cached["journal"],
        pub_date=cached["pub_date"],
        full_text=cached.get("full_text"),
        citation_metrics=None,
    )


def _citation_metrics_response(metrics) -> CitationMetricsResponse | None:
    """Convert citation metrics (dataclass or dict) to response model."""
    if metrics is None:
        return None
    if isinstance(metrics, dict):
        return CitationMetricsResponse(
            citation_count=metrics.get("citation_count", 0),
            citations_per_year=metrics.get("citations_per_year"),
            relative_citation_ratio=metrics.get("relative_citation_ratio"),
            nih_percentile=metrics.get("nih_percentile"),
            expected_citations=metrics.get("expected_citations"),
            field_citation_rate=metrics.get("field_citation_rate"),
        )
    return CitationMetricsResponse(
        citation_count=metrics.citation_count,
        citations_per_year=metrics.citations_per_year,
        relative_citation_ratio=metrics.relative_citation_ratio,
        nih_percentile=metrics.nih_percentile,
        expected_citations=metrics.expected_citations,
        field_citation_rate=metrics.field_citation_rate,
    )


def _article_to_cache_dict(article: ArticleMetadata) -> dict:
    """Convert ArticleMetadata to a dict suitable for caching."""
    return {
        "article_id": article.article_id,
        "source": article.source,
        "pmcid": article.pmcid,
        "doi": article.doi,
        "title": article.title,
        "abstract": article.abstract,
        "authors": article.authors,
        "journal": article.journal,
        "pub_date": article.pub_date,
        "full_text": article.full_text,
        "has_full_text": article.full_text is not None,
    }


async def _resolve_article_id(identifier: str) -> tuple[str, IdentifierType]:
    """Resolve an identifier string to an article_id and its type.

    For PubMed types (PMID, PMCID, DOI, TITLE), resolves to a PMID string.
    For preprint types, resolves to a prefixed ID like 'arxiv:2401.12345'.
    """
    parsed = parse_identifier(identifier)

    if _is_preprint(parsed.type):
        # For preprints, we need to fetch to get the canonical article_id
        # but we can construct it from the parsed value
        if parsed.type == IdentifierType.ARXIV:
            return f"arxiv:{parsed.value}", parsed.type
        elif parsed.type == IdentifierType.BIORXIV:
            return f"biorxiv:{parsed.value}", parsed.type
        elif parsed.type == IdentifierType.MEDRXIV:
            return f"medrxiv:{parsed.value}", parsed.type

    # PubMed path — resolve to PMID
    client = PubMedClient()
    try:
        pmid = await client.resolve_pmid(identifier)
        return pmid, parsed.type
    finally:
        await client.close()


async def _fetch_article_from_source(identifier: str) -> ArticleMetadata:
    """Fetch article from the appropriate source based on identifier type."""
    parsed = parse_identifier(identifier)

    if _is_preprint(parsed.type):
        client = PreprintClient()
        try:
            return await client.get_preprint(parsed)
        finally:
            await client.close()
    else:
        client = PubMedClient()
        try:
            return await client.get_article(identifier)
        finally:
            await client.close()


@router.post("/fetch", response_model=ArticleFetchResponse)
async def fetch_article(request: ArticleFetchRequest):
    """
    Fetch article metadata.

    Accepts PMID, PMCID, DOI, PubMed/PMC URL, arxiv/biorxiv/medrxiv URL, or article title.
    """
    try:
        # Resolve to article_id for cache lookup
        article_id, id_type = await _resolve_article_id(request.identifier)

        # Check article cache
        cached_article = await DatabaseService.get_cached_article(article_id)
        cached_metrics = await DatabaseService.get_cached_citation_metrics(article_id)

        if cached_article:
            await DatabaseService.log_usage("fetch", article_id=article_id, cache_hit=True)
            return ArticleFetchResponse(
                article_id=cached_article["article_id"],
                source=cached_article.get("source", "pubmed"),
                pmcid=cached_article.get("pmcid"),
                doi=cached_article.get("doi"),
                title=cached_article["title"],
                abstract=cached_article["abstract"],
                authors=cached_article["authors"],
                journal=cached_article["journal"],
                pub_date=cached_article["pub_date"],
                has_full_text=cached_article["has_full_text"],
                citation_metrics=_citation_metrics_response(cached_metrics),
                from_cache=True,
                cached_at=cached_article["cached_at"],
            )

        # Cache miss — fetch from source
        article = await _fetch_article_from_source(request.identifier)

        # Cache the article
        await DatabaseService.cache_article(_article_to_cache_dict(article))

        # Cache citation metrics (only for PubMed articles)
        citation_metrics = None
        if article.citation_metrics:
            await DatabaseService.cache_citation_metrics(article.article_id, {
                "citation_count": article.citation_metrics.citation_count,
                "citations_per_year": article.citation_metrics.citations_per_year,
                "relative_citation_ratio": article.citation_metrics.relative_citation_ratio,
                "nih_percentile": article.citation_metrics.nih_percentile,
                "expected_citations": article.citation_metrics.expected_citations,
                "field_citation_rate": article.citation_metrics.field_citation_rate,
            })
            citation_metrics = CitationMetricsResponse(
                citation_count=article.citation_metrics.citation_count,
                citations_per_year=article.citation_metrics.citations_per_year,
                relative_citation_ratio=article.citation_metrics.relative_citation_ratio,
                nih_percentile=article.citation_metrics.nih_percentile,
                expected_citations=article.citation_metrics.expected_citations,
                field_citation_rate=article.citation_metrics.field_citation_rate,
            )

        await DatabaseService.log_usage("fetch", article_id=article.article_id, cache_hit=False)

        return ArticleFetchResponse(
            article_id=article.article_id,
            source=article.source,
            pmcid=article.pmcid,
            doi=article.doi,
            title=article.title,
            abstract=article.abstract,
            authors=article.authors,
            journal=article.journal,
            pub_date=article.pub_date,
            has_full_text=article.full_text is not None,
            citation_metrics=citation_metrics,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching article: {str(e)}")


async def _get_article_for_processing(article_id: str, identifier: str | None = None) -> ArticleMetadata:
    """Get an ArticleMetadata for Claude processing — from cache or source."""
    cached = await DatabaseService.get_cached_article(article_id)
    if cached:
        article = _build_article_metadata_from_cache(cached)
        # Attach citation metrics if cached
        cached_metrics = await DatabaseService.get_cached_citation_metrics(article_id)
        if cached_metrics:
            article.citation_metrics = CitationMetrics(
                citation_count=cached_metrics["citation_count"],
                citations_per_year=cached_metrics.get("citations_per_year"),
                relative_citation_ratio=cached_metrics.get("relative_citation_ratio"),
                nih_percentile=cached_metrics.get("nih_percentile"),
                expected_citations=cached_metrics.get("expected_citations"),
                field_citation_rate=cached_metrics.get("field_citation_rate"),
            )
        return article

    # Not cached — fetch fresh using the original identifier if available
    fetch_id = identifier or article_id
    article = await _fetch_article_from_source(fetch_id)
    await DatabaseService.cache_article(_article_to_cache_dict(article))
    if article.citation_metrics:
        await DatabaseService.cache_citation_metrics(article.article_id, {
            "citation_count": article.citation_metrics.citation_count,
            "citations_per_year": article.citation_metrics.citations_per_year,
            "relative_citation_ratio": article.citation_metrics.relative_citation_ratio,
            "nih_percentile": article.citation_metrics.nih_percentile,
            "expected_citations": article.citation_metrics.expected_citations,
            "field_citation_rate": article.citation_metrics.field_citation_rate,
        })
    return article


@router.post("/process", response_model=ProcessResponse)
async def process_article(request: ProcessRequest):
    """
    Process an article with translation and/or summarization.

    - Translation: Translates title and abstract/full text to target language
    - Summarization: Generates summary at specified knowledge level
    """
    if not request.translate and not request.summarize:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'translate' or 'summarize' must be provided"
        )

    claude_service = ClaudeService()

    try:
        # Resolve article_id
        article_id, id_type = await _resolve_article_id(request.identifier)

        # Check caches for requested operations
        cached_translation = None
        cached_summary = None
        translation_cache_hit = False
        summary_cache_hit = False

        if request.translate:
            cached_translation = await DatabaseService.get_cached_translation(
                article_id, request.translate.target_language
            )
            translation_cache_hit = cached_translation is not None

        if request.summarize:
            cached_summary = await DatabaseService.get_cached_summary(
                article_id, request.summarize.knowledge_level.value
            )
            summary_cache_hit = cached_summary is not None

        # Determine if we need to call Claude at all
        need_fresh_translation = request.translate and not cached_translation
        need_fresh_summary = request.summarize and not cached_summary

        # Only fetch full article if we need to call Claude
        article = None
        if need_fresh_translation or need_fresh_summary:
            article = await _get_article_for_processing(article_id, request.identifier)

        # If fully cached, we still need basic article info for the response
        if article is None:
            cached_article = await DatabaseService.get_cached_article(article_id)
            if cached_article:
                article_title = cached_article["title"]
                article_abstract = cached_article["abstract"]
            else:
                # Shouldn't happen, but fallback
                article = await _get_article_for_processing(article_id, request.identifier)
                article_title = article.title
                article_abstract = article.abstract
        else:
            article_title = article.title
            article_abstract = article.abstract

        response = ProcessResponse(
            article_id=article_id,
            title=article_title,
            original_abstract=article_abstract,
        )

        # Track overall cache status
        all_cached = True
        cached_at = None
        result_id = None

        # Handle translation
        if request.translate:
            if cached_translation:
                response.translated_title = cached_translation["translated_title"]
                response.translated_abstract = cached_translation["translated_abstract"]
                response.target_language = request.translate.target_language
                cached_at = cached_translation["cached_at"]
                result_id = cached_translation["id"]
            else:
                all_cached = False
                translation = await claude_service.translate(
                    article, request.translate.target_language
                )
                response.translated_title = translation["translated_title"]
                response.translated_abstract = translation["translated_abstract"]
                response.target_language = request.translate.target_language
                result_id = await DatabaseService.cache_translation(
                    article_id, request.translate.target_language, translation
                )

            await DatabaseService.log_usage(
                "translate",
                article_id=article_id,
                options={"target_language": request.translate.target_language},
                cache_hit=translation_cache_hit,
            )

        # Handle summarization
        if request.summarize:
            if cached_summary:
                response.summary = cached_summary["summary"]
                response.key_findings = cached_summary["key_findings"]
                response.context = cached_summary["context"]
                response.acronyms = cached_summary["acronyms"]
                response.knowledge_level = request.summarize.knowledge_level.value
                cached_at = cached_summary["cached_at"]
                result_id = cached_summary["id"]
            else:
                all_cached = False
                summary_result = await claude_service.summarize(
                    article, request.summarize.knowledge_level
                )
                response.summary = summary_result["summary"]
                response.key_findings = summary_result["key_findings"]
                response.context = summary_result["context"]
                response.acronyms = summary_result.get("acronyms")
                response.knowledge_level = request.summarize.knowledge_level.value
                result_id = await DatabaseService.cache_summary(
                    article_id, request.summarize.knowledge_level.value, summary_result
                )

            await DatabaseService.log_usage(
                "summarize",
                article_id=article_id,
                options={"knowledge_level": request.summarize.knowledge_level.value},
                cache_hit=summary_cache_hit,
            )

        response.from_cache = all_cached
        response.cached_at = cached_at if all_cached else None
        response.result_id = result_id

        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing article: {str(e)}")


@router.post("/report", response_model=ReportBadOutputResponse)
async def report_bad_output(request: ReportBadOutputRequest):
    """
    Report bad output, invalidate cache, regenerate with Claude, and return fresh result.
    """
    claude_service = ClaudeService()

    try:
        article = await _get_article_for_processing(request.article_id)

        # Log the bad output report
        await DatabaseService.report_bad_output(
            article_id=request.article_id,
            result_type=request.result_type,
            target_language=request.target_language,
            knowledge_level=request.knowledge_level,
            comment=request.comment,
        )

        response = ProcessResponse(
            article_id=article.article_id,
            title=article.title,
            original_abstract=article.abstract,
        )

        if request.result_type == "translation" and request.target_language:
            # Invalidate and regenerate translation
            await DatabaseService.invalidate_translation(request.article_id, request.target_language)
            translation = await claude_service.translate(article, request.target_language)
            response.translated_title = translation["translated_title"]
            response.translated_abstract = translation["translated_abstract"]
            response.target_language = request.target_language
            result_id = await DatabaseService.cache_translation(
                request.article_id, request.target_language, translation
            )
            response.result_id = result_id

            await DatabaseService.log_usage(
                "translate",
                article_id=request.article_id,
                options={"target_language": request.target_language, "regenerated": True},
                cache_hit=False,
            )

        elif request.result_type == "summary" and request.knowledge_level:
            # Invalidate and regenerate summary
            await DatabaseService.invalidate_summary(request.article_id, request.knowledge_level)
            knowledge_level_enum = KnowledgeLevel(request.knowledge_level)
            summary_result = await claude_service.summarize(article, knowledge_level_enum)
            response.summary = summary_result["summary"]
            response.key_findings = summary_result["key_findings"]
            response.context = summary_result["context"]
            response.acronyms = summary_result.get("acronyms")
            response.knowledge_level = request.knowledge_level
            result_id = await DatabaseService.cache_summary(
                request.article_id, request.knowledge_level, summary_result
            )
            response.result_id = result_id

            await DatabaseService.log_usage(
                "summarize",
                article_id=request.article_id,
                options={"knowledge_level": request.knowledge_level, "regenerated": True},
                cache_hit=False,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid result_type or missing required language/level parameter"
            )

        return ReportBadOutputResponse(success=True, new_result=response)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating output: {str(e)}")
