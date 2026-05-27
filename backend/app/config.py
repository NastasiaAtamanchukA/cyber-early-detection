from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cyber Early Detection"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./cyber_early_detection.db"
    ml_service_url: str = "http://localhost:8001"
    alert_threshold: float = Field(default=0.72, ge=0.0, le=1.0)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://cyber-early-detection.ru",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
