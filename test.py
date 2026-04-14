"""End-to-end test: questionnaire -> answers -> cover letter -> markdown file."""

import asyncio
import sys
from pathlib import Path

from cori.models.questionnaire import QuestionnaireRequest
from cori.services.questionnaire import generate_questions
from cori.services.research import research_company
from cori.services.generator import generate_cover_letter

JOB_DESCRIPTION = """\
We are hiring a Backend Engineer to join our infrastructure team. You will:
- Design and build high-throughput REST APIs using Python and FastAPI
- Optimize PostgreSQL queries for large-scale data pipelines
- Mentor junior engineers and participate in code reviews
- Collaborate with SRE teams on reliability and observability

Requirements:
- 5+ years of backend engineering experience
- Strong Python skills, experience with async frameworks (FastAPI, Starlette)
- Deep knowledge of PostgreSQL (indexing, query planning, partitioning)
- Experience with Docker, Kubernetes, and CI/CD pipelines
"""

COMPANY_NAME = "Google"
JOB_TITLE = "Backend Engineer"

# Simulated candidate answers keyed by question id.
ANSWERS = {
    "full_name": "Pavle Doe",
    "email": "pavle@example.com",
    "current_role": "Senior Software Engineer at StartupX",
    "years_experience": "7",
}


async def main() -> None:
    print("=== Step 1: Generating questionnaire ===")
    questionnaire = await generate_questions(
        QuestionnaireRequest(
            job_description=JOB_DESCRIPTION,
            company_name=COMPANY_NAME,
        )
    )

    print(f"Generated {len(questionnaire.questions)} questions:\n")
    for q in questionnaire.questions:
        print(f"  [{q.category}] {q.id}: {q.text}")

    # Fill in dynamic questions with plausible answers.
    dynamic_answers = {
        "experience": (
            "I led the migration of our core platform from Flask to FastAPI, "
            "serving 3M daily requests. I implemented a parallel routing layer "
            "for zero-downtime migration and reduced p95 latency by 40%."
        ),
        "skills": (
            "I optimized a reporting dashboard querying a 200M-row PostgreSQL "
            "events table. Using partial indexes, CTEs, and materialized views "
            "I reduced query times from 12s to under 400ms."
        ),
        "motivation": (
            "I want to work on systems that serve billions of users. I value "
            "rigorous code review and knowledge sharing, which is central to "
            "how I like to work."
        ),
    }

    answers = dict(ANSWERS)
    for q in questionnaire.questions:
        if q.id not in answers:
            answers[q.id] = dynamic_answers.get(q.category, "N/A")

    print(f"\n=== Step 2: Researching {COMPANY_NAME} ===")
    company_context = await research_company(
        company_name=COMPANY_NAME,
        job_title=JOB_TITLE,
    )
    print(f"  Confidence: {company_context.confidence}")
    print(f"  Sources: {len(company_context.sources)}")

    print("\n=== Step 3: Generating cover letter ===")
    cover_letter = await generate_cover_letter(
        answers=answers,
        company_context=company_context,
        job_description=JOB_DESCRIPTION,
        tone="confident",
    )

    # Build markdown output.
    lines = [
        "# Cover Letter\n",
        cover_letter,
        "\n---\n",
        "## Company Research\n",
        f"**Company:** {company_context.name}  ",
        f"**Confidence:** {company_context.confidence}\n",
    ]
    if company_context.description:
        lines.append(f"**Description:** {company_context.description}\n")
    if company_context.industry:
        lines.append(f"**Industry:** {company_context.industry}\n")
    if company_context.products_services:
        lines.append("**Products/Services:** " + ", ".join(company_context.products_services) + "\n")
    if company_context.culture_signals:
        lines.append("\n**Culture Signals:**\n")
        for signal in company_context.culture_signals:
            lines.append(f"- {signal}")
    if company_context.sources:
        lines.append("\n\n**Sources:**\n")
        for src in company_context.sources:
            lines.append(f"- [{src.title}]({src.url})")

    output = Path("output.md")
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {output.resolve()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(1)
