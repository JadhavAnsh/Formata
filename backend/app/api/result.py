# /result/{job_id} endpoint
# JOB FLOW: Step 7 - Final Output + Error Report Saved + Step 8 - User Downloads Result
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from typing import Dict, Any
import os

from app.jobs.store import job_store, JobStatus
from app.utils.logger import logger

router = APIRouter(prefix="/result", tags=["result"])


@router.get("/{job_id}/download")
async def download_job_result(job_id: str):
    """
    STEP 8: User Downloads Result
    - Download processed/cleaned data as file
    - Returns CSV or JSON based on output format
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job.status.value} state. Result file not available yet."
            )
        
        # Get output file path from job result
        if not job.result or not job.result.get("output_path"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found in job result"
            )
        
        output_path = job.result["output_path"]
        
        if not os.path.exists(output_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found on disk"
            )
        
        # Determine media type based on file extension
        file_extension = output_path.split('.')[-1].lower()
        media_type = "text/csv" if file_extension == "csv" else "application/json"
        filename = f"{job_id}_clean.{file_extension}"
        
        logger.info(f"Downloading result file for job {job_id}")
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading job result {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading job result: {str(e)}"
        )
