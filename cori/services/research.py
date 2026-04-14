import logging

from typing import Final

from google.genai import errors as genai_errors, types
from pydantic import ValidationError

from cori.config import get_genai_client, settings
from cori.models.research import CompanyContext, ResearchResult, Source

logger = logging.getLogger(__name__)

RESEARCH_PROMPT: Final[str] = (
    'Research the company "{company_name}" and extract structured information.\n'
    "{job_context}\n"
    "Only include facts that are clearly supported by search results — do not "
    "guess or fabricate details."
)

_search_tool: Final = types.Tool(google_search=types.GoogleSearch())


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
    job_context = ""
    job_context += f"The role is: {job_title}\n" if job_title else ""
    job_context += f"Job posting URL: {job_url}\n" if job_url else ""

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
                response_schema=ResearchResult,
                temperature=0.2,
            ),
        )

        result = ResearchResult.model_validate_json(response.text)
        sources = _extract_sources(response.candidates[0])

        return CompanyContext(
            **result.model_dump(),
            name=company_name,
            sources=sources,
        )
    except (genai_errors.APIError, ValueError, ValidationError):
        logger.exception("Company research failed for %s", company_name)
        return CompanyContext(name=company_name, confidence="low")
