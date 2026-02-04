import httpx
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from app.config import get_settings
from app.services.identifier import parse_identifier, IdentifierType, ParsedIdentifier


@dataclass
class CitationMetrics:
    """Citation metrics from iCite."""
    citation_count: int = 0
    citations_per_year: float | None = None
    relative_citation_ratio: float | None = None  # Field-normalized impact
    nih_percentile: float | None = None  # Percentile among NIH-funded papers
    expected_citations: float | None = None
    field_citation_rate: float | None = None


@dataclass
class ArticleMetadata:
    """Metadata for a PubMed article."""
    pmid: str
    pmcid: str | None = None
    doi: str | None = None
    title: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    pub_date: str = ""
    full_text: str | None = None
    citation_metrics: CitationMetrics | None = None


class PubMedClient:
    """Client for PubMed E-utilities and PMC APIs."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PMC_OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ncbi_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    def _add_api_key(self, params: dict) -> dict:
        """Add API key to request params if available."""
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    async def search_by_title(self, title: str) -> str | None:
        """Search PubMed by title and return the first matching PMID."""
        params = self._add_api_key({
            "db": "pubmed",
            "term": f"{title}[Title]",
            "retmax": "1",
            "retmode": "json",
        })

        response = await self.client.get(f"{self.BASE_URL}/esearch.fcgi", params=params)
        response.raise_for_status()

        data = response.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        return id_list[0] if id_list else None

    async def search_by_doi(self, doi: str) -> str | None:
        """Search PubMed by DOI and return the matching PMID."""
        params = self._add_api_key({
            "db": "pubmed",
            "term": f"{doi}[DOI]",
            "retmax": "1",
            "retmode": "json",
        })

        response = await self.client.get(f"{self.BASE_URL}/esearch.fcgi", params=params)
        response.raise_for_status()

        data = response.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        return id_list[0] if id_list else None

    async def get_pmid_from_pmcid(self, pmcid: str) -> str | None:
        """Convert PMCID to PMID using ID converter."""
        # Remove 'PMC' prefix if present for the search
        pmc_number = pmcid.replace("PMC", "")

        params = self._add_api_key({
            "db": "pmc",
            "term": f"PMC{pmc_number}[pmcid]",
            "retmax": "1",
            "retmode": "json",
        })

        response = await self.client.get(f"{self.BASE_URL}/esearch.fcgi", params=params)
        response.raise_for_status()

        data = response.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            return None

        # Use elink to convert PMC ID to PubMed ID
        pmc_id = id_list[0]
        link_params = self._add_api_key({
            "dbfrom": "pmc",
            "db": "pubmed",
            "id": pmc_id,
            "retmode": "json",
        })

        link_response = await self.client.get(f"{self.BASE_URL}/elink.fcgi", params=link_params)
        link_response.raise_for_status()

        link_data = link_response.json()
        linksets = link_data.get("linksets", [])
        if linksets:
            linksetdbs = linksets[0].get("linksetdbs", [])
            if linksetdbs:
                links = linksetdbs[0].get("links", [])
                if links:
                    return links[0]

        return None

    async def fetch_article(self, pmid: str) -> ArticleMetadata:
        """Fetch article metadata and abstract from PubMed."""
        params = self._add_api_key({
            "db": "pubmed",
            "id": pmid,
            "rettype": "xml",
            "retmode": "xml",
        })

        response = await self.client.get(f"{self.BASE_URL}/efetch.fcgi", params=params)
        response.raise_for_status()

        return self._parse_pubmed_xml(response.text, pmid)

    def _parse_pubmed_xml(self, xml_str: str, pmid: str) -> ArticleMetadata:
        """Parse PubMed XML response into ArticleMetadata."""
        root = ET.fromstring(xml_str)
        article = root.find(".//PubmedArticle")

        if article is None:
            raise ValueError(f"No article found for PMID {pmid}")

        medline = article.find(".//MedlineCitation")
        article_elem = medline.find(".//Article")

        # Title
        title_elem = article_elem.find(".//ArticleTitle")
        title = "".join(title_elem.itertext()) if title_elem is not None else ""

        # Abstract
        abstract_parts = []
        abstract_elem = article_elem.find(".//Abstract")
        if abstract_elem is not None:
            for text_elem in abstract_elem.findall(".//AbstractText"):
                label = text_elem.get("Label", "")
                text = "".join(text_elem.itertext())
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        abstract = "\n\n".join(abstract_parts)

        # Authors
        authors = []
        author_list = article_elem.find(".//AuthorList")
        if author_list is not None:
            for author in author_list.findall(".//Author"):
                lastname = author.find("LastName")
                forename = author.find("ForeName")
                if lastname is not None:
                    name = lastname.text or ""
                    if forename is not None and forename.text:
                        name = f"{forename.text} {name}"
                    authors.append(name)

        # Journal
        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # Publication date
        pub_date_elem = article_elem.find(".//Journal/JournalIssue/PubDate")
        pub_date = ""
        if pub_date_elem is not None:
            year = pub_date_elem.find("Year")
            month = pub_date_elem.find("Month")
            if year is not None:
                pub_date = year.text or ""
                if month is not None and month.text:
                    pub_date = f"{month.text} {pub_date}"

        # PMCID and DOI from article IDs
        pmcid = None
        doi = None
        article_id_list = article.find(".//PubmedData/ArticleIdList")
        if article_id_list is not None:
            for article_id in article_id_list.findall("ArticleId"):
                id_type = article_id.get("IdType")
                if id_type == "pmc" and article_id.text:
                    pmcid = article_id.text
                elif id_type == "doi" and article_id.text:
                    doi = article_id.text

        return ArticleMetadata(
            pmid=pmid,
            pmcid=pmcid,
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            pub_date=pub_date,
        )

    async def fetch_pmc_full_text(self, pmcid: str) -> str | None:
        """Attempt to fetch full text from PMC."""
        # Method 1: Try PMC efetch API (works for most PMC articles)
        pmc_number = pmcid.replace("PMC", "")
        efetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = self._add_api_key({
            "db": "pmc",
            "id": pmc_number,
            "rettype": "xml",
            "retmode": "xml",
        })

        try:
            response = await self.client.get(efetch_url, params=params)
            if response.status_code == 200:
                full_text = self._parse_pmc_xml(response.text)
                if full_text:
                    print(f"Got full text via efetch: {len(full_text)} chars")
                    return full_text
        except Exception as e:
            print(f"efetch failed: {e}")

        # Method 2: Fall back to OA service (for open access articles)
        params = {"id": pmcid}
        try:
            response = await self.client.get(self.PMC_OA_URL, params=params)

            if response.status_code != 200:
                print(f"OA service returned {response.status_code}")
                return None

            root = ET.fromstring(response.text)
            record = root.find(".//record")

            if record is None:
                print("No record found in OA response")
                return None

            # Check for error
            error = record.find(".//error")
            if error is not None:
                print(f"OA error: {error.text}")
                return None

            link = record.find(".//link[@format='xml']")
            if link is None:
                link = record.find(".//link[@format='tgz']")

            if link is None:
                print("No XML link in OA response")
                return None

            href = link.get("href")
            if not href:
                return None

            if link.get("format") == "xml":
                xml_response = await self.client.get(href)
                xml_response.raise_for_status()
                return self._parse_pmc_xml(xml_response.text)
        except Exception as e:
            print(f"OA fetch failed: {e}")

        return None

    def _parse_pmc_xml(self, xml_str: str) -> str:
        """Parse PMC XML to extract article body text."""
        root = ET.fromstring(xml_str)

        # Find body element
        body = root.find(".//body")
        if body is None:
            return ""

        # Extract all text from body, preserving some structure
        text_parts = []

        for section in body.iter():
            if section.tag == "title":
                text = "".join(section.itertext()).strip()
                if text:
                    text_parts.append(f"\n## {text}\n")
            elif section.tag == "p":
                text = "".join(section.itertext()).strip()
                if text:
                    text_parts.append(text)

        return "\n\n".join(text_parts)

    async def fetch_citation_metrics(self, pmid: str) -> CitationMetrics | None:
        """Fetch citation metrics from NIH iCite API."""
        icite_url = "https://icite.od.nih.gov/api/pubs"
        params = {"pmids": pmid, "format": "json"}

        try:
            response = await self.client.get(icite_url, params=params)
            if response.status_code != 200:
                print(f"iCite returned {response.status_code}")
                return None

            data = response.json()
            if not data.get("data"):
                return None

            pub = data["data"][0]

            return CitationMetrics(
                citation_count=pub.get("citation_count", 0) or 0,
                citations_per_year=pub.get("citations_per_year"),
                relative_citation_ratio=pub.get("relative_citation_ratio"),
                nih_percentile=pub.get("nih_percentile"),
                expected_citations=pub.get("expected_citations_per_year"),
                field_citation_rate=pub.get("field_citation_rate"),
            )
        except Exception as e:
            print(f"iCite fetch failed: {e}")
            return None

    async def resolve_pmid(self, identifier: str) -> str:
        """Resolve any identifier type to a PMID without fetching full metadata."""
        parsed = parse_identifier(identifier)

        if parsed.type == IdentifierType.PMID:
            return parsed.value
        elif parsed.type == IdentifierType.PMCID:
            pmid = await self.get_pmid_from_pmcid(parsed.value)
            if not pmid:
                raise ValueError(f"Could not find PMID for {parsed.value}")
            return pmid
        elif parsed.type == IdentifierType.DOI:
            pmid = await self.search_by_doi(parsed.value)
            if not pmid:
                raise ValueError(f"Could not find article for DOI {parsed.value}")
            return pmid
        elif parsed.type == IdentifierType.TITLE:
            pmid = await self.search_by_title(parsed.value)
            if not pmid:
                raise ValueError(f"No article found matching title: {parsed.value}")
            return pmid

        raise ValueError(f"Could not resolve identifier: {identifier}")

    async def get_article(self, identifier: str) -> ArticleMetadata:
        """
        Get article by any identifier type (PMID, PMCID, DOI, URL, or title).

        This is the main entry point for fetching articles.
        """
        parsed = parse_identifier(identifier)

        pmid = None

        if parsed.type == IdentifierType.PMID:
            pmid = parsed.value
        elif parsed.type == IdentifierType.PMCID:
            pmid = await self.get_pmid_from_pmcid(parsed.value)
            if not pmid:
                raise ValueError(f"Could not find PMID for {parsed.value}")
        elif parsed.type == IdentifierType.DOI:
            pmid = await self.search_by_doi(parsed.value)
            if not pmid:
                raise ValueError(f"Could not find article for DOI {parsed.value}")
        elif parsed.type == IdentifierType.TITLE:
            pmid = await self.search_by_title(parsed.value)
            if not pmid:
                raise ValueError(f"No article found matching title: {parsed.value}")

        if not pmid:
            raise ValueError(f"Could not resolve identifier: {identifier}")

        # Fetch article metadata
        article = await self.fetch_article(pmid)

        # Try to get full text if PMCID is available
        if article.pmcid:
            full_text = await self.fetch_pmc_full_text(article.pmcid)
            if full_text:
                article.full_text = full_text

        # Fetch citation metrics from iCite
        article.citation_metrics = await self.fetch_citation_metrics(pmid)

        return article

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
