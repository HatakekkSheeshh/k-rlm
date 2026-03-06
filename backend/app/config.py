"""
app/config.py — centralised settings loaded from environment / .env
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_timeout:  int = 120          # seconds — SLM inference can be slow

    # API
    api_prefix:      str = "/api/v1"
    cors_origins:    list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Default model tag (must match Ollama library)
    default_model:   str = "phi3:mini"


settings = Settings()
