from fastapi import APIRouter

from cori.models.cover_letter import CoverLetterResponse, GenerateRequest
from cori.services.generator import generate_cover_letter
from cori.services.research import research_company

router = APIRouter()


@router.post("/cover-letter/generate")
async def generate(request: GenerateRequest) -> CoverLetterResponse:
    company_context = await research_company(
        company_name=request.company_name,
        job_title=request.job_title,
        job_url=request.job_url,
    )

    cover_letter = await generate_cover_letter(
        answers=request.answers,
        company_context=company_context,
        job_description=request.job_description,
        tone=request.tone,
    )

    return CoverLetterResponse(cover_letter=cover_letter, company_context=company_context)
