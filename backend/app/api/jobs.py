# /jobs endpoints - Job management and listing
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
import os
import glob

from app.jobs.store import job_store, JobStatus
from app.guards.appwrite_auth import verify_appwrite_session
from app.services.appwrite_db import appwrite_db
from app.utils.logger import logger
import os
import glob
import json

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_user_jobs(user: dict = Depends(verify_appwrite_session)) -> List[Dict[str, Any]]:
    """
    List all jobs belonging to the authenticated user from DB
    """
    try:
        user_id = user["$id"]
        jobs = job_store.get_jobs_by_user(user_id)
        logger.info(f"Retrieved {len(jobs)} jobs from DB for user {user_id}")
        return jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}"
        )


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_details(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific job from DB
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        if job.user_id != user["$id"]:
            raise HTTPException(status_code=403, detail="Forbidden")
            
        return job.to_dict()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job details {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job details: {str(e)}"
        )


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
) -> Dict[str, str]:
    """
    Delete a job from DB
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            # If it's already gone, consider it a success or 404
            return {"message": f"Job {job_id} already deleted", "job_id": job_id}
            
        if job.user_id != user["$id"]:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Delete from DB via JobStore
        job_store.delete_job(job_id)
        
        return {
            "message": f"Job {job_id} deleted successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job: {str(e)}"
        )


@router.get("/status/summary", response_model=Dict[str, Any])
async def get_jobs_summary(user: dict = Depends(verify_appwrite_session)) -> Dict[str, Any]:
    """
    Get a summary of user jobs by status
    """
    try:
        user_id = user["$id"]
        jobs = job_store.get_jobs_by_user(user_id)
        
        summary = {
            "total": len(jobs),
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for job in jobs:
            status = job.get("status", "unknown")
            if status in summary:
                summary[status] += 1
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting jobs summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting jobs summary: {str(e)}"
        )
