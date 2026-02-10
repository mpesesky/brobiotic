import xml.etree.ElementTree as ET

import httpx

from app.services.identifier import ParsedIdentifier, IdentifierType
from app.services.pdf import extract_text_from_pdf
from app.services.pubmed import ArticleMetadata


class PreprintClient:
    """Client for fetching preprints from arxiv, biorxiv, and medrxiv."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def fetch_arxiv(self, arxiv_id: str) -> ArticleMetadata:
        """Fetch metadata and full text from arxiv."""
        # Fetch metadata via Atom API
        api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
        response = await self.client.get(api_url)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        entry = root.find("atom:entry", ns)
        if entry is None:
            raise ValueError(f"No arxiv entry found for {arxiv_id}")

        # Check for error
        id_elem = entry.find("atom:id", ns)
        if id_elem is not None and "error" in (id_elem.text or "").lower():
            raise ValueError(f"arxiv API error for {arxiv_id}")

        title = entry.find("atom:title", ns)
        title_text = title.text.strip().replace("\n", " ") if title is not None and title.text else ""

        summary = entry.find("atom:summary", ns)
        abstract = summary.text.strip() if summary is not None and summary.text else ""

        authors = []
        for author_elem in entry.findall("atom:author", ns):
            name = author_elem.find("atom:name", ns)
            if name is not None and name.text:
                authors.append(name.text)

        published = entry.find("atom:published", ns)
        pub_date = ""
        if published is not None and published.text:
            pub_date = published.text[:10]  # YYYY-MM-DD

        # Extract DOI if present
        doi = None
        doi_elem = entry.find("arxiv:doi", ns)
        if doi_elem is not None and doi_elem.text:
            doi = doi_elem.text

        # Download PDF and extract text
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        full_text = await self._download_and_extract_pdf(pdf_url)

        return ArticleMetadata(
            article_id=f"arxiv:{arxiv_id}",
            source="arxiv",
            doi=doi,
            title=title_text,
            abstract=abstract,
            authors=authors,
            journal="arXiv",
            pub_date=pub_date,
            full_text=full_text,
        )

    async def fetch_biorxiv(self, doi: str) -> ArticleMetadata:
        """Fetch metadata and full text from biorxiv."""
        return await self._fetch_rxiv(doi, "biorxiv")

    async def fetch_medrxiv(self, doi: str) -> ArticleMetadata:
        """Fetch metadata and full text from medrxiv."""
        return await self._fetch_rxiv(doi, "medrxiv")

    async def _fetch_rxiv(self, doi: str, server: str) -> ArticleMetadata:
        """Fetch from biorxiv or medrxiv API."""
        # The biorxiv API serves both biorxiv and medrxiv
        # Strip the 10.1101/ prefix for the API call
        doi_suffix = doi.replace("10.1101/", "")
        api_url = f"https://api.biorxiv.org/details/{server}/{doi_suffix}"
        response = await self.client.get(api_url)
        response.raise_for_status()

        data = response.json()
        collection = data.get("collection", [])
        if not collection:
            # If not found on the specified server, try the other one
            other_server = "medrxiv" if server == "biorxiv" else "biorxiv"
            api_url = f"https://api.biorxiv.org/details/{other_server}/{doi_suffix}"
            response = await self.client.get(api_url)
            response.raise_for_status()
            data = response.json()
            collection = data.get("collection", [])
            if not collection:
                raise ValueError(f"No preprint found for DOI {doi}")
            server = other_server

        # Use the latest version (last entry)
        entry = collection[-1]

        title = entry.get("title", "")
        abstract = entry.get("abstract", "")
        authors_str = entry.get("authors", "")
        authors = [a.strip() for a in authors_str.split(";") if a.strip()]
        pub_date = entry.get("date", "")

        # Download PDF and extract text
        # biorxiv/medrxiv PDFs are at the content URL + .full.pdf
        pdf_url = f"https://www.{server}.org/content/{doi}v{entry.get('version', '1')}.full.pdf"
        full_text = await self._download_and_extract_pdf(pdf_url)

        return ArticleMetadata(
            article_id=f"{server}:{doi}",
            source=server,
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=f"{server}",
            pub_date=pub_date,
            full_text=full_text,
        )

    async def _download_and_extract_pdf(self, pdf_url: str) -> str | None:
        """Download a PDF and extract text."""
        try:
            response = await self.client.get(pdf_url, follow_redirects=True)
            if response.status_code != 200:
                print(f"PDF download failed ({response.status_code}): {pdf_url}")
                return None
            return extract_text_from_pdf(response.content)
        except Exception as e:
            print(f"PDF extraction failed: {e}")
            return None

    async def get_preprint(self, parsed: ParsedIdentifier) -> ArticleMetadata:
        """Main entry point: fetch preprint based on parsed identifier."""
        if parsed.type == IdentifierType.ARXIV:
            return await self.fetch_arxiv(parsed.value)
        elif parsed.type == IdentifierType.BIORXIV:
            return await self.fetch_biorxiv(parsed.value)
        elif parsed.type == IdentifierType.MEDRXIV:
            return await self.fetch_medrxiv(parsed.value)
        else:
            raise ValueError(f"Not a preprint identifier: {parsed.type}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
