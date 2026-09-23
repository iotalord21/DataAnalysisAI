import os
from pathlib import Path
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Provider selection
    llm_provider: Literal["gemini", "openai", "anthropic", "ollama"] = "gemini"

    # Google Gemini (Primary)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"

    # OpenAI (Optional)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # Anthropic (Optional)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # Ollama / Local (Optional)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Server Settings
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Execution & Security
    execution_timeout_seconds: int = 25
    max_verification_retries: int = 2
    max_sample_rows_for_prompt: int = 5

    # Directory Paths
    backend_dir: Path = Path(__file__).resolve().parent.parent
    uploads_dir: Path = Path(__file__).resolve().parent / "storage" / "uploads"
    reports_dir: Path = Path(__file__).resolve().parent / "storage" / "reports"
    sample_data_dir: Path = Path(__file__).resolve().parent / "storage" / "sample_data"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Ensure directories exist
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
settings.sample_data_dir.mkdir(parents=True, exist_ok=True)
