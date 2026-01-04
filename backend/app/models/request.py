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
    
    # Type enforcement options
    enforce_types: bool = True
    type_map: Optional[Dict[str, str]] = None  # Column name -> type ('int', 'float', 'bool', 'datetime', 'string')
    auto_detect_types: bool = True
    range_rules: Optional[Dict[str, Dict[str, Any]]] = None  # Column name -> {'min': val, 'max': val, 'action': 'flag'|'drop'|'clip'}
    
    # Missing data handling options
    handle_missing_data: bool = True
    missing_data_strategy: Optional[Dict[str, str]] = None  # Column name -> strategy
    default_missing_strategy: str = 'fill_mean'  # Default strategy: 'fill_mean', 'fill_median', 'fill_mode', 'drop_rows', etc.
    flag_missing_data: bool = False  # Create flag columns for missing data


class ConvertRequest(BaseModel):
    """Request model for format conversion"""
    input_format: str
    output_format: str
    data: Dict[str, Any]
