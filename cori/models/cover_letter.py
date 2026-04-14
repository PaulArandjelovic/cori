from typing import Literal

from pydantic import BaseModel

from cori.models.research import CompanyContext


class GenerateRequest(BaseModel):
    company_name: str
    job_title: str | None = None
    job_url: str | None = None
    job_description: str | None = None
    answers: dict[str, str]
    tone: Literal["formal", "conversational", "confident"] = "formal"


class CoverLetterResponse(BaseModel):
    cover_letter: str
    company_context: CompanyContext
