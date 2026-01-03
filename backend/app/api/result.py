# /result/{job_id} endpoint
from fastapi import APIRouter

router = APIRouter(prefix="/result", tags=["result"])


@router.get("/{job_id}")
async def get_job_result(job_id: str):
    """
    Get the result of a completed job
    """
    pass
