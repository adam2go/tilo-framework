from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Tilo Framework"
    database_url: str = "sqlite:///./tilo.db"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4.1-mini"
    default_embedding_model: str = "text-embedding-3-small"
    jwt_secret: str = "change-me"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
