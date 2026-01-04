# /convert endpoint
# Format conversion utility
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, List
import io
import csv
import json
import tempfile
import os

from app.utils.logger import logger
from app.services.conversion import csv_to_json, json_to_csv

router = APIRouter(prefix="/convert", tags=["convert"])


class ConvertRequest(BaseModel):
    """Request model for format conversion"""
    input_format: str
    output_format: str
    data: Dict[str, Any]


class JsonToCSVRequest(BaseModel):
    """Request model for JSON to CSV conversion"""
    data: Dict[str, Any] | List[Dict[str, Any]]


@router.post("/json-to-csv")
async def convert_json_to_csv(request: JsonToCSVRequest) -> Dict[str, Any]:
    """
    Convert JSON to CSV format
    - Accepts JSON data (dict with records or list of objects)
    - Returns CSV as string
    - Handles nested JSON flattening
    """
    try:
        logger.info("Converting JSON to CSV")
        
        # Create temporary file for CSV output
        temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
        os.close(temp_fd)
        
        try:
            # Use conversion service
            json_to_csv(request.data, temp_path)
            
            # Read CSV content
            with open(temp_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            return {
                "status": "success",
                "format": "csv",
                "content": csv_content,
                "message": "Successfully converted JSON to CSV"
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except ValueError as e:
        logger.error(f"Validation error in JSON to CSV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error converting JSON to CSV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting JSON to CSV: {str(e)}"
        )


@router.post("/csv-to-json")
async def convert_csv_to_json(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert CSV to JSON format
    - Accepts CSV file upload
    - Returns JSON with records array
    - Handles type inference and normalization
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a CSV file"
            )
        
        logger.info(f"Converting CSV to JSON: {file.filename}")
        
        # Create temporary file for CSV
        temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
        
        try:
            # Save uploaded file temporarily
            content = await file.read()
            with os.fdopen(temp_fd, 'wb') as f:
                f.write(content)
            
            # Use conversion service
            result = csv_to_json(temp_path)
            
            return {
                "status": "success",
                "format": "json",
                "data": result,
                "message": "Successfully converted CSV to JSON"
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"File error in CSV to JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file or file not found"
        )
    except Exception as e:
        logger.error(f"Error converting CSV to JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting CSV to JSON: {str(e)}"
        )


@router.post("/")
async def convert_data(request: ConvertRequest) -> Dict[str, Any]:
    """
    Generic format conversion endpoint
    - Supports CSV ↔ JSON
    - Validates input and output formats
    """
    try:
        supported_formats = ["csv", "json"]
        input_fmt = request.input_format.lower()
        output_fmt = request.output_format.lower()
        
        if input_fmt not in supported_formats or output_fmt not in supported_formats:
            raise ValueError(f"Supported formats: {supported_formats}")
        
        if input_fmt == output_fmt:
            raise ValueError("Input and output formats must be different")
        
        logger.info(f"Converting data from {input_fmt} to {output_fmt}")
        
        if input_fmt == "json" and output_fmt == "csv":
            # JSON to CSV conversion
            temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
            os.close(temp_fd)
            
            try:
                json_to_csv(request.data, temp_path)
                with open(temp_path, 'r', encoding='utf-8') as f:
                    csv_content = f.read()
                
                return {
                    "status": "success",
                    "input_format": input_fmt,
                    "output_format": output_fmt,
                    "content": csv_content
                }
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        else:
            raise ValueError("CSV to JSON conversion requires file upload. Use /csv-to-json endpoint")
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error converting data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting data: {str(e)}"
        )
