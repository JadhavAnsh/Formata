# Background processing worker
import asyncio
from typing import Dict, Any
import traceback

from app.jobs.store import job_store, JobStatus
from app.utils.logger import logger
from app.services.pipeline import ProcessingPipeline


async def process_job_async(job_id: str, file_path: str, config: Dict[str, Any]) -> None:
    """
    Process job in background asynchronously
    """
    try:
        # Update status to processing
        job_store.update_job_status(job_id, JobStatus.PROCESSING)
        logger.info(f"Started processing job {job_id}")
        
        # Update progress
        job_store.update_job_progress(job_id, 0.1)
        
        # Initialize pipeline
        pipeline = ProcessingPipeline()
        
        # Run processing pipeline
        result = await pipeline.run_async(
            job_id=job_id,
            file_path=file_path,
            config=config,
            progress_callback=lambda progress: job_store.update_job_progress(job_id, progress)
        )
        
        # Set result
        job_store.set_job_result(job_id, result)
        
        # Mark as completed
        job_store.update_job_status(job_id, JobStatus.COMPLETED)
        logger.info(f"Completed processing job {job_id}")
        
    except Exception as e:
        error_message = f"{str(e)}\n{traceback.format_exc()}"
        job_store.add_job_error(job_id, error_message)
        job_store.update_job_status(job_id, JobStatus.FAILED)
        logger.error(f"Error processing job {job_id}: {error_message}")


def start_background_job(job_id: str, file_path: str, config: Dict[str, Any]) -> None:
    """
    Start a background processing job (non-blocking)
    """
    asyncio.create_task(process_job_async(job_id, file_path, config))
