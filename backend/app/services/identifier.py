import re
from enum import Enum
from dataclasses import dataclass


class IdentifierType(str, Enum):
    """Type of article identifier."""
    PMID = "pmid"
    PMCID = "pmcid"
    DOI = "doi"
    TITLE = "title"
    ARXIV = "arxiv"
    BIORXIV = "biorxiv"
    MEDRXIV = "medrxiv"
    UNKNOWN = "unknown"


@dataclass
class ParsedIdentifier:
    """Result of parsing an article identifier."""
    type: IdentifierType
    value: str
    original: str


def parse_identifier(input_str: str) -> ParsedIdentifier:
    """
    Parse an input string to determine what type of identifier it is.

    Supports:
    - PMIDs (numeric, e.g., "41514338")
    - PMCIDs (e.g., "PMC12283410")
    - DOIs (e.g., "10.1234/example")
    - PubMed URLs (e.g., "https://pubmed.ncbi.nlm.nih.gov/41514338/")
    - PMC URLs (e.g., "https://pmc.ncbi.nlm.nih.gov/articles/PMC4136005/")
    - arxiv URLs and IDs (e.g., "https://arxiv.org/abs/2401.12345", "arxiv:2401.12345")
    - biorxiv URLs (e.g., "https://www.biorxiv.org/content/10.1101/2024.01.01.123456v1")
    - medrxiv URLs (e.g., "https://www.medrxiv.org/content/10.1101/2024.01.01.123456v1")
    - biorxiv/medrxiv DOIs (10.1101/...)
    - Titles (anything else, used for search)
    """
    input_str = input_str.strip()

    # Check for arxiv URL: arxiv.org/abs/... or arxiv.org/pdf/...
    arxiv_url_pattern = r"(?:https?://)?(?:export\.)?arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)"
    match = re.search(arxiv_url_pattern, input_str)
    if match:
        return ParsedIdentifier(
            type=IdentifierType.ARXIV,
            value=match.group(1),
            original=input_str
        )

    # Check for arxiv: prefix (e.g., "arxiv:2401.12345")
    arxiv_prefix_pattern = r"^arxiv:(\d{4}\.\d{4,5}(?:v\d+)?)$"
    match = re.match(arxiv_prefix_pattern, input_str, re.IGNORECASE)
    if match:
        return ParsedIdentifier(
            type=IdentifierType.ARXIV,
            value=match.group(1),
            original=input_str
        )

    # Check for biorxiv URL
    biorxiv_url_pattern = r"(?:https?://)?(?:www\.)?biorxiv\.org/content/(10\.1101/[^\s?#]+?)(?:v\d+)?(?:\?|#|$)"
    match = re.search(biorxiv_url_pattern, input_str)
    if match:
        # Strip trailing version from DOI value
        doi = re.sub(r"v\d+$", "", match.group(1))
        return ParsedIdentifier(
            type=IdentifierType.BIORXIV,
            value=doi,
            original=input_str
        )

    # Check for medrxiv URL
    medrxiv_url_pattern = r"(?:https?://)?(?:www\.)?medrxiv\.org/content/(10\.1101/[^\s?#]+?)(?:v\d+)?(?:\?|#|$)"
    match = re.search(medrxiv_url_pattern, input_str)
    if match:
        doi = re.sub(r"v\d+$", "", match.group(1))
        return ParsedIdentifier(
            type=IdentifierType.MEDRXIV,
            value=doi,
            original=input_str
        )

    # Check for PubMed URL
    pubmed_url_pattern = r"(?:https?://)?(?:www\.)?pubmed\.ncbi\.nlm\.nih\.gov/(\d+)"
    match = re.search(pubmed_url_pattern, input_str)
    if match:
        return ParsedIdentifier(
            type=IdentifierType.PMID,
            value=match.group(1),
            original=input_str
        )

    # Check for PMC URL
    pmc_url_pattern = r"(?:https?://)?(?:www\.)?(?:ncbi\.nlm\.nih\.gov/)?pmc/articles/(PMC\d+)"
    match = re.search(pmc_url_pattern, input_str, re.IGNORECASE)
    if match:
        return ParsedIdentifier(
            type=IdentifierType.PMCID,
            value=match.group(1).upper(),
            original=input_str
        )

    # Check for bare PMCID
    pmcid_pattern = r"^PMC\d+$"
    if re.match(pmcid_pattern, input_str, re.IGNORECASE):
        return ParsedIdentifier(
            type=IdentifierType.PMCID,
            value=input_str.upper(),
            original=input_str
        )

    # Check for bare PMID (just numbers)
    if input_str.isdigit():
        return ParsedIdentifier(
            type=IdentifierType.PMID,
            value=input_str,
            original=input_str
        )

    # Check for DOI - must come after preprint URL checks
    doi_pattern = r"(?:https?://)?(?:dx\.)?(?:doi\.org/)?(10\.\d{4,}/[^\s]+)"
    match = re.search(doi_pattern, input_str)
    if match:
        doi_value = match.group(1)
        # 10.1101/ DOIs are biorxiv/medrxiv preprints
        if doi_value.startswith("10.1101/"):
            # Default to biorxiv; the preprint client will try both
            return ParsedIdentifier(
                type=IdentifierType.BIORXIV,
                value=doi_value,
                original=input_str
            )
        return ParsedIdentifier(
            type=IdentifierType.DOI,
            value=doi_value,
            original=input_str
        )

    # Assume it's a title for search
    return ParsedIdentifier(
        type=IdentifierType.TITLE,
        value=input_str,
        original=input_str
    )
