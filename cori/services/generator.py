import logging

from cori.config import get_genai_client, settings
from cori.models.research import CompanyContext

logger = logging.getLogger(__name__)

TONE_DESCRIPTIONS = {
    "formal": "professional and formal",
    "conversational": "warm and conversational while remaining professional",
    "confident": "confident and assertive while remaining respectful",
}

GENERATE_PROMPT = """
Write a personalized cover letter for a job application.
The tone should be {tone_description}.

Candidate Information:
{answers_section}

Company Information:
{company_section}
{job_section}

Guidelines:
- Address specific requirements from the job posting using the candidate's actual experience
- Reference the company's products, mission, or culture naturally — don't just list facts
- If company information is limited, focus on the job requirements and candidate strengths
- Keep it concise (3-4 paragraphs)
- Do not fabricate achievements or experiences not provided by the candidate
- Do not include a subject line or date — start with the greeting
- Return the cover letter in markdown format
"""


def _build_company_section(ctx: CompanyContext) -> str:
    """Include only the company context fields we actually have."""
    parts = []
    if ctx.description:
        parts.append(f"About: {ctx.description}")
    if ctx.industry:
        parts.append(f"Industry: {ctx.industry}")
    if ctx.products_services:
        parts.append(f"Products/Services: {', '.join(ctx.products_services)}")
    if ctx.culture_signals:
        parts.append(f"Culture: {', '.join(ctx.culture_signals)}")
    return "\n".join(parts) or "No company information available."


def _build_prompt(
    answers: dict[str, str],
    company_context: CompanyContext,
    job_description: str | None,
    tone: str,
) -> str:
    answers_section = "\n".join(f"- {k}: {v}" for k, v in answers.items())
    company_section = _build_company_section(company_context)
    job_section = (
        f"\nJob Description:\n---\n{job_description[:6_000]}\n---"
        if job_description
        else ""
    )
    tone_description = TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS["formal"])

    return GENERATE_PROMPT.format(
        tone_description=tone_description,
        answers_section=answers_section,
        company_section=company_section,
        job_section=job_section,
    )


async def generate_cover_letter(
    answers: dict[str, str],
    company_context: CompanyContext,
    job_description: str | None = None,
    tone: str = "formal",
) -> str:
    """Generate a cover letter using the LLM."""
    prompt = _build_prompt(answers, company_context, job_description, tone)

    client = get_genai_client()
    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )
    return response.text.strip()
