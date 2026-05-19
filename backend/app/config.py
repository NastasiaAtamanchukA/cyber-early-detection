from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cyber Early Detection API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg2://cyber:cyber@db:5432/cyberlogs"
    ml_predict_url: str = "http://ml-service:8001/predict"
    ml_train_url: str = "http://ml-service:8001/train"
    frontend_origins: str = "http://localhost:3000,http://localhost:5173"
    enable_auth: bool = False
    api_key: str = "change-me"
    alert_threshold: float = 0.62
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
