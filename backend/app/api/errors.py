# /errors/{job_id} endpoint
# JOB FLOW: Step 5 - Errors Stream via SSE (Live) + Error Report Saved
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from typing import Dict, Any
import os

from app.jobs.store import job_store
from app.guards.appwrite_auth import verify_appwrite_session
from app.utils.logger import logger

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get("/{job_id}/download")
async def download_error_report(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
):
    """
    Download error report file
    - Returns error report as downloadable text file
    - Only available if job has errors
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Verify ownership
        if job.user_id != user["$id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job"
            )
        
        # Check if job has errors
        if not job.errors or len(job.errors) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No errors to report for this job"
            )
        
        # Check if error report file exists
        error_path = os.path.join("storage/errors", f"{job_id}_errors.txt")
        if not os.path.exists(error_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error report file not found"
            )
        
        logger.info(f"Downloading error report for job {job_id}")
        return FileResponse(
            path=error_path,
            filename=f"{job_id}_errors.txt",
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading error report {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading error report: {str(e)}"
        )


# TODO: Implement SSE endpoint for live error streaming
@router.get("/stream-errors/{job_id}")
async def stream_job_errors(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
):
    """
    STEP 5: Errors Stream via SSE (Live)
    - Server-Sent Events endpoint for live error streaming
    - Streams errors as they occur during processing
    - Implementation pending
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Verify ownership
        if job.user_id != user["$id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job"
            )
        
        # Implementation pending
        return {"message": "SSE streaming placeholder"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming errors {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming errors: {str(e)}"
        )
