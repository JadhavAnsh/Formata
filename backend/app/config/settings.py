# Environment variables and settings
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (.env file)
    """
    # Application
    app_name: str
    debug: bool
    
    # API
    api_host: str
    api_port: int
    
    # Security
    api_keys: str  # Comma-separated list of valid API keys
    
    # Storage
    upload_dir: str
    output_dir: str
    error_dir: str
    
    # Processing
    max_file_size: int
    
    # Optional: Database
    database_url: Optional[str] = None
    
    # Optional: Vector DB for embeddings
    vector_db_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
