"""
Configuration management for the AI Agent application.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # FastAPI Configuration
    environment: str = "development"
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    api_title: str = "Autonomous AI Agent API"
    api_version: str = "1.0.0"

    # LLM Provider Configuration
    llm_provider: str = "ollama"

    # Ollama Configuration (Local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # Common LLM Settings
    temperature: float = 0.7
    max_tokens: int = 2000

    # Gmail Configuration
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_refresh_token: Optional[str] = None

    # Google OAuth (Gmail)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None

    # Slack Configuration
    slack_bot_token: Optional[str] = None
    slack_channel_id: Optional[str] = None

    # Notion Configuration
    notion_api_key: Optional[str] = None
    notion_database_id: Optional[str] = None

    # Database Configuration
    database_url: str = "sqlite:///./app.db"

    # FAISS Vector DB Configuration (Local)
    faiss_index_path: str = "./data/faiss_index"
    embedding_model: str = "text-embedding-ada-002"

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # CORS Configuration
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def model_name(self) -> str:
        return self.ollama_model

    class Config:
        env_file = "backend/.env"
        case_sensitive = False
        protected_namespaces = ('settings_',)

    @property
    def allowed_origins_list(self) -> list:
        """Convert comma-separated origins to list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Create global settings instance
settings = Settings()