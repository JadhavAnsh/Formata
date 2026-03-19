# Environment variables and settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (.env file)
    """
    app_name: str = "Formata API"
    debug: bool = False
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Security
    api_keys: str = Field(..., description="Comma-separated list of valid API keys")
    
    # Appwrite
    appwrite_endpoint: str = "http://localhost/v1"
    appwrite_project_id: str = Field(..., description="Appwrite Project ID")
    appwrite_api_key: str = Field(..., description="Appwrite API Key")
    appwrite_database_id: str = Field(..., description="Appwrite Database ID")
    appwrite_jobs_collection_id: str = Field(..., description="Appwrite Jobs Collection ID")
    appwrite_storage_bucket_id: str = Field(..., description="Appwrite Storage Bucket ID")

    @field_validator("api_keys", "appwrite_project_id", "appwrite_api_key", "appwrite_database_id", "appwrite_jobs_collection_id", "appwrite_storage_bucket_id")
    @classmethod
    def ensure_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Setting cannot be empty")
        return v

    @field_validator("api_keys")
    @classmethod
    def ensure_secure_api_key(cls, v: str) -> str:
        if v == "default_key":
            raise ValueError("Insecure 'default_key' is not allowed in production")
        return v
    
    # Storage
    upload_dir: str = "storage/uploads"
    output_dir: str = "storage/outputs"
    error_dir: str = "storage/errors"
    
    # Limits
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # AI/ML settings (optional)
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Optional: Vector DB for embeddings
    vector_db_url: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global settings instance
settings = Settings()
