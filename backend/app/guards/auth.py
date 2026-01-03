# API Key Authentication Guard
from fastapi import HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from app.config.settings import settings

# Define API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Verify API key from request header.
    Raises HTTPException if API key is missing or invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if API key matches configured key(s)
    valid_keys = settings.api_keys.split(",") if settings.api_keys else []
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key
