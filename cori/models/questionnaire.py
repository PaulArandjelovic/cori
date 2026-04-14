from typing import Literal

from pydantic import BaseModel, HttpUrl, model_validator


class QuestionnaireRequest(BaseModel):
    job_url: HttpUrl | None = None
    job_description: str | None = None
    company_name: str | None = None

    @model_validator(mode="after")
    def at_least_one_input(self) -> "QuestionnaireRequest":
        if not any((self.job_url, self.job_description, self.company_name)):
            raise ValueError(
                "Provide at least one of job_url, job_description, or company_name"
            )
        return self


class Question(BaseModel):
    id: str
    text: str
    category: Literal["personal_info", "experience", "skills", "motivation"]
    input_type: Literal["text", "textarea"]
    required: bool = True


class QuestionnaireResponse(BaseModel):
    questions: list[Question]
    job_description: str | None = None
