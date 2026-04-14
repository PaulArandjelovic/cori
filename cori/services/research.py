import json
import logging

from google.genai import types

from cori.config import get_genai_client, settings
from cori.models.research import CompanyContext, Source

logger = logging.getLogger(__name__)

RESEARCH_PROMPT = """
Research the company "{company_name}" and extract structured information.
{job_context}

Only include facts that are clearly supported by search results — do not
guess or fabricate details.

Return a JSON object with:
- "description": one-paragraph company description (null if not enough info)
- "industry": the company's industry or sector (null if unknown)
- "products_services": list of main products or services (empty list if unknown)
- "culture_signals": list of notable culture aspects, values, or recent initiatives
  (empty list if unknown)
- "confidence": "high" if multiple sources agree on key facts, "medium" if limited
  info found, "low" if mostly uncertain

Return ONLY the JSON object.
"""

_search_tool = types.Tool(google_search=types.GoogleSearch())


def _extract_sources(candidate: types.Candidate) -> list[Source]:
    """Pull source URLs from Gemini's grounding metadata."""
    metadata = candidate.grounding_metadata
    if not metadata or not metadata.grounding_chunks:
        return []

    sources = []
    seen = set()
    for chunk in metadata.grounding_chunks:
        if chunk.web and chunk.web.uri and chunk.web.uri not in seen:
            seen.add(chunk.web.uri)
            sources.append(Source(url=chunk.web.uri, title=chunk.web.title or ""))
    return sources


async def research_company(
    company_name: str,
    job_title: str | None = None,
    job_url: str | None = None,
) -> CompanyContext:
    """Use Gemini with Google Search grounding to research a company."""
    job_parts = []
    if job_title:
        job_parts.append(f"The role is: {job_title}")
    if job_url:
        job_parts.append(f"Job posting URL: {job_url}")
    job_context = "\n".join(job_parts)

    prompt = RESEARCH_PROMPT.format(
        company_name=company_name,
        job_context=job_context,
    )

    try:
        client = get_genai_client()
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[_search_tool],
                response_mime_type="application/json",
            ),
        )

        data = json.loads(response.text)
        sources = _extract_sources(response.candidates[0]) if response.candidates else []

        return CompanyContext(
            name=company_name,
            description=data.get("description"),
            industry=data.get("industry"),
            products_services=data.get("products_services", []),
            culture_signals=data.get("culture_signals", []),
            sources=sources,
            confidence=data.get("confidence", "low"),
        )
    except Exception:
        logger.exception("Company research failed for %s", company_name)
        return CompanyContext(name=company_name, confidence="low")
