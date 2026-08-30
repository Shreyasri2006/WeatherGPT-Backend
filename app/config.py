from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WeatherGPT API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    http_timeout_seconds: float = 15.0
    historical_dataset_path: str = "data/india_daily_weather.csv"
    imd_warning_url: str = ""
    imd_api_key: str = ""
    llm_endpoint: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    wis2_broker: str = ""
    wis2_port: int = 8883
    wis2_topic: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def historical_path(self) -> Path:
        return Path(self.historical_dataset_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
