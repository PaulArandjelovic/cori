from typing import Literal

from pydantic import BaseModel


class Source(BaseModel):
    url: str
    title: str


class CompanyContext(BaseModel):
    name: str
    description: str | None = None
    industry: str | None = None
    products_services: list[str] = []
    culture_signals: list[str] = []
    sources: list[Source] = []
    confidence: Literal["high", "medium", "low"]
