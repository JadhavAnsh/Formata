# Background processing worker
import asyncio
from typing import Dict, Any
import traceback
from datetime import datetime

from app.jobs.store import job_store, JobStatus
from app.utils.logger import logger
from app.services.pipeline import ProcessingPipeline
from app.services.appwrite_storage import appwrite_storage
from app.services.appwrite_db import appwrite_db
from app.config.settings import settings
import os
import json


async def process_job_async(job_id: str, file_path: str, config: Dict[str, Any]) -> None:
    """
    Process job in background asynchronously
    """
    local_input_path = None
    try:
        # Update status to processing in memory and Appwrite
        job_store.update_job_status(job_id, JobStatus.PROCESSING)
        appwrite_db.update_job_document(job_id, {"status": "processing", "progress": 0.1})
        logger.info(f"Started processing job {job_id}")
        
        # Determine if we need to download from Appwrite
        if file_path.startswith("appwrite://"):
            file_id = file_path.replace("appwrite://", "")
            local_input_path = os.path.join(settings.upload_dir, f"input_{job_id}")
            logger.info(f"Downloading file {file_id} from Appwrite Storage...")
            appwrite_storage.download_file(file_id, local_input_path)
            actual_file_path = local_input_path
        else:
            actual_file_path = file_path

        # Update progress
        job_store.update_job_progress(job_id, 0.2)
        
        # Initialize pipeline
        pipeline = ProcessingPipeline()
        
        # Define progress callback for Appwrite DB sync
        def progress_callback(progress: float):
            job_store.update_job_progress(job_id, progress)
            # Throttle DB updates or just do it for key milestones
            if int(progress * 10) % 2 == 0: # Update every 20%
                appwrite_db.update_job_document(job_id, {"progress": progress})

        # Run processing pipeline
        result = await pipeline.run_async(
            job_id=job_id,
            file_path=actual_file_path,
            config=config,
            progress_callback=progress_callback
        )
        
        # Upload result file to Appwrite Storage if available
        result_file_id = None
        if result.get("output_path") and os.path.exists(result["output_path"]):
            logger.info(f"Uploading result file to Appwrite Storage...")
            result_file_id = appwrite_storage.upload_file(result["output_path"])
            result["appwrite_result_file_id"] = result_file_id
        
        # Set result in memory
        job_store.set_job_result(job_id, result)
        
        # Update job metadata
        job = job_store.get_job(job_id)
        update_data = {
            "status": "completed",
            "progress": 1.0,
            "completed_at": datetime.now().isoformat(),
            "result_file_id": result_file_id or ""
        }
        
        if job and result.get("metadata"):
            # Save metadata as JSON string for Appwrite
            update_data["metadata"] = json.dumps(result["metadata"])
            
            # Update memory store as well
            if result["metadata"].get("clean_profile_path"):
                job.metadata["clean_profile_path"] = result["metadata"]["clean_profile_path"]
            if result["metadata"].get("processing_time"):
                job.metadata["processing_time"] = result["metadata"]["processing_time"]
            if result.get("summary"):
                job.metadata["summary"] = result["summary"]
            
            job_store.jobs[job_id] = job
        
        # Update Appwrite DB
        appwrite_db.update_job_document(job_id, update_data)
        
        # Mark as completed in memory
        job_store.update_job_status(job_id, JobStatus.COMPLETED)
        logger.info(f"Completed processing job {job_id}")
        
    except Exception as e:
        error_message = f"{str(e)}\n{traceback.format_exc()}"
        job_store.add_job_error(job_id, error_message)
        job_store.update_job_status(job_id, JobStatus.FAILED)
        
        # Update Appwrite DB with error
        try:
            appwrite_db.update_job_document(job_id, {
                "status": "failed",
                "progress": 1.0,
                "metadata": json.dumps({"error": str(e)})
            })
        except:
            pass
            
        logger.error(f"Error processing job {job_id}: {error_message}")
    finally:
        # Cleanup local temporary file
        if local_input_path and os.path.exists(local_input_path):
            try:
                os.remove(local_input_path)
            except:
                pass


def start_background_job(job_id: str, file_path: str, config: Dict[str, Any]) -> None:
    """
    Start a background processing job (non-blocking)
    """
    asyncio.create_task(process_job_async(job_id, file_path, config))
