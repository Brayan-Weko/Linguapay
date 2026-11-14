"""Configuration settings for LinguaPay Core API."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LINGUAPAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    host: str = "127.0.0.1"  # nosec B104 - default localhost, overridden by LINGUAPAY_HOST
    port: int = 8000
    ai_provider: str = "glossary_only"  # "gemini" | "ollama" | "auto" | "glossary_only"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ai_timeout_seconds: float = 8.0
    strict_verifier: bool = True
    log_pii: bool = False
    linguistics_dir: Path = REPO_ROOT / "linguistics"


settings = Settings()
