import logging

import html2text
import httpx
from google.genai import types
from pydantic import TypeAdapter

from cori.config import get_genai_client, settings
from cori.models.questionnaire import Question, QuestionnaireRequest, QuestionnaireResponse

_question_list_adapter = TypeAdapter(list[Question])

logger = logging.getLogger(__name__)

# Always-asked identity and background questions.
BASE_QUESTIONS: list[Question] = [
    Question(
        id="full_name",
        text="What is your full name?",
        category="personal_info",
        input_type="text",
    ),
    Question(
        id="email",
        text="What is your email address?",
        category="personal_info",
        input_type="text",
    ),
    Question(
        id="current_role",
        text="What is your current job title or role?",
        category="experience",
        input_type="text",
    ),
    Question(
        id="years_experience",
        text="How many years of relevant experience do you have?",
        category="experience",
        input_type="text",
    ),
]

# Used when no job context is available or Gemini is unavailable.
FALLBACK_QUESTIONS: list[Question] = [
    Question(
        id="key_achievement",
        text="Describe your most relevant professional achievement.",
        category="experience",
        input_type="textarea",
    ),
    Question(
        id="technical_skills",
        text="What are your key skills relevant to this type of role?",
        category="skills",
        input_type="textarea",
    ),
    Question(
        id="why_interested",
        text="Why are you interested in this role and company?",
        category="motivation",
        input_type="textarea",
    ),
    Question(
        id="unique_value",
        text="What unique value would you bring to this position?",
        category="motivation",
        input_type="textarea",
    ),
]

DYNAMIC_PROMPT = """
Analyze the following job posting and generate exactly 4 questions that will
help a candidate provide specific, relevant details for a personalized cover letter.

Each question should target a concrete skill, experience, or quality mentioned
in the job posting. Avoid vague or generic questions — reference specific
technologies, responsibilities, or qualifications from the posting.

Distribute questions across these categories:
- "experience" (1-2 questions): past roles, projects, or achievements related to key requirements
- "skills" (1 question): specific technical skills, tools, or methodologies from the posting
- "motivation" (1 question): why they're drawn to this specific role, team, or company mission

Use short snake_case ids (e.g. "kubernetes_experience"). Address the candidate
directly with "you/your". Always set input_type to "textarea".

{company_line}

Job posting:
---
{job_text}
---
"""


_html_converter = html2text.HTML2Text()
_html_converter.ignore_links = True
_html_converter.ignore_images = True
_html_converter.body_width = 0


async def _fetch_job_posting(url: str) -> str | None:
    """Fetch and extract text from a job posting URL."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "html" in content_type:
                return _html_converter.handle(resp.text).strip()[:10_000]
            return resp.text[:10_000]
    except httpx.HTTPError:
        logger.warning("Failed to fetch job posting from %s", url)
        return None


async def _generate_dynamic_questions(
    job_text: str,
    company_name: str | None,
) -> list[Question]:
    """Use Gemini to produce questions tailored to the job posting."""
    if not settings.gemini_api_key:
        logger.warning("No Gemini API key — using fallback questions")
        return FALLBACK_QUESTIONS

    company_line = f"The company is: {company_name}" if company_name else ""
    prompt = DYNAMIC_PROMPT.format(job_text=job_text[:8_000], company_line=company_line)

    try:
        client = get_genai_client()
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Question],
            ),
        )
        return _question_list_adapter.validate_json(response.text)
    except Exception:
        logger.exception("Dynamic question generation failed — using fallback")
        return FALLBACK_QUESTIONS


async def generate_questions(request: QuestionnaireRequest) -> QuestionnaireResponse:
    job_text = request.job_description

    # If only a URL was provided, try to scrape the posting.
    if not job_text and request.job_url:
        job_text = await _fetch_job_posting(str(request.job_url))

    if job_text:
        dynamic = await _generate_dynamic_questions(job_text, request.company_name)
    else:
        dynamic = FALLBACK_QUESTIONS

    # Pass back the description only when we fetched it from a URL (saves the frontend a refetch).
    fetched_from_url = not request.job_description and request.job_url and job_text is not None

    return QuestionnaireResponse(
        questions=BASE_QUESTIONS + dynamic,
        job_description=job_text if fetched_from_url else None,
    )
