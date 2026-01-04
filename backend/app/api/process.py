# /process/{job_id} endpoint
# JOB FLOW: Step 3 - Background Worker Starts + Step 4 - Pipeline Executes Step-by-Step
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.jobs.store import job_store, JobStatus
from app.jobs.worker import start_background_job
from app.models.response import JobResponse
from app.utils.logger import logger

router = APIRouter(prefix="/process", tags=["process"])


class ProcessConfig(BaseModel):
    """Configuration for processing pipeline"""
    normalize: bool = True
    remove_duplicates: bool = True
    remove_outliers: bool = False
    filters: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    output_format: str = "csv"
    detect_data_quality_issues: bool = True


@router.post("/{job_id}", response_model=JobResponse)
async def process_job(job_id: str, config: ProcessConfig = ProcessConfig()):
    """
    STEP 3: Background Worker Starts
    STEP 4: Pipeline Executes Step-by-Step
    - Validates job exists and is in pending state
    - Starts async background worker
    - Pipeline steps:
      1. Parse input file
      2. Normalize data types
      3. Apply filters
      4. Remove noise
      5. Validate results
    """
    try:
        # Check if job exists
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check if job is in valid state to process
        if job.status != JobStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job.status.value} state. Cannot process."
            )
        
        # Prepare config dictionary
        config_dict = config.dict()
        
        # Start background processing
        start_background_job(job_id, job.file_path, config_dict)
        
        logger.info(f"Processing started for job {job_id}")
        
        return JobResponse(
            job_id=job_id,
            status="processing",
            message="Processing started. Monitor progress at /status/{job_id}. Errors stream via SSE at /stream-errors/{job_id}."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting processing for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting processing: {str(e)}"
        )
