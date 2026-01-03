# /errors/{job_id} endpoint
# JOB FLOW: Step 5 - Errors Stream via SSE (Live) + Error Report Saved
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.jobs.store import job_store
from app.utils.logger import logger

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get("/{job_id}")
async def get_job_errors(job_id: str) -> Dict[str, Any]:
    """
    STEP 5: Errors Stream via SSE (Live) + Error Report Saved
    - Returns all errors encountered during processing
    - Errors are collected and saved with job result
    - Use this to get full error report after processing completes
    
    For live error streaming, use SSE endpoint: /stream-errors/{job_id}
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "error_count": len(job.errors),
            "errors": job.errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job errors {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job errors: {str(e)}"
        )


# TODO: Implement SSE endpoint for live error streaming
@router.get("/stream-errors/{job_id}")
async def stream_job_errors(job_id: str):
    """
    STEP 5: Errors Stream via SSE (Live)
    - Server-Sent Events endpoint for live error streaming
    - Streams errors as they occur during processing
    - Implementation pending
    """
    pass
