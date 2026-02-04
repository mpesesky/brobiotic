from pydantic import BaseModel, Field
from enum import Enum


class KnowledgeLevel(str, Enum):
    """Level of scientific background assumed for summaries."""
    EXPERT = "expert"
    ADJACENT = "adjacent"
    LAY_PERSON = "lay_person"


class ArticleFetchRequest(BaseModel):
    """Request to fetch an article by identifier."""
    identifier: str = Field(..., description="PMID, PMCID, DOI, URL, or article title")


class CitationMetricsResponse(BaseModel):
    """Citation metrics from iCite."""
    citation_count: int = 0
    citations_per_year: float | None = None
    relative_citation_ratio: float | None = None  # Field-normalized impact (1.0 = average)
    nih_percentile: float | None = None  # Percentile among NIH-funded papers
    expected_citations: float | None = None
    field_citation_rate: float | None = None


class ArticleFetchResponse(BaseModel):
    """Response containing fetched article data."""
    pmid: str
    pmcid: str | None = None
    doi: str | None = None
    title: str
    abstract: str
    authors: list[str]
    journal: str
    pub_date: str
    has_full_text: bool
    citation_metrics: CitationMetricsResponse | None = None
    from_cache: bool = False
    cached_at: str | None = None


class TranslationOptions(BaseModel):
    """Options for translating an article."""
    target_language: str = Field(..., description="Target language for translation")


class SummarizationOptions(BaseModel):
    """Options for summarizing an article."""
    knowledge_level: KnowledgeLevel = Field(
        default=KnowledgeLevel.ADJACENT,
        description="Assumed knowledge level of the reader"
    )


class ProcessRequest(BaseModel):
    """Request to process an article with translation and/or summarization."""
    identifier: str = Field(..., description="PMID or other identifier of the article")
    translate: TranslationOptions | None = None
    summarize: SummarizationOptions | None = None


class ProcessResponse(BaseModel):
    """Response containing processed article data."""
    pmid: str
    title: str
    original_abstract: str
    translated_abstract: str | None = None
    translated_title: str | None = None
    summary: str | None = None
    key_findings: list[str] | None = None
    context: str | None = None
    acronyms: list[str] | None = None
    target_language: str | None = None
    knowledge_level: str | None = None
    from_cache: bool = False
    cached_at: str | None = None
    result_id: str | None = None


class ReportBadOutputRequest(BaseModel):
    """Request to report bad output and regenerate."""
    pmid: str
    result_type: str = Field(..., description="'translation' or 'summary'")
    target_language: str | None = None
    knowledge_level: str | None = None
    comment: str | None = None


class ReportBadOutputResponse(BaseModel):
    """Response after reporting bad output with fresh result."""
    success: bool
    new_result: ProcessResponse


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
