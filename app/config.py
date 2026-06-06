import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    COMPOSIO_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./adspulse.db"
    SECRET_KEY: str = "change-me-in-production"
    DEFAULT_CUSTOMER_ID: str = "5313006442"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
