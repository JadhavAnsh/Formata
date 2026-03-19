# /result/{job_id} endpoint
# JOB FLOW: Step 7 - Final Output + Error Report Saved + Step 8 - User Downloads Result
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from typing import Dict, Any
import os

from app.jobs.store import job_store, JobStatus
from app.guards.appwrite_auth import verify_appwrite_session
from app.services.appwrite_storage import appwrite_storage
from app.services.appwrite_db import appwrite_db
from app.config.settings import settings
from app.utils.logger import logger
import os

router = APIRouter(prefix="/result", tags=["result"])


@router.get("/{job_id}/download")
async def download_job_result(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
):
    """
    STEP 8: User Downloads Result
    - Download processed/cleaned data as file
    - Priority: Appwrite Storage (Cloud)
    - Fallback: Local disk
    """
    try:
        # First, try to get job from Appwrite DB for persistence
        try:
            job_doc = appwrite_db.get_job_document(job_id)
            user_id = job_doc.get("user_id")
            job_status = job_doc.get("status")
            result_file_id = job_doc.get("result_file_id")
        except:
            # Fallback to in-memory store if Appwrite DB fails or document not found
            job = job_store.get_job(job_id)
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            user_id = job.user_id
            job_status = job.status.value
            result_file_id = job.result.get("appwrite_result_file_id") if job.result else None

        # Verify ownership
        if user_id != user["$id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job"
            )
        
        if job_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job_status} state. Result file not available yet."
            )
        
        # Priority 1: Download from Appwrite Storage
        if result_file_id:
            local_temp_path = os.path.join(settings.output_dir, f"dl_{job_id}")
            logger.info(f"Downloading result file {result_file_id} from Appwrite Storage")
            appwrite_storage.download_file(result_file_id, local_temp_path)
            
            # Appwrite doesn't easily give extension without another call, assume CSV or check metadata
            # For now, let's use FileResponse which will stream it
            return FileResponse(
                path=local_temp_path,
                filename=f"{job_id}_result",
                background=None # We should ideally cleanup this temp file
            )

        # Priority 2: Fallback to local disk (if it was a local job)
        job = job_store.get_job(job_id)
        if job and job.result and job.result.get("output_path"):
            output_path = job.result["output_path"]
            if os.path.exists(output_path):
                file_extension = output_path.split('.')[-1].lower()
                return FileResponse(
                    path=output_path,
                    filename=f"{job_id}_clean.{file_extension}",
                    media_type="text/csv" if file_extension == "csv" else "application/json"
                )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found in cloud or local storage"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading job result {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading job result: {str(e)}"
        )
