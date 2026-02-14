from anthropic import AsyncAnthropic

from app.config import get_settings
from app.models.schemas import KnowledgeLevel
from app.services.pubmed import ArticleMetadata


def _extract_inline_content(line: str, keyword: str) -> str:
    """Extract any content that appears inline after a section header keyword and colon.

    Handles lines like '3. CONTEXT: Some text here' where the content follows
    the header on the same line.
    """
    upper = line.upper()
    idx = upper.find(keyword.upper())
    if idx == -1:
        return ""
    colon_start = idx + len(keyword)
    colon_idx = line.find(":", colon_start)
    if colon_idx == -1:
        return ""
    return line[colon_idx + 1:].strip()


class ClaudeService:
    """Service for article translation and summarization using Claude."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def translate(
        self,
        article: ArticleMetadata,
        target_language: str
    ) -> dict:
        """
        Translate article title and abstract to the target language.

        Returns dict with translated_title and translated_abstract.
        """
        # Use full text if available, otherwise use abstract
        content = article.full_text if article.full_text else article.abstract

        prompt = f"""Translate the following scientific article content to {target_language}.

Maintain scientific accuracy and preserve technical terminology where appropriate.
If a technical term is commonly used in its original form in {target_language},
you may keep it with a translation in parentheses.

TITLE:
{article.title}

CONTENT:
{content}

Provide your translation in the following format:
TRANSLATED TITLE:
[translated title here]

TRANSLATED CONTENT:
[translated content here]"""

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse the response
        translated_title = ""
        translated_content = ""

        if "TRANSLATED TITLE:" in response_text:
            parts = response_text.split("TRANSLATED CONTENT:")
            if len(parts) >= 2:
                title_part = parts[0].replace("TRANSLATED TITLE:", "").strip()
                translated_title = title_part
                translated_content = parts[1].strip()
            else:
                translated_content = response_text

        return {
            "translated_title": translated_title,
            "translated_abstract": translated_content,
        }

    async def summarize(
        self,
        article: ArticleMetadata,
        knowledge_level: KnowledgeLevel
    ) -> dict:
        """
        Summarize article at the specified knowledge level.

        Returns dict with summary, key_findings, and context.
        """
        content = article.full_text if article.full_text else article.abstract

        has_full_text = article.full_text is not None

        system_prompts = {
            KnowledgeLevel.EXPERT: """You are a scientific research assistant summarizing articles for domain experts.
Assume the reader has deep knowledge of the field. Focus on:
- Novel methodology and technical innovations
- Specific findings and statistical significance
- Implications for current research paradigms
- Technical limitations and future directions
Use field-specific terminology without explanation.

Writing guidelines:
- Be concise. The summary must always be shorter than the text being summarized — never produce more text than the original content.
- Use neutral, objective language. Avoid promotional phrases like "groundbreaking," "significant advance," or "revolutionize."
- State findings factually without editorializing their importance.
- Let readers draw their own conclusions about impact.
- When full text is provided, reference specific figures and tables (e.g., "Fig. 2", "Table 1") that support each key finding.
- In the context section, critically assess the work's standing: Is it well-accepted, controversial, contradicted by other research, or too new to evaluate? Cite specific contradicting or supporting work if known.""",

            KnowledgeLevel.ADJACENT: """You are a scientific research assistant summarizing articles for researchers from related fields.
Assume the reader has scientific training but may not know field-specific terminology. Focus on:
- Brief explanation of key field-specific terms
- Core methodology and approach
- Main findings and their significance
- How this research connects to broader scientific questions
Balance technical accuracy with accessibility.

Writing guidelines:
- Be concise. The summary must always be shorter than the text being summarized — never produce more text than the original content.
- Use neutral, objective language. Avoid promotional phrases like "groundbreaking," "significant advance," or "revolutionize."
- State findings factually without editorializing their importance.
- Let readers draw their own conclusions about impact.
- When full text is provided, every key finding MUST cite the specific figure(s) or table(s) that support it (e.g., "Fig. 2", "Table 1"). Do not list a finding without its supporting figure/table reference.
- In the context section, critically assess the work's standing: Is it well-accepted, controversial, contradicted by other research, or too new to evaluate? Cite specific contradicting or supporting work if known.""",

            KnowledgeLevel.LAY_PERSON: """You are a science communicator summarizing articles for the general public.
Assume the reader is intelligent but has no scientific background. Focus on:
- Why this research matters in everyday terms
- What the researchers did (avoid jargon)
- What they found (use analogies when helpful)
- What this means for society or future applications
Use plain language and explain any necessary technical terms.

Writing guidelines:
- Be concise. Keep the summary to 1-2 short paragraphs. The summary must always be shorter than the text being summarized — never produce more text than the original content.
- Use neutral, measured language. Avoid promotional phrases like "groundbreaking," "breakthrough," "significant advance," "revolutionize," or "game-changing."
- Present findings objectively. Do not overstate implications or promise future applications that are speculative.
- Respect the reader's intelligence - inform without hyping.
- In the context section, mention if this research is controversial, widely accepted, or too new to fully evaluate."""
        }

        # Build prompt with conditional instructions based on knowledge level
        figure_instruction = ""
        acronym_instruction = ""
        if knowledge_level in (KnowledgeLevel.EXPERT, KnowledgeLevel.ADJACENT):
            if has_full_text:
                figure_instruction = " IMPORTANT: Every finding MUST cite the specific supporting figure(s) or table(s) in parentheses, e.g., '(Fig. 2, Table 1)'. Do not omit these references."
            acronym_instruction = "\n4. ACRONYMS: List any acronyms/abbreviations used in the article with their full meanings, formatted as 'ACRONYM: Full Meaning' (one per line)."

        # Build citation metrics section if available
        citation_info = ""
        if article.citation_metrics:
            cm = article.citation_metrics
            citation_parts = [f"Citations: {cm.citation_count}"]
            if cm.citations_per_year:
                citation_parts.append(f"Citations/year: {cm.citations_per_year:.1f}")
            if cm.relative_citation_ratio:
                citation_parts.append(f"Relative Citation Ratio: {cm.relative_citation_ratio:.2f} (1.0 = field average)")
            if cm.nih_percentile:
                citation_parts.append(f"NIH Percentile: {cm.nih_percentile:.1f}")
            citation_info = f"\nCITATION METRICS: {' | '.join(citation_parts)}"

        prompt = f"""Please summarize this scientific article.

TITLE: {article.title}

AUTHORS: {', '.join(article.authors[:5])}{'...' if len(article.authors) > 5 else ''}

JOURNAL: {article.journal}

PUBLICATION DATE: {article.pub_date}{citation_info}

{"NOTE: Full text is provided below." if has_full_text else "NOTE: Only the abstract is available."}

CONTENT:
{content}

Please provide:
1. SUMMARY: A brief high-level overview (2-4 sentences) covering the research question, approach, and overall conclusion. Do NOT list specific results here — those belong in KEY FINDINGS.
2. KEY FINDINGS: The most important specific findings (3-5 brief bullet points).{figure_instruction}
3. CONTEXT: One paragraph on how this research fits into the broader field. Incorporate the citation metrics to assess the paper's impact. Based on your knowledge, indicate whether this work is: well-accepted in the field, controversial, contradicted by other studies, preliminary/unsupported by other work, or if you cannot assess its reception. Be specific about any known controversies or supporting/contradicting evidence.{acronym_instruction}"""

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompts[knowledge_level],
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse the response - handle markdown headers like "## 1. SUMMARY"
        summary = ""
        key_findings = []
        context = ""
        acronyms = []

        lines = response_text.split("\n")
        current_section = ""

        for line in lines:
            line_stripped = line.strip()
            line_upper = line_stripped.upper()

            # Check for section headers (with or without markdown ##)
            clean_line = line_upper.lstrip("#").strip()

            if "SUMMARY" in clean_line and ("1." in clean_line or clean_line.startswith("SUMMARY")):
                current_section = "summary"
                inline = _extract_inline_content(line_stripped, "SUMMARY")
                if inline:
                    summary = inline
                continue
            elif "KEY FINDINGS" in clean_line or "FINDINGS" in clean_line and "2." in clean_line:
                current_section = "findings"
                inline = _extract_inline_content(line_stripped, "FINDINGS")
                if inline:
                    finding = inline.lstrip("-*• ").strip()
                    if finding:
                        key_findings.append(finding)
                continue
            elif "CONTEXT" in clean_line and ("3." in clean_line or clean_line.startswith("CONTEXT")):
                current_section = "context"
                inline = _extract_inline_content(line_stripped, "CONTEXT")
                if inline:
                    context = inline
                continue
            elif "ACRONYM" in clean_line and ("4." in clean_line or clean_line.startswith("ACRONYM")):
                current_section = "acronyms"
                inline = _extract_inline_content(line_stripped, "ACRONYM")
                if inline and ":" in inline:
                    acronyms.append(inline)
                continue

            # Add content to the appropriate section
            if current_section == "summary" and line_stripped:
                if summary:
                    summary += "\n" + line_stripped
                else:
                    summary = line_stripped
            elif current_section == "findings" and line_stripped:
                # Parse bullet points (-, *, •)
                if line_stripped.startswith(("-", "*", "•")):
                    finding = line_stripped.lstrip("-*• ").strip()
                    if finding:
                        key_findings.append(finding)
            elif current_section == "context" and line_stripped:
                if context:
                    context += "\n" + line_stripped
                else:
                    context = line_stripped
            elif current_section == "acronyms" and line_stripped:
                # Parse acronym entries (-, *, •, or plain lines with ":")
                entry = line_stripped.lstrip("-*• ").strip()
                if entry and ":" in entry:
                    acronyms.append(entry)

        # Clean up
        summary = summary.strip()
        context = context.strip()
        key_findings = [f for f in key_findings if f]
        acronyms = [a for a in acronyms if a]

        return {
            "summary": summary,
            "key_findings": key_findings,
            "context": context,
            "acronyms": acronyms,
        }

    async def detect_language(self, text: str) -> str:
        """Detect the language of the given text."""
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": f"What language is this text written in? Respond with only the language name.\n\n{text[:500]}"
                }
            ]
        )

        return message.content[0].text.strip()
