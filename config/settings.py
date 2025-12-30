# app/config/settings.py

"""
Global application settings.
Loads values from environment variables using Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # -----------------------
    # Core application config
    # -----------------------
    APP_NAME: str = "TANMIYA AI ENGINE"
    BASE_API_URL: str = "http://localhost:8000"

    #------------------------
    # Tanmiya Backend Base URL
    #------------------------
    TANMIYA_BACKEND_BASE_URL: str
    TANMIYA_BACKEND_TOKEN: str

    # -----------------------
    # Directus API config
    # -----------------------
    DIRECTUS_URL: str
    DIRECTUS_TOKEN: str

    # -----------------------
    # Translation API
    # -----------------------
    TRANSLATION_API_URL: str

    # -----------------------
    # SMTP Email Config
    # -----------------------
    EMAIL_FROM: str
    SMTP_HOST: str
    SMTP_PORT: int = 465
    SMTP_USER: str
    SMTP_PASS: str

    # -----------------------
    # LLM API
    # -----------------------
    LLM_API_URL: str

    # -----------------------
    # PDF Storage
    # -----------------------
    PDF_FOLDER_ID: str | None = None

    # -----------------------
    # Security
    # -----------------------
    SECRET_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
