# Environment variables and settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (.env file)
    """
    app_name: str = "Formata API"
    debug: bool = False
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    api_keys: str = "default_key"  # Comma-separated list of valid API keys
    
    # Appwrite
    appwrite_endpoint: str = "http://localhost/v1"
    appwrite_project_id: str = ""
    appwrite_api_key: str = ""
    appwrite_database_id: str = ""
    appwrite_jobs_collection_id: str = ""
    appwrite_storage_bucket_id: str = ""
    
    # Storage
    upload_dir: str = "storage/uploads"
    output_dir: str = "storage/outputs"
    error_dir: str = "storage/errors"
    
    # Limits
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # AI/ML settings (optional)
    openai_api_key: Optional[str] = None
    
    # Optional: Vector DB for embeddings
    vector_db_url: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global settings instance
settings = Settings()
