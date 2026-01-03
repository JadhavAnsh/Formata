# /jobs endpoints - Job management and listing
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List

from app.jobs.store import job_store, JobStatus
from app.utils.logger import logger

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_all_jobs() -> List[Dict[str, Any]]:
    """
    List all jobs with their status and details
    """
    try:
        jobs = job_store.get_all_jobs()
        logger.info(f"Retrieved {len(jobs)} jobs")
        return jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}"
        )


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific job
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
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
async def delete_job(job_id: str) -> Dict[str, str]:
    """
    Delete a job and its associated data
    """
    try:
        if not job_store.job_exists(job_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Delete the job
        job_store.delete_job(job_id)
        logger.info(f"Job {job_id} deleted")
        
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
async def get_jobs_summary() -> Dict[str, Any]:
    """
    Get a summary of all jobs by status
    """
    try:
        jobs = job_store.get_all_jobs()
        
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
