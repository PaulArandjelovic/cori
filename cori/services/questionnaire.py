import logging

from typing import Final

from google.genai import errors as genai_errors, types
from pydantic import TypeAdapter, ValidationError

from cori.config import get_genai_client, settings
from cori.models.questionnaire import Question, QuestionnaireRequest, QuestionnaireResponse

_question_list_adapter = TypeAdapter(list[Question])

logger = logging.getLogger(__name__)

# Always-asked identity and background questions.
BASE_QUESTIONS: Final[list[Question]] = [
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
FALLBACK_QUESTIONS: Final[list[Question]] = [
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

DYNAMIC_PROMPT: Final[str] = """
Generate exactly 4 questions for a candidate applying to the job posting below.
{company_line}

Their answers will feed directly into a cover letter generator, so each question
should elicit a concrete, personal story or detail — not a yes/no or a list.
Reference specific technologies, responsibilities, or qualifications from the
posting so the candidate knows exactly what to address.

The candidate will already be asked these separately — do NOT overlap:
{base_questions}

Distribute across these categories:
- "experience" (1-2): ask about a past project, role, or achievement that maps
  to a specific requirement in the posting
- "skills" (1): ask about hands-on experience with a technology, tool, or
  methodology named in the posting
- "motivation" (1): ask what draws them to this specific role, team, or mission

Job posting:
---
{job_text}
---
"""


async def generate_questions(request: QuestionnaireRequest) -> QuestionnaireResponse:
    """Generate base + dynamic questions tailored to the job posting."""
    company_line = (
        f"The company is: {request.company_name}" if request.company_name else ""
    )
    base_questions = "\n".join(f"- {q.text}" for q in BASE_QUESTIONS)
    prompt = DYNAMIC_PROMPT.format(
        job_text=request.job_description,
        company_line=company_line,
        base_questions=base_questions,
    )

    try:
        client = get_genai_client()
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Question],
                temperature=0.3,
            ),
        )
        dynamic = _question_list_adapter.validate_json(response.text)
    except (genai_errors.APIError, ValidationError, ValueError):
        logger.exception("Dynamic question generation failed — using fallback")
        dynamic = FALLBACK_QUESTIONS

    return QuestionnaireResponse(questions=BASE_QUESTIONS + dynamic)
