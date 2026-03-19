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
    STEP 2: Job Created in Appwrite DB via JobStore
    """
    try:
        user_id = user["$id"]
        
        # Create job via JobStore (which handles Appwrite DB persistence)
        job_id = job_store.create_job(
            file_name=request.file_name,
            file_path=f"appwrite://{request.file_id}",
            user_id=user_id
        )
        
        logger.info(f"File registered successfully. Job ID: {job_id}, File ID: {request.file_id}")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="File registered successfully. Use /status/{job_id} to check processing status."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Error ingesting file: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting file: {str(e)}"
        )
