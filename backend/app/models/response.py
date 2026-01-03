# Output schemas
from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class JobResponse(BaseModel):
    """Response model for job operations"""
    job_id: str
    status: str
    message: Optional[str] = None


class StatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    progress: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ResultResponse(BaseModel):
    """Response model for job results"""
    job_id: str
    data: Any
    metadata: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Response model for errors"""
    job_id: str
    errors: List[str]
    timestamp: datetime
