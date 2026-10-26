"""Settings: .env se parhi jaati hain (pydantic-settings)."""
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Store Support API"
    version: str = "1.0.0"
    api_keys: list[str] = []          # .env mein JSON list: ["a","b"]
    llm_api_key: SecretStr
    llm_timeout: float = 30
    cors_origins: list[str] = []


@lru_cache                            # ek hi baar parho, har request par nahi
def get_settings() -> Settings:
    return Settings()
