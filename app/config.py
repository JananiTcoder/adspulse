import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    COMPOSIO_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./adspulse.db"
    SECRET_KEY: str = "change-me-in-production"
    DEFAULT_CUSTOMER_ID: str = "5313006442"
    GMAIL_ADDRESS: str = "jananiroshini2005@gmail.com"
    GMAIL_APP_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
