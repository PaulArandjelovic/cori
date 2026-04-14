from fastapi import APIRouter

from cori.models.questionnaire import QuestionnaireRequest, QuestionnaireResponse
from cori.services.questionnaire import generate_questions

router = APIRouter()


@router.post("/questionnaire")
async def questionnaire(request: QuestionnaireRequest) -> QuestionnaireResponse:
    return await generate_questions(request)
