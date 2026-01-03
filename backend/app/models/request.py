# Input schemas
from pydantic import BaseModel
from typing import Optional, Dict, Any


class IngestRequest(BaseModel):
    """Request model for data ingestion"""
    pass


class ProcessRequest(BaseModel):
    """Request model for job processing"""
    filters: Optional[Dict[str, Any]] = None
    normalize: bool = True
    remove_duplicates: bool = True


class ConvertRequest(BaseModel):
    """Request model for format conversion"""
    input_format: str
    output_format: str
    data: Dict[str, Any]
