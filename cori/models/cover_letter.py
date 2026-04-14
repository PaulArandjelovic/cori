from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from cori.models.fields import CompanyName, JobDescription
from cori.models.research import CompanyContext


class GenerateRequest(BaseModel):
    company_name: CompanyName
    job_title: Annotated[str, Field(max_length=200)] | None = None
    job_url: Annotated[str, Field(max_length=2_000)] | None = None
    job_description: JobDescription | None = None
    answers: dict[
        Annotated[str, Field(max_length=500)],
        Annotated[str, Field(max_length=5_000)],
    ]
    tone: Literal["formal", "conversational", "confident"] = "formal"

    @field_validator("answers")
    @classmethod
    def limit_answer_count(cls, v: dict[str, str]) -> dict[str, str]:
        if len(v) > 50:
            raise ValueError("answers must contain at most 50 entries")
        return v


class CoverLetterResponse(BaseModel):
    cover_letter: str
    company_context: CompanyContext
