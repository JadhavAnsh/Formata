# /result/{job_id} endpoint
# JOB FLOW: Step 7 - Final Output + Error Report Saved + Step 8 - User Downloads Result
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
import os

from app.jobs.store import JobStatus, job_store
from app.guards.appwrite_auth import verify_appwrite_session
from app.services.appwrite_storage import appwrite_storage
from app.services.pipeline import ProcessingPipeline
from app.config.settings import settings
from app.utils.logger import logger
from app.utils.job_utils import get_job_with_fallback

router = APIRouter(prefix="/result", tags=["result"])


def _resolve_output_format(job) -> str:
    output_format = (job.metadata or {}).get("output_format")
    if output_format in {"csv", "json"}:
        return output_format

    if job.result and job.result.get("output_path"):
        ext = job.result["output_path"].split(".")[-1].lower()
        if ext in {"csv", "json"}:
            return ext

    metadata_output = (job.metadata or {}).get("output_path")
    if isinstance(metadata_output, str) and "." in metadata_output:
        ext = metadata_output.split(".")[-1].lower()
        if ext in {"csv", "json"}:
            return ext

    return "csv"


def _resolve_output_path(job):
    if job.result and job.result.get("output_path"):
        return job.result["output_path"]
    if (job.metadata or {}).get("output_path"):
        return job.metadata["output_path"]
    return None


def _default_process_config(output_format: str) -> dict:
    return {
        "normalize": True,
        "remove_duplicates": True,
        "remove_outliers": False,
        "filters": None,
        "validation_rules": None,
        "output_format": output_format,
        "detect_data_quality_issues": True,
        "enforce_types": True,
        "auto_detect_types": True,
        "handle_missing_data": True,
        "default_missing_strategy": "fill_mean",
        "flag_missing_data": False,
    }


async def _recover_output_for_job(job_id: str, job) -> tuple[str | None, str | None]:
    """
    Attempt to regenerate output for completed jobs that lost output references.
    Returns (output_path, result_file_id).
    """
    if not job.file_path or not job.file_path.startswith("appwrite://"):
        return None, None

    try:
        file_id = job.file_path.replace("appwrite://", "")
        local_input_path = os.path.join(settings.upload_dir, f"recover_input_{job_id}")
        os.makedirs(settings.upload_dir, exist_ok=True)
        appwrite_storage.download_file(file_id, local_input_path)

        output_format = _resolve_output_format(job)
        process_config = (job.metadata or {}).get("process_config") or _default_process_config(output_format)
        process_config["output_format"] = process_config.get("output_format", output_format)

        pipeline = ProcessingPipeline()
        recovered_result = await pipeline.run_async(
            job_id=job_id,
            file_path=local_input_path,
            config=process_config
        )

        output_path = recovered_result.get("output_path")
        if not output_path or not os.path.exists(output_path):
            return None, None

        result_file_id = appwrite_storage.upload_file(output_path)
        job_store.set_job_metadata(job_id, {
            "output_path": output_path,
            "output_format": process_config.get("output_format", output_format),
            "result_file_id": result_file_id
        })
        job_store.set_job_result(job_id, {
            "job_id": job_id,
            "status": "completed",
            "output_path": output_path,
            "summary": recovered_result.get("summary", {}),
            "errors": recovered_result.get("errors", []),
            "reports": recovered_result.get("reports", {}),
            "metadata": recovered_result.get("metadata", {}),
            "appwrite_result_file_id": result_file_id
        })

        try:
            os.remove(local_input_path)
        except Exception:
            pass

        return output_path, result_file_id
    except Exception as e:
        logger.error(f"Failed to recover output for job {job_id}: {str(e)}")
        return None, None


@router.get("/{job_id}/download")
async def download_job_result(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
):
    """
    STEP 8: User Downloads Result
    - Download processed/cleaned data as file
    - Priority: Appwrite Storage (Cloud)
    - Fallback: Local disk
    """
    try:
        job = await get_job_with_fallback(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # Verify ownership
        if job.user_id != user["$id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job"
            )

        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job.status.value} state. Result file not available yet."
            )

        output_format = _resolve_output_format(job)

        # Priority 1: Download from Appwrite Storage
        result_file_id = job.metadata.get("result_file_id") or (job.result.get("appwrite_result_file_id") if job.result else None)

        if result_file_id:
            local_temp_path = os.path.join(settings.output_dir, f"dl_{job_id}.{output_format}")
            logger.info(f"Downloading result file {result_file_id} from Appwrite Storage to {local_temp_path}")

            # Ensure directory exists
            os.makedirs(settings.output_dir, exist_ok=True)
            appwrite_storage.download_file(result_file_id, local_temp_path)

            if os.path.exists(local_temp_path):
                return FileResponse(
                    path=local_temp_path,
                    filename=f"{job_id}_result.{output_format}",
                    media_type="text/csv" if output_format == "csv" else "application/json"
                )

        # Priority 2: Local disk fallback
        output_path = _resolve_output_path(job)
        if output_path and os.path.exists(output_path):
            file_extension = output_path.split(".")[-1].lower()
            return FileResponse(
                path=output_path,
                filename=f"{job_id}_clean.{file_extension}",
                media_type="text/csv" if file_extension == "csv" else "application/json"
            )

        # Priority 3: Recovery path (regenerate output from source file)
        recovered_output_path, recovered_file_id = await _recover_output_for_job(job_id, job)
        if recovered_file_id:
            local_temp_path = os.path.join(settings.output_dir, f"dl_{job_id}.{output_format}")
            appwrite_storage.download_file(recovered_file_id, local_temp_path)
            if os.path.exists(local_temp_path):
                return FileResponse(
                    path=local_temp_path,
                    filename=f"{job_id}_result.{output_format}",
                    media_type="text/csv" if output_format == "csv" else "application/json"
                )

        if recovered_output_path and os.path.exists(recovered_output_path):
            file_extension = recovered_output_path.split(".")[-1].lower()
            return FileResponse(
                path=recovered_output_path,
                filename=f"{job_id}_clean.{file_extension}",
                media_type="text/csv" if file_extension == "csv" else "application/json"
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found in cloud or local storage"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading job result {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading job result: {str(e)}"
        )
