import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Call Quality Control AI"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "call_qc"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/call_qc"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/call_qc"
    REDIS_URL: str = "redis://localhost:6379/0"
    GROQ_API_KEY: str = ""
    GOOGLE_DRIVE_SOURCE_FOLDER_ID: str = ""
    GOOGLE_DRIVE_WORKING_FOLDER_ID: str = ""
    GOOGLE_SHEET_ID: str = ""
    GOOGLE_CREDENTIALS_PATH: str = "credentials.json"
    LOCAL_STORAGE_DIR: str = "storage"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_LANGUAGE: str = "ru"
    WHISPER_INITIAL_PROMPT: str = (
        "автосервис, СТО, ремонт автомобиля, VIN-код, пробег, диагностика, запчасти, история обслуживания, запись на СТО, X-Trail, Qashqai"
    )

settings = Settings()
