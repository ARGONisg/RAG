"""
Centralized application settings loaded from environment variables / .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All tunables in one place.  Values come from environment variables first,
    then fall back to the `.env` file at the project root.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ────────────────────────────────────────────────────────────────
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model_name: str = "llama3"

    # ── Retrieval ──────────────────────────────────────────────────────────
    similarity_threshold: float = 0.65

    # ── CORS ───────────────────────────────────────────────────────────────
    cors_origin: str = "http://localhost:3000"

    # ── Uploads ────────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"


settings = Settings()
