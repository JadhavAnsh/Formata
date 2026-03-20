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


def _build_compact_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Build a compact result payload for DB persistence when full payload is too large."""
    compact = {
        "job_id": result.get("job_id"),
        "status": result.get("status"),
        "rows_before": result.get("rows_before", 0),
        "rows_after": result.get("rows_after", 0),
        "output_path": result.get("output_path"),
        "errors": (result.get("errors") or [])[:200],
        "reports": result.get("reports", {}),
        "summary": result.get("summary", {}),
        "metadata": result.get("metadata", {}),
    }

    before_data = result.get("before_data")
    if isinstance(before_data, dict):
        compact["before_data"] = {
            "rowCount": before_data.get("rowCount", 0),
            "columns": before_data.get("columns", []),
            "rows": (before_data.get("rows") or [])[:10],
        }

    after_data = result.get("after_data")
    if isinstance(after_data, dict):
        compact["after_data"] = {
            "rowCount": after_data.get("rowCount", 0),
            "columns": after_data.get("columns", []),
            "rows": (after_data.get("rows") or [])[:10],
        }

    return compact


async def process_job_async(job_id: str, file_path: str, config: Dict[str, Any]) -> None:
    """
    Process job in background asynchronously
    """
    local_input_path = None
    try:
        # Update status (now DB-backed)
        job_store.update_job_status(job_id, JobStatus.PROCESSING)
        logger.info(f"Started processing job {job_id}")
        
        # Determine if we need to download from Appwrite
        if file_path.startswith("appwrite://"):
            file_id = file_path.replace("appwrite://", "")
            source_file_name = config.get("_source_file_name", "")
            source_ext = os.path.splitext(source_file_name)[1] if source_file_name else ""
            local_input_path = os.path.join(settings.upload_dir, f"input_{job_id}{source_ext}")
            logger.info(f"Downloading file {file_id} from Appwrite Storage...")
            appwrite_storage.download_file(file_id, local_input_path)
            actual_file_path = local_input_path
        else:
            actual_file_path = file_path

        # Update progress
        job_store.update_job_progress(job_id, 0.2)
        
        # Initialize pipeline
        pipeline = ProcessingPipeline()
        
        # Define progress callback
        def progress_callback(progress: float):
            # Throttle DB updates via job_store
            if int(progress * 10) % 2 == 0: # Update every 20%
                job_store.update_job_progress(job_id, progress)

        # Run processing pipeline
        result = await pipeline.run_async(
            job_id=job_id,
            file_path=actual_file_path,
            config=config,
            progress_callback=progress_callback
        )

        if result.get("status") != "completed":
            failure_errors = result.get("errors", []) or ["Pipeline failed without explicit error details"]
            job_store.set_job_metadata(job_id, {
                "summary": result.get("summary", {}),
                "output_path": result.get("output_path"),
                "output_format": config.get("output_format", "csv")
            })
            job_store.set_job_result(job_id, _build_compact_result(result))
            for error in failure_errors:
                job_store.add_job_error(job_id, str(error))
            job_store.update_job_status(job_id, JobStatus.FAILED)
            job_store.update_job_progress(job_id, 1.0)
            logger.error(f"Pipeline returned failed status for job {job_id}: {failure_errors}")
            return
        
        # Upload result file to Appwrite Storage if available
        result_file_id = None
        if result.get("output_path") and os.path.exists(result["output_path"]):
            logger.info(f"Uploading result file to Appwrite Storage...")
            result_file_id = appwrite_storage.upload_file(result["output_path"])
            result["appwrite_result_file_id"] = result_file_id
        
        # Upload reports to Appwrite Storage
        profile_file_id = None
        if result.get("reports", {}).get("clean_profile") and os.path.exists(result["reports"]["clean_profile"]):
            logger.info(f"Uploading profile report to Appwrite Storage...")
            profile_file_id = appwrite_storage.upload_file(result["reports"]["clean_profile"])
            result["appwrite_profile_file_id"] = profile_file_id
            
        error_file_id = None
        if result.get("reports", {}).get("error_report") and os.path.exists(result["reports"]["error_report"]):
            logger.info(f"Uploading error report to Appwrite Storage...")
            error_file_id = appwrite_storage.upload_file(result["reports"]["error_report"])
            result["appwrite_error_file_id"] = error_file_id

        # Merge result into metadata for DB persistence
        metadata = result.get("metadata", {})
        metadata["summary"] = result.get("summary", {})
        metadata["result_file_id"] = result_file_id
        metadata["profile_file_id"] = profile_file_id
        metadata["error_file_id"] = error_file_id
        metadata["output_path"] = result.get("output_path")
        metadata["output_format"] = config.get("output_format", "csv")
        
        # Update JobStore (updates DB)
        # Note: We call set_job_metadata first, then set_job_result will merge the result key into it
        if not job_store.set_job_metadata(job_id, metadata):
            logger.warning(f"Failed to persist job metadata for {job_id}")

        if not job_store.set_job_result(job_id, result):
            logger.warning(f"Full result payload too large/unavailable for {job_id}; retrying with compact result")
            compact_result = _build_compact_result(result)
            if not job_store.set_job_result(job_id, compact_result):
                logger.warning(f"Failed to persist compact result payload for {job_id}")

        job_store.update_job_status(job_id, JobStatus.COMPLETED)
        job_store.update_job_progress(job_id, 1.0)
        
        logger.info(f"Completed processing job {job_id}")
        
    except Exception as e:
        error_message = f"{str(e)}\n{traceback.format_exc()}"
        job_store.add_job_error(job_id, error_message)
        job_store.update_job_status(job_id, JobStatus.FAILED)
        logger.error(f"Error processing job {job_id}: {error_message}")
    finally:
        # Cleanup local temporary file
        if local_input_path and os.path.exists(local_input_path):
            try:
                os.remove(local_input_path)
            except:
                pass


def start_background_job(job_id: str, file_path: str, config: Dict[str, Any], file_name: str = "") -> None:
    """
    Start a background processing job (non-blocking)
    """
    if file_name:
        config = dict(config)
        config["_source_file_name"] = file_name
    asyncio.create_task(process_job_async(job_id, file_path, config))
