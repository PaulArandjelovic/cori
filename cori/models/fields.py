from typing import Annotated

from pydantic import Field

CompanyName = Annotated[str, Field(max_length=200)]
JobDescription = Annotated[str, Field(max_length=15_000)]
