from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    client_key: Optional[str] = None
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")

# a single instance to be used throughout the app
settings = Settings()
