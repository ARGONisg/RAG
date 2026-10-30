"""
Centralized application settings loaded from environment variables / .env file.
"""

from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All tunables in one place. Values come from environment variables first,
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
    llm_model_name: str = "hf.co/chaitanya-rathi/llama-3-8b-rag-grounded:Q4_K_M"

    @field_validator("llm_base_url")
    @classmethod
    def normalize_base_url(cls, v: str) -> str:
        """Ensure the URL has a protocol and ends with /v1."""
        url = v.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            # Default to https for ngrok / remote tunnels, http for localhost
            if "localhost" in url or "127.0.0.1" in url:
                url = f"http://{url}"
            else:
                url = f"https://{url}"
        
        # Ensure it ends with /v1
        url = url.rstrip("/")
        if not url.endswith("/v1"):
            url = f"{url}/v1"
        return url

    # ── Retrieval ──────────────────────────────────────────────────────────
    use_mock_retrieval: bool = False
    chroma_persist_dir: str = "./chroma_db"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    similarity_threshold: float = 0.0
    top_k_chunks: int = 4

    # ── CORS & Server ──────────────────────────────────────────────────────
    cors_origin: str = "http://localhost:3000"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # ── Uploads ────────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"

    # ── Mock mode ──────────────────────────────────────────────────────────
    # When True, the LLM call is simulated with a fake streamer so
    # the full pipeline is testable without a running Ollama instance.
    use_mock_llm: bool = False


settings = Settings()
