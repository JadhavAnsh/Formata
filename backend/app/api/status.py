# /status/{job_id} endpoint
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from app.jobs.store import job_store, JobStatus
from app.guards.appwrite_auth import verify_appwrite_session
from app.utils.logger import logger
from app.utils.job_utils import get_job_with_fallback

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
) -> Dict[str, Any]:
    """
    STEP 6: Progress Updated Continuously
    - Returns current job status
    - Progress: 0.0 (not started) to 1.0 (complete)
    - Status: pending | processing | completed | failed | cancelled
    """
    try:
        job = await get_job_with_fallback(job_id)
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
        
        return job.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job status {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job status: {str(e)}"
        )
