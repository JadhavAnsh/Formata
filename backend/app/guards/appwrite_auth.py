# Appwrite Authentication Guard
from fastapi import HTTPException, status, Depends, Header, Query
from typing import Optional
from appwrite.client import Client
from appwrite.services.account import Account
from app.config.settings import settings
from app.utils.logger import logger

# Initialize Appwrite client
client = Client()
client.set_endpoint(settings.appwrite_endpoint)
client.set_project(settings.appwrite_project_id)
client.set_key(settings.appwrite_api_key)

async def verify_appwrite_session(
    x_appwrite_jwt: Optional[str] = Header(None, description="Appwrite JWT token"),
    jwt: Optional[str] = Query(None, description="Appwrite JWT token as query param")
) -> dict:
    """
    Verify Appwrite session using the provided JWT from the frontend.
    Accepts JWT from 'X-Appwrite-JWT' header OR 'jwt' query parameter.
    Returns user details if valid.
    """
    token = x_appwrite_jwt or jwt
    
    if not token:
        logger.warning("verify_appwrite_session: No token provided in header or query")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Appwrite JWT. Please provide X-Appwrite-JWT header or jwt query parameter.",
        )
    
    try:
        # Create a new client per request to use the JWT
        user_client = Client()
        user_client.set_endpoint(settings.appwrite_endpoint)
        user_client.set_project(settings.appwrite_project_id)
        user_client.set_jwt(token)
        
        account = Account(user_client)
        user = account.get()
        
        return user
        
    except Exception as e:
        logger.error(f"Appwrite Auth Error (Token: {token[:10]}...): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Appwrite session: {str(e)}",
        )
