# /vectors endpoint
# Vector generation and download for LLM integration
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import tempfile
import os
import pandas as pd

from app.jobs.store import job_store, JobStatus
from app.utils.logger import logger
from app.utils.file_utils import ensure_directory
from app.services.conversion import csv_to_json
from app.services.vectorization import (
    dataframe_to_vectors,
    save_vectors_pickle,
    save_vectors_hdf5
)
from app.config.settings import settings

router = APIRouter(prefix="/vectors", tags=["vectors"])


class VectorRequest(BaseModel):
    """Request model for vector generation"""
    method: str = "hybrid"  # hybrid, text_only, numeric


@router.post("/{job_id}/generate")
async def generate_vectors(job_id: str, request: VectorRequest = VectorRequest()) -> Dict[str, Any]:
    """
    Generate vector embeddings from processed data
    
    Methods:
    - hybrid: Text embeddings (512d) + normalized numeric + one-hot categorical
    - text_only: Treats all columns as text, generates embeddings
    - numeric: Numeric normalization + one-hot encoding for categoricals
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job.status.value} state. Only completed jobs can be vectorized."
            )
        
        if not job.result or not job.result.get("output_path"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found in job result"
            )
        
        output_path = job.result["output_path"]
        if not os.path.exists(output_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found on disk"
            )
        
        logger.info(f"Generating vectors for job {job_id} using method: {request.method}")
        
        # Validate method
        valid_methods = ["hybrid", "text_only", "numeric"]
        if request.method not in valid_methods:
            raise ValueError(f"Invalid method. Supported: {valid_methods}")
        
        # Read output file
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
        
        # Generate vectors
        vectors, metadata = dataframe_to_vectors(df, method=request.method)
        
        # Store vector info in job metadata
        if not job.metadata:
            job.metadata = {}
        job.metadata['vector_info'] = {
            'shape': list(metadata['shape']),
            'method': metadata['method'],
            'n_samples': metadata['n_samples'],
            'n_features': metadata['n_features'],
            'n_original_columns': len(metadata['original_columns']),
            'original_columns': metadata['original_columns']
        }
        
        logger.info(f"Vectors generated: shape {metadata['shape']}")
        
        return {
            "status": "success",
            "job_id": job_id,
            "vector_shape": metadata['shape'],
            "n_samples": metadata['n_samples'],
            "n_features": metadata['n_features'],
            "method": metadata['method'],
            "message": f"Vectors generated successfully. Download using /vectors/{{job_id}}/download with format parameter.",
            "download_formats": ["pkl", "h5"]
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
async def download_vectors(job_id: str, format: str = "pkl") -> FileResponse:
    """
    Download vectorized data in specified format
    
    Formats:
    - pkl: Python pickle format (smaller file size, Python-native)
    - h5: HDF5 format (better for large data, language-agnostic, supports chunking)
    
    Returns downloadable vector file ready for LLM feeding
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job.status.value} state. Only completed jobs have vectors."
            )
        
        if not job.result or not job.result.get("output_path"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found"
            )
        
        # Validate format
        format = format.lower()
        if format not in ["pkl", "h5"]:
            raise ValueError("Format must be 'pkl' or 'h5'")
        
        output_path = job.result["output_path"]
        if not os.path.exists(output_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found on disk"
            )
        
        logger.info(f"Downloading vectors for job {job_id} in {format} format")
        
        # Read output file
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
        
        # Get vectorization method from metadata or use default
        method = "hybrid"
        if job.metadata and 'vector_method' in job.metadata:
            method = job.metadata['vector_method']
        
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
            
            logger.info(f"Vectors saved to {temp_path}, size: {os.path.getsize(temp_path)} bytes")
            
            return FileResponse(
                path=temp_path,
                filename=filename,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Vector-Shape": str(vectors.shape),
                    "X-Vector-Method": method
                }
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
async def get_vector_info(job_id: str) -> Dict[str, Any]:
    """
    Get vector information for a job without downloading
    
    Returns metadata about the vectors that would be generated
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is in {job.status.value} state"
            )
        
        if not job.result or not job.result.get("output_path"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found"
            )
        
        output_path = job.result["output_path"]
        if not os.path.exists(output_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Output file not found on disk"
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
