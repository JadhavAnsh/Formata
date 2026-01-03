# /errors/{job_id} endpoint
from fastapi import APIRouter

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get("/{job_id}")
async def get_job_errors(job_id: str):
    """
    Get error details for a job
    """
    pass
