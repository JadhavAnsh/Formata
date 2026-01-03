# Environment variables and settings
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Application
    app_name: str = "Formata"
    debug: bool = False
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    api_keys: str = "KuU2/uCTTP1IwvrDeNSquSPmT4w1LF53829uxCt4wDAA"  # Comma-separated list of valid API keys
    
    # Storage
    upload_dir: str = "storage/uploads"
    output_dir: str = "storage/outputs"
    error_dir: str = "storage/errors"
    
    # Processing
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Optional: Database
    database_url: Optional[str] = None
    
    # Optional: Vector DB for embeddings
    vector_db_url: Optional[str] = None
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
