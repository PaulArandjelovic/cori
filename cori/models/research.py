from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    url: str
    title: str


class ResearchResult(BaseModel):
    """Schema for Gemini structured output."""

    description: str | None = Field(
        default=None, description="One-paragraph company description, null if not enough info"
    )
    industry: str | None = Field(
        default=None, description="The company's industry or sector, null if unknown"
    )
    products_services: list[str] = Field(
        default=[], description="Main products or services"
    )
    culture_signals: list[str] = Field(
        default=[],
        description="Notable culture aspects, values, or recent initiatives",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description=(
            "high if multiple sources agree on key facts, "
            "medium if limited info found, "
            "low if mostly uncertain"
        )
    )


class CompanyContext(ResearchResult):
    name: str
    sources: list[Source] = []
