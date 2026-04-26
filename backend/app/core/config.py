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
    llm_enabled: bool = False
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    google_api_key: str = ""
    xai_api_key: str = ""
    mistral_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    together_api_key: str = ""
    qwen_api_key: str = ""
    tencent_api_key: str = ""
    moonshot_api_key: str = ""
    zhipu_api_key: str = ""
    jwt_secret: str = "change-me"
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_webhook_url: str = ""
    public_app_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
