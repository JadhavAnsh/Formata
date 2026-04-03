# /ingest endpoint
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
import math
import os
from datetime import date, datetime
import pandas as pd

from app.jobs.store import job_store
from app.models.response import JobResponse
from app.utils.file_utils import ensure_directory, get_file_extension
from app.config.settings import settings
from app.utils.logger import logger
from app.services.parser import parse_csv, parse_excel, parse_json, parse_markdown

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=JobResponse)
async def ingest_data(file: UploadFile = File(...), preview_rows: int = Form(0)):
    """
    STEP 1: User Uploads File
    STEP 2: Job Created (job_id)
    - Validates file format
    - Creates job entry
    - Saves file to storage
    - Returns job_id for tracking
    """
    try:
        # Validate file extension
        extension = get_file_extension(file.filename)
        valid_extensions = [".csv", ".json", ".xlsx", ".xls", ".md"]
        
        if extension not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported: {', '.join(valid_extensions)}"
            )
        
        # Ensure upload directory exists
        ensure_directory(settings.upload_dir)
        
        # Create job entry
        job_id = job_store.create_job(file.filename, "")
        
        # Save uploaded file
        file_path = os.path.join(settings.upload_dir, f"{job_id}_{file.filename}")
        max_file_size = int(settings.max_file_size)
        bytes_written = 0
        
        try:
            with open(file_path, "wb") as buffer:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break

                    bytes_written += len(chunk)
                    if bytes_written > max_file_size:
                        buffer.close()
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=(
                                f"File exceeds max allowed size of "
                                f"{max_file_size // (1024 * 1024)}MB"
                            ),
                        )

                    buffer.write(chunk)
        finally:
            await file.close()
        
        # Update file path in job
        job = job_store.get_job(job_id)
        if job:
            job.file_path = file_path
        
        logger.info(f"File ingested successfully. Job ID: {job_id}")

        preview_payload = None
        if preview_rows > 0:
            preview_payload = _build_preview_payload(file_path=file_path, extension=extension, max_rows=preview_rows)

        return JobResponse(
            job_id=job_id,
            status="pending",
            message="File ingested successfully. Use /status/{job_id} to check processing status.",
            preview=preview_payload,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting file: {str(e)}"
        )


def _build_preview_payload(file_path: str, extension: str, max_rows: int = 100) -> dict:
    """
    Build sampled preview payload for immediate UI rendering.
    """
    max_rows = max(1, int(max_rows))

    if extension == ".csv":
        sample = parse_csv(file_path).head(max_rows)
        total_rows = max(0, int(sum(1 for _ in open(file_path, "r", encoding="utf-8", errors="ignore")) - 1))
    elif extension in [".xlsx", ".xls"]:
        full = parse_excel(file_path)
        sample = full.head(max_rows)
        total_rows = int(len(full))
    elif extension == ".json":
        data = parse_json(file_path)
        if isinstance(data, dict) and "records" in data:
            full = pd.DataFrame(data["records"])
        elif isinstance(data, list):
            full = pd.DataFrame(data)
        else:
            full = pd.DataFrame([data])
        sample = full.head(max_rows)
        total_rows = int(len(full))
    elif extension == ".md":
        markdown_text = parse_markdown(file_path)
        full = pd.DataFrame({"content": markdown_text.splitlines()})
        sample = full.head(max_rows)
        total_rows = int(len(full))
    else:
        sample = pd.DataFrame()
        total_rows = 0

    records = _to_json_safe(sample.to_dict(orient="records"))
    columns = [str(col) for col in sample.columns]

    return {
        "records": records,
        "metadata": {
            "columns": columns,
            "rowCount": len(records),
            "totalRows": total_rows,
            "sampled": True,
        },
    }


def _to_json_safe(value):
    """
    Recursively sanitize values so FastAPI/Starlette JSON serialization cannot fail
    on NaN/Infinity or pandas/numpy scalar types.
    """
    if value is None:
        return None

    if isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_to_json_safe(v) for v in value]

    # Handle numpy/pandas scalar values via .item() when available.
    if hasattr(value, "item"):
        try:
            return _to_json_safe(value.item())
        except Exception:
            pass

    # Last resort: convert unsupported objects to string.
    return str(value)
