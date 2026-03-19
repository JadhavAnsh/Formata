# /ingest endpoint
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
import shutil
import os
from datetime import datetime

from app.jobs.store import job_store
from app.guards.appwrite_auth import verify_appwrite_session
from app.models.response import JobResponse
from app.utils.file_utils import ensure_directory, get_file_extension
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter(prefix="/ingest", tags=["ingest"])


from app.models.request import IngestRequest
from app.services.appwrite_db import appwrite_db
import uuid

@router.post("", response_model=JobResponse)
async def ingest_data(
    request: IngestRequest,
    user: dict = Depends(verify_appwrite_session)
):
    """
    STEP 1: Register file from Appwrite Storage
    STEP 2: Job Created (job_id) in Appwrite DB
    - Validates file ID exists (implicitly by being passed)
    - Creates job entry in Appwrite DB
    - Returns job_id for tracking
    """
    try:
        user_id = user["$id"]
        job_id = str(uuid.uuid4())
        
        # Prepare job data for Appwrite
        job_data = {
            "user_id": user_id,
            "file_id": request.file_id,
            "file_name": request.file_name,
            "file_size": request.file_size or 0,
            "file_type": request.file_type or get_file_extension(request.file_name),
            "status": "pending",
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "metadata": "{}" # Appwrite usually prefers strings or JSON objects
        }
        
        # Create job document in Appwrite DB
        appwrite_db.create_job_document(job_id, job_data)
        
        # Sync with in-memory store for now (if still used)
        job_store.create_job(request.file_name, f"appwrite://{request.file_id}", user_id, job_id)
        
        logger.info(f"File registered successfully. Job ID: {job_id}, File ID: {request.file_id}")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="File registered successfully. Use /status/{job_id} to check processing status."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting file: {str(e)}"
        )
