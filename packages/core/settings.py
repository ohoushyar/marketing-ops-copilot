from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load env vars + optionally .env file at repo root
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # API (server)
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # API (client default for CLI)
    api_base_url: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("API_BASE_URL", "api_base_url"),
    )

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices(
            "OLLAMA_URL",
            "OLLAMA_BASE_URL",
            "ollama_base_url",
        ),
    )
    ollama_chat_model: str = Field(
        default="llama3.2:1b",
        validation_alias=AliasChoices(
            "OLLAMA_CHAT_MODEL",
            "ollama_chat_model",
        ),
    )
    ollama_embed_model: str = Field(
        default="nomic-embed-text",
        validation_alias=AliasChoices(
            "OLLAMA_EMBED_MODEL",
            "ollama_embed_model",
        ),
    )

    # RAG
    rag_top_k: int = Field(
        default=8,
        validation_alias=AliasChoices("RAG_TOP_K", "rag_top_k"),
    )
    rag_min_sim: float = Field(
        default=0.25,
        validation_alias=AliasChoices("RAG_MIN_SIM", "rag_min_sim"),
    )

    # Embeddings
    embed_dim: int = Field(
        default=768,
        validation_alias=AliasChoices("EMBED_DIM", "embed_dim"),
    )

    # Database
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )

    # Analytics / logging safety limits
    analytics_max_rows: int = 50

    # Auth
    # Use JSON in env for reliability:
    #   COPILOT_API_KEYS=["dev-key"]
    #   COPILOT_API_KEY_MAP={"dev-key":"ohoushyar"}
    copilot_api_keys: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("COPILOT_API_KEYS", "copilot_api_keys"),
    )
    copilot_api_key_map: dict[str, str] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("COPILOT_API_KEY_MAP", "copilot_api_key_map"),
    )


settings = Settings()
