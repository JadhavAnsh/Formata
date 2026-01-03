# /ingest endpoint
from fastapi import APIRouter, UploadFile, File, HTTPException, status
import shutil
import os

from app.jobs.store import job_store
from app.models.response import JobResponse
from app.utils.file_utils import ensure_directory, get_file_extension
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=JobResponse)
async def ingest_data(file: UploadFile = File(...)):
    """
    STEP 1: User Uploads File
    STEP 2: Job Created (job_id)
    - Validates file format
    - Creates job entry
    - Saves file to storage
    - Returns job_id for tracking
    """
    try:
        # Validate file extension
        extension = get_file_extension(file.filename)
        valid_extensions = [".csv", ".json", ".xlsx", ".xls", ".md"]
        
        if extension not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported: {', '.join(valid_extensions)}"
            )
        
        # Ensure upload directory exists
        ensure_directory(settings.upload_dir)
        
        # Create job entry
        job_id = job_store.create_job(file.filename, "")
        
        # Save uploaded file
        file_path = os.path.join(settings.upload_dir, f"{job_id}_{file.filename}")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            await file.close()
        
        # Update file path in job
        job = job_store.get_job(job_id)
        if job:
            job.file_path = file_path
        
        logger.info(f"File ingested successfully. Job ID: {job_id}")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="File ingested successfully. Use /status/{job_id} to check processing status."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting file: {str(e)}"
        )
