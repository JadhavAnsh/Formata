# /result/{job_id} endpoint
# JOB FLOW: Step 7 - Final Output + Error Report Saved + Step 8 - User Downloads Result
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.jobs.store import job_store, JobStatus
from app.utils.logger import logger

router = APIRouter(prefix="/result", tags=["result"])


@router.get("/{job_id}")
async def get_job_result(job_id: str) -> Dict[str, Any]:
    """
    STEP 7: Final Output + Error Report Saved
    - Returns processed data and error report
    - Only available when job is completed
    - Includes full metadata and processing summary
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
                detail=f"Job is in {job.status.value} state. Result not available yet."
            )
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "result": job.result,
            "errors": job.errors,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job result {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job result: {str(e)}"
        )


# TODO: Implement file download endpoint
@router.get("/{job_id}/download")
async def download_job_result(job_id: str):
    """
    STEP 8: User Downloads Result
    - Download processed data as file
    - Includes error report
    - Implementation pending
    """
    pass
