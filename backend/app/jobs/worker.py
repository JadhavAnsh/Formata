# Background processing
import asyncio
from typing import Dict, Any


async def process_job_async(job_id: str, file_path: str, config: Dict[str, Any]) -> None:
    """
    Process job in background
    """
    pass


def start_background_job(job_id: str, file_path: str, config: Dict[str, Any]) -> None:
    """
    Start a background processing job
    """
    asyncio.create_task(process_job_async(job_id, file_path, config))
