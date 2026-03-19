# /errors/{job_id} endpoint
# JOB FLOW: Step 5 - Errors Stream via SSE (Live) + Error Report Saved
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from typing import Dict, Any
import os

from app.jobs.store import job_store
from app.guards.appwrite_auth import verify_appwrite_session
from app.services.appwrite_storage import appwrite_storage
from app.config.settings import settings
from app.utils.logger import logger
from app.utils.job_utils import get_job_with_fallback

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get("/{job_id}/download")
async def download_error_report(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
):
    """
    Download error report file
    - Returns error report as downloadable text file
    - Priority: Appwrite Storage (Cloud)
    - Fallback: Local disk
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
        
        # Priority 1: Check Appwrite Storage
        error_file_id = job.metadata.get("error_file_id")
        if error_file_id:
            local_temp_path = os.path.join(settings.error_dir, f"dl_{job_id}_errors.txt")
            logger.info(f"Downloading error report {error_file_id} from Appwrite Storage")
            appwrite_storage.download_file(error_file_id, local_temp_path)
            
            return FileResponse(
                path=local_temp_path,
                filename=f"{job_id}_errors.txt",
                media_type="text/plain"
            )

        # Priority 2: Fallback to local disk
        error_path = os.path.join(settings.error_dir, f"{job_id}_errors.txt")
        if not os.path.exists(error_path):
            # Check if job actually has errors in metadata
            if not job.errors or len(job.errors) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No errors to report for this job"
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error report file not found on cloud or local storage"
            )
        
        logger.info(f"Downloading error report for job {job_id} from local storage")
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
