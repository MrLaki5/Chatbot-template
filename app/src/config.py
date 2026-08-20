from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODEL_BASE_URL: str = "https://api.openai.com/v1"
    MODEL_NAME: str = "gpt-4.1-mini"
    MODEL_API_KEY: str
    SYSTEM_PROMPT: str = "You are a helpful assistant."

    REDIS_URL: str = "redis:6379"
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Signs the session cookie. Override in any real deployment.
    SESSION_SECRET_KEY: str = "chatbot-template-dev-secret-change-me"
    SESSION_TTL_HOURS: int = 24

    class Config:
        env_file = ".env"


settings = Settings()
