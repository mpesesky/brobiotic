import re
from enum import Enum
from dataclasses import dataclass


class IdentifierType(str, Enum):
    """Type of article identifier."""
    PMID = "pmid"
    PMCID = "pmcid"
    DOI = "doi"
    TITLE = "title"
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
    - Titles (anything else, used for search)
    """
    input_str = input_str.strip()

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

    # Check for DOI
    doi_pattern = r"(?:https?://)?(?:dx\.)?(?:doi\.org/)?(10\.\d{4,}/[^\s]+)"
    match = re.search(doi_pattern, input_str)
    if match:
        return ParsedIdentifier(
            type=IdentifierType.DOI,
            value=match.group(1),
            original=input_str
        )

    # Assume it's a title for search
    return ParsedIdentifier(
        type=IdentifierType.TITLE,
        value=input_str,
        original=input_str
    )
