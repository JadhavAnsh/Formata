from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import os
import pandas as pd

from app.guards.appwrite_auth import verify_appwrite_session
from app.services.appwrite_storage import appwrite_storage
from app.services.appwrite_db import appwrite_db
from app.services.parser import DataParser
from app.config.settings import settings
from app.utils.logger import logger

router = APIRouter(prefix="/preview", tags=["preview"])

@router.get("/{job_id}")
async def get_data_preview(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
):
    """
    Phase 3: Backend-Driven Data Preview
    - Fetches file_id from Appwrite DB
    - Streams a sample (first 100 lines) from Appwrite Storage
    - Parses it using DataParser
    - Returns structured JSON
    """
    local_temp_path = None
    try:
        # 1. Get job document to find file_id
        try:
            job_doc = appwrite_db.get_job_document(job_id)
            file_id = job_doc.get("file_id")
            user_id = job_doc.get("user_id")
        except Exception as e:
            logger.error(f"Error fetching job document for preview: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # 2. Verify ownership
        if user_id != user["$id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job"
            )

        if not file_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No file associated with this job"
            )

        # 3. Download a sample from Appwrite Storage
        # Note: Appwrite Python SDK doesn't support range requests for partial downloads easily
        # For now, we download the whole file but limit parsing
        local_temp_path = os.path.join(settings.upload_dir, f"preview_{job_id}")
        appwrite_storage.download_file(file_id, local_temp_path)

        # 4. Parse the sample
        parser = DataParser()
        # DataParser.parse usually returns a dict with 'records', 'columns', etc.
        # We can limit it to 100 rows
        result = parser.parse(local_temp_path)
        
        # Limit records to 100
        if "records" in result:
            result["records"] = result["records"][:100]
            result["preview_count"] = len(result["records"])
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating preview: {str(e)}"
        )
    finally:
        # Cleanup
        if local_temp_path and os.path.exists(local_temp_path):
            try:
                os.remove(local_temp_path)
            except:
                pass
