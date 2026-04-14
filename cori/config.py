import functools

from google import genai
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


settings = Settings()


@functools.cache
def get_genai_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)
