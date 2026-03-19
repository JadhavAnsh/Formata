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
from app.utils.job_utils import get_job_with_fallback
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
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job.status.value} state. Result file not available yet."
            )
        
        # Priority 1: Download from Appwrite Storage
        result_file_id = job.metadata.get("result_file_id") or (job.result.get("appwrite_result_file_id") if job.result else None)
        
        if result_file_id:
            local_temp_path = os.path.join(settings.output_dir, f"dl_{job_id}")
            logger.info(f"Downloading result file {result_file_id} from Appwrite Storage to {local_temp_path}")
            
            # Ensure directory exists
            os.makedirs(settings.output_dir, exist_ok=True)
            
            appwrite_storage.download_file(result_file_id, local_temp_path)
            
            # Check if file exists after download
            if os.path.exists(local_temp_path):
                # Appwrite doesn't easily give extension without another call, assume CSV or check metadata
                return FileResponse(
                    path=local_temp_path,
                    filename=f"{job_id}_result",
                    media_type="text/csv"
                )
            else:
                logger.error(f"File {local_temp_path} not found after Appwrite download")

        # Priority 2: Fallback to local disk
        if job.result and job.result.get("output_path"):
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
