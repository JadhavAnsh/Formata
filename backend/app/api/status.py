# /status/{job_id} endpoint
from fastapi import APIRouter

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a job
    """
    pass
