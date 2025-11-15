# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Application configuration settings"""

    # Database Configuration
    database_url: str

    # Anthropic Configuration
    anthropic_api_key: str
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Embedding Configuration
    embedding_provider: str = "huggingface"  # Options: "huggingface" or "openai"
    embedding_model: str = "all-MiniLM-L6-v2"  # HuggingFace: 384 dimensions, fast and efficient

    # Tavily Web Search
    tavily_api_key: str

    # Google Drive Configuration (OAuth 2.0)
    google_drive_client_id: Optional[str] = None
    google_drive_client_secret: Optional[str] = None
    google_drive_root_folder: str = "UVA_Research_Assistant"

    # GitHub Configuration (OAuth 2.0)
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None

    # JWT Authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days

    # Application Settings
    debug: bool = False
    allowed_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    similarity_threshold: float = 0.4
    max_results: int = 5

    # LangGraph Settings
    max_iterations: int = 3
    enable_detailed_reasoning: bool = True

    # UVA Specific Settings
    uva_base_url: str = "https://virginia.edu"
    uva_it_resources_url: str = "https://its.virginia.edu"

    # Local Storage Settings
    local_storage_path: str = "/app/storage"
    enable_google_drive: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()
