from typing import Literal

from pydantic import BaseModel, Field

from cori.models.fields import CompanyName, JobDescription


class QuestionnaireRequest(BaseModel):
    job_description: JobDescription
    company_name: CompanyName | None = None


class Question(BaseModel):
    id: str = Field(description="Short snake_case identifier, e.g. 'kubernetes_experience'")
    text: str = Field(
        description="Question addressing the candidate directly with you/your pronouns"
    )
    category: Literal["personal_info", "experience", "skills", "motivation"]
    input_type: Literal["text", "textarea"] = Field(
        description="Use 'text' for short factual answers, 'textarea' for detailed responses"
    )


class QuestionnaireResponse(BaseModel):
    questions: list[Question]
