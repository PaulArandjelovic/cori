import functools
import os
import sys

from google import genai
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    gemini_api_key: str
    gemini_model: str = "gemini-3-flash-preview"

    @model_validator(mode="after")
    def check_required_keys(self):
        if not self.gemini_api_key.strip():
            raise ValueError("GEMINI_API_KEY is empty — check your .env file")
        return self


try:
    settings = Settings()
except Exception as e:
    sys.exit(f"[FATAL] Failed to load settings: {e}")


@functools.cache
def get_genai_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)
