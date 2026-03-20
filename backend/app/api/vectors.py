# /vectors endpoint
# Vector generation and download for LLM integration
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import tempfile
import os
import pandas as pd
from datetime import datetime

from app.jobs.store import job_store, JobStatus
from app.guards.appwrite_auth import verify_appwrite_session
from app.services.appwrite_storage import appwrite_storage
from app.config.settings import settings
from app.utils.logger import logger
from app.utils.job_utils import get_job_with_fallback
from app.services.pipeline import ProcessingPipeline
from app.services.vectorization import (
    dataframe_to_vectors,
    save_vectors_pickle,
    save_vectors_hdf5
)
from app.services.appwrite_db import appwrite_db
import json

router = APIRouter(prefix="/vectors", tags=["vectors"])


class VectorRequest(BaseModel):
    """Request model for vector generation"""
    method: str = "hybrid"  # hybrid, text_only, numeric
    provider: str = "local" # local, gemini


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


async def _resolve_or_download_output_path(job_id: str, job) -> Optional[str]:
    output_path = None
    if job.result and job.result.get("output_path"):
        output_path = job.result["output_path"]
    elif (job.metadata or {}).get("output_path"):
        output_path = job.metadata["output_path"]
    else:
        output_format = _resolve_output_format(job)
        output_path = os.path.join(settings.output_dir, f"resolved_{job_id}.{output_format}")

    if output_path and os.path.exists(output_path):
        return output_path

    result_file_id = (job.metadata or {}).get("result_file_id") or (job.result.get("appwrite_result_file_id") if job.result else None)
    if not result_file_id:
        recovered_output_path, recovered_file_id = await _recover_output_for_job(job_id, job)
        if recovered_output_path and os.path.exists(recovered_output_path):
            return recovered_output_path
        if recovered_file_id:
            result_file_id = recovered_file_id
            output_path = os.path.join(settings.output_dir, f"resolved_{job_id}.{_resolve_output_format(job)}")
        else:
            return None

    logger.info(f"Local output file missing, downloading {result_file_id} from Appwrite Storage")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    appwrite_storage.download_file(result_file_id, output_path)

    return output_path if os.path.exists(output_path) else None


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


async def _recover_output_for_job(job_id: str, job) -> tuple[Optional[str], Optional[str]]:
    if not job.file_path or not job.file_path.startswith("appwrite://"):
        return None, None

    try:
        file_id = job.file_path.replace("appwrite://", "")
        source_ext = os.path.splitext(job.file_name or "")[1]
        local_input_path = os.path.join(settings.upload_dir, f"recover_input_{job_id}{source_ext}")
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
        logger.error(f"Failed to recover output for vectors job {job_id}: {str(e)}")
        return None, None


@router.post("/{job_id}/generate")
async def generate_vectors(
    job_id: str,
    request: VectorRequest = VectorRequest(),
    user: dict = Depends(verify_appwrite_session)
) -> Dict[str, Any]:
    """
    Generate vector embeddings from processed data and upload to Appwrite
    
    Methods:
    - hybrid: Text embeddings + normalized numeric + one-hot categorical
    - text_only: Treats all columns as text, generates embeddings
    - numeric: Numeric normalization + one-hot encoding for categoricals
    
    Providers:
    - local: HashingVectorizer (512d)
    - gemini: Google Generative AI (768d)
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
                detail=f"Job is in {job.status.value} state. Only completed jobs can be vectorized."
            )
        
        output_path = await _resolve_or_download_output_path(job_id, job)
        if not output_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found on disk or cloud. Cannot generate vectors."
            )
        
        logger.info(f"Generating vectors for job {job_id} using method: {request.method}, provider: {request.provider}")
        
        # Validate method and provider
        valid_methods = ["hybrid", "text_only", "numeric"]
        if request.method not in valid_methods:
            raise ValueError(f"Invalid method. Supported: {valid_methods}")
            
        valid_providers = ["local", "gemini"]
        if request.provider not in valid_providers:
            raise ValueError(f"Invalid provider. Supported: {valid_providers}")
        
        if request.provider == "gemini" and not settings.google_api_key:
            raise ValueError("Gemini API key not configured. Please use 'local' provider.")
        
        # Read output file
        if output_path.endswith('.csv'):
            df = pd.read_csv(output_path)
        elif output_path.endswith('.json'):
            with open(output_path, 'r') as f:
                data = json.load(f)
                records = data.get('records', data) if isinstance(data, dict) else data
                df = pd.DataFrame(records)
        else:
            raise ValueError("Unsupported output file format")
        
        # Generate vectors
        vectors, metadata = dataframe_to_vectors(df, method=request.method, provider=request.provider)
        
        # Save locally first
        temp_dir = tempfile.gettempdir()
        pkl_path = os.path.join(temp_dir, f"{job_id}_vectors.pkl")
        h5_path = os.path.join(temp_dir, f"{job_id}_vectors.h5")
        
        save_vectors_pickle(vectors, metadata, pkl_path)
        save_vectors_hdf5(vectors, metadata, h5_path)
        
        # Upload to Appwrite Storage
        logger.info(f"Uploading vectors to Appwrite Storage...")
        pkl_file_id = appwrite_storage.upload_file(pkl_path)
        h5_file_id = appwrite_storage.upload_file(h5_path)
        
        # Cleanup local temp files
        os.remove(pkl_path)
        os.remove(h5_path)
        
        # Store vector info in job metadata
        vector_info = {
            'shape': list(metadata['shape']),
            'method': metadata['method'],
            'provider': metadata['provider'],
            'n_samples': metadata['n_samples'],
            'n_features': metadata['n_features'],
            'pkl_file_id': pkl_file_id,
            'h5_file_id': h5_file_id,
            'generated_at': datetime.now().isoformat()
        }
        
        if not job.metadata:
            job.metadata = {}
        job.metadata['vector_info'] = vector_info
        
        # Update Appwrite DB
        try:
            job_doc = appwrite_db.get_job_document(job_id)
            existing_metadata = json.loads(job_doc.get('metadata', '{}'))
            existing_metadata['vector_info'] = vector_info
            appwrite_db.update_job_document(job_id, {"metadata": json.dumps(existing_metadata)})
        except Exception as e:
            logger.error(f"Failed to update Appwrite DB with vector info: {str(e)}")
        
        logger.info(f"Vectors generated and uploaded: shape {metadata['shape']}")
        
        return {
            "status": "success",
            "job_id": job_id,
            "vector_shape": metadata['shape'],
            "n_samples": metadata['n_samples'],
            "n_features": metadata['n_features'],
            "method": metadata['method'],
            "provider": metadata['provider'],
            "pkl_file_id": pkl_file_id,
            "h5_file_id": h5_file_id,
            "message": "Vectors generated and uploaded to Appwrite Storage successfully."
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating vectors for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating vectors: {str(e)}"
        )


@router.get("/{job_id}/download")
async def download_vectors(
    job_id: str,
    format: str = "pkl",
    user: dict = Depends(verify_appwrite_session)
):
    """
    Download vectorized data in specified format
    - Priority: Appwrite Storage (if previously generated)
    - Fallback: On-the-fly generation from output file
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
                detail=f"Job is in {job.status.value} state. Only completed jobs have vectors."
            )
        
        format = format.lower()
        if format not in ["pkl", "h5"]:
            raise ValueError("Format must be 'pkl' or 'h5'")

        # Priority 1: Check metadata for Appwrite file IDs
        vector_info = job.metadata.get("vector_info", {})
        file_id = vector_info.get(f"{format}_file_id")
        
        if file_id:
            local_temp_path = os.path.join(settings.output_dir, f"dl_vectors_{job_id}.{format}")
            logger.info(f"Downloading {format} vectors {file_id} from Appwrite Storage")
            appwrite_storage.download_file(file_id, local_temp_path)
            
            return FileResponse(
                path=local_temp_path,
                filename=f"{job_id}_vectors.{format}",
                media_type="application/octet-stream" if format == "pkl" else "application/x-hdf"
            )

        # Priority 2: On-the-fly generation fallback
        output_path = await _resolve_or_download_output_path(job_id, job)
        if not output_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found on disk or cloud"
            )
        
        logger.info(f"Generating vectors on-the-fly for job {job_id} in {format} format")
        
        # Read output file
        if output_path.endswith('.csv'):
            df = pd.read_csv(output_path)
        elif output_path.endswith('.json'):
            with open(output_path, 'r') as f:
                data = json.load(f)
                records = data.get('records', data) if isinstance(data, dict) else data
                df = pd.DataFrame(records)
        else:
            raise ValueError("Unsupported output file format")
        
        # Get vectorization method from metadata or use default
        method = vector_info.get('method', "hybrid")
        
        # Generate vectors
        vectors, metadata = dataframe_to_vectors(df, method=method)
        
        # Create temporary file for output
        temp_fd, temp_path = tempfile.mkstemp(suffix=f".{format}")
        os.close(temp_fd)
        
        try:
            # Save vectors in requested format
            if format == "pkl":
                save_vectors_pickle(vectors, metadata, temp_path)
                media_type = "application/octet-stream"
                filename = f"{job_id}_vectors.pkl"
            else:  # h5
                save_vectors_hdf5(vectors, metadata, temp_path)
                media_type = "application/x-hdf"
                filename = f"{job_id}_vectors.h5"
            
            return FileResponse(
                path=temp_path,
                filename=filename,
                media_type=media_type
            )
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading vectors for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading vectors: {str(e)}"
        )


@router.get("/{job_id}/info")
async def get_vector_info(
    job_id: str,
    user: dict = Depends(verify_appwrite_session)
) -> Dict[str, Any]:
    """
    Get vector information for a job without downloading
    
    Returns metadata about the vectors that would be generated
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
                detail=f"Job is in {job.status.value} state"
            )
        
        output_path = await _resolve_or_download_output_path(job_id, job)
        if not output_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found on disk or cloud"
            )
        
        logger.info(f"Retrieving vector info for job {job_id}")
        
        # Read and analyze data
        if output_path.endswith('.csv'):
            df = pd.read_csv(output_path)
        elif output_path.endswith('.json'):
            with open(output_path, 'r') as f:
                import json
                data = json.load(f)
                records = data.get('records', data) if isinstance(data, dict) else data
                df = pd.DataFrame(records)
        else:
            raise ValueError("Unsupported output file format")
        
        # Generate vectors to get metadata
        vectors, metadata = dataframe_to_vectors(df, method="hybrid")
        
        return {
            "status": "success",
            "job_id": job_id,
            "vector_info": {
                "shape": metadata['shape'],
                "n_samples": metadata['n_samples'],
                "n_features": metadata['n_features'],
                "method": metadata['method'],
                "original_columns": metadata['original_columns'],
                "feature_names": metadata['feature_names'][:20]  # First 20 features
            },
            "download_formats": ["pkl", "h5"],
            "supported_methods": ["hybrid", "text_only", "numeric"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vector info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vector info: {str(e)}"
        )
