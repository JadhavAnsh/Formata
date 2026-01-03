# /process/{job_id} endpoint
from fastapi import APIRouter

router = APIRouter(prefix="/process", tags=["process"])


@router.post("/{job_id}")
async def process_job(job_id: str):
    """
    Start processing a job
    """
    pass
