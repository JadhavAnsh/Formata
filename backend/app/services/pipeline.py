# Full processing flow
from typing import Dict, Any, Optional, Callable
import asyncio
import os
import pandas as pd

from app.services.parser import parse_csv, parse_json, parse_excel, parse_markdown
from app.services.normalization import standardize_columns, normalize_types
from app.services.filtering import apply_filters
from app.services.noise import remove_duplicates, remove_outliers
from app.services.validation import validate_schema, get_validation_errors
from app.utils.logger import logger


class ProcessingPipeline:
    """
    Orchestrates the full data processing workflow
    5-step pipeline:
    1. Parse input file
    2. Normalize data types and columns
    3. Apply filters
    4. Remove duplicates and outliers
    5. Validate results
    """
    
    def __init__(self):
        self.upload_dir = "storage/uploads"
        self.output_dir = "storage/outputs"
        self.error_dir = "storage/errors"
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.error_dir, exist_ok=True)
    
    def run(self, job_id: str, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete processing pipeline (synchronous)
        """
        result = {
            "job_id": job_id,
            "status": "processing",
            "rows_before": 0,
            "rows_after": 0,
            "output_path": None,
            "errors": [],
            "summary": {}
        }
        
        try:
            logger.info(f"Starting pipeline for job {job_id}")
            ext = os.path.splitext(file_path)[1].lower()
            
            # STEP 1: Parse input file
            logger.info("STEP 1: Parsing input file")
            if ext == ".csv":
                df = parse_csv(file_path)
            elif ext in [".xlsx", ".xls"]:
                df = parse_excel(file_path)
            elif ext == ".json":
                json_data = parse_json(file_path)
                if isinstance(json_data, dict) and 'records' in json_data:
                    df = pd.DataFrame(json_data['records'])
                elif isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                else:
                    df = pd.DataFrame([json_data])
            elif ext == ".md":
                content = parse_markdown(file_path)
                logger.info("Markdown parsed as text content")
                result["status"] = "completed"
                result["rows_before"] = len(content.split('\n'))
                result["rows_after"] = result["rows_before"]
                return result
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            result["rows_before"] = len(df)
            logger.info(f"File parsed. Rows: {len(df)}, Columns: {len(df.columns)}")
            
            # STEP 2: Normalize data types and columns
            logger.info("STEP 2: Normalizing data types and columns")
            df = standardize_columns(df)
            df = normalize_types(df)
            logger.info(f"Normalization completed. Columns: {list(df.columns)}")
            
            # STEP 3: Apply filters
            logger.info("STEP 3: Applying filters")
            filters = config.get("filters")
            if filters:
                df = apply_filters(df, filters)
                logger.info(f"Filters applied. Remaining rows: {len(df)}")
            
            # STEP 4: Remove duplicates and outliers
            logger.info("STEP 4: Removing duplicates and outliers")
            if config.get("remove_duplicates", True):
                df = remove_duplicates(df)
            
            if config.get("remove_outliers", False):
                df = remove_outliers(df, method='iqr')
            
            result["rows_after"] = len(df)
            logger.info(f"Noise removal completed. Final rows: {len(df)}")
            
            # STEP 5: Validate results
            logger.info("STEP 5: Validating results")
            validation_rules = config.get("validation_rules")
            if validation_rules:
                # Convert DataFrame to dict format for validation
                data_dict = {"records": df.to_dict(orient='records')}
                errors = get_validation_errors(data_dict, validation_rules)
                if errors:
                    result["errors"].extend(errors)
                    logger.warning(f"Validation found {len(errors)} issues")
            
            # Save output
            output_format = config.get("output_format", "json")
            output_path = os.path.join(self.output_dir, f"{job_id}.{output_format}")
            
            if output_format == "json":
                df.to_json(output_path, orient='records', indent=2)
            elif output_format == "csv":
                df.to_csv(output_path, index=False)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            result["output_path"] = output_path
            result["status"] = "completed"
            result["summary"] = {
                "rows_removed": result["rows_before"] - result["rows_after"],
                "columns": len(df.columns),
                "output_format": output_format
            }
            
            logger.info(f"Pipeline completed successfully. Job: {job_id}")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            logger.error(f"Pipeline failed: {str(e)}")
            
            # Save error report
            error_path = os.path.join(self.error_dir, f"{job_id}_error.txt")
            with open(error_path, 'w') as f:
                f.write(f"Job {job_id} Error:\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"Rows before: {result['rows_before']}\n")
                f.write(f"Rows after: {result['rows_after']}\n")
        
        return result
    
    async def run_async(
        self,
        job_id: str,
        file_path: str,
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete processing pipeline (asynchronous)
        """
        result = {
            "job_id": job_id,
            "status": "processing",
            "rows_before": 0,
            "rows_after": 0,
            "output_path": None,
            "errors": [],
            "summary": {}
        }
        
        try:
            logger.info(f"Starting async pipeline for job {job_id}")
            ext = os.path.splitext(file_path)[1].lower()
            
            # STEP 1: Parse input file (20% progress)
            if progress_callback:
                progress_callback(0.2)
            logger.info("STEP 1: Parsing input file")
            
            if ext == ".csv":
                df = parse_csv(file_path)
            elif ext in [".xlsx", ".xls"]:
                df = parse_excel(file_path)
            elif ext == ".json":
                json_data = parse_json(file_path)
                if isinstance(json_data, dict) and 'records' in json_data:
                    df = pd.DataFrame(json_data['records'])
                elif isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                else:
                    df = pd.DataFrame([json_data])
            elif ext == ".md":
                content = parse_markdown(file_path)
                result["status"] = "completed"
                result["rows_before"] = len(content.split('\n'))
                result["rows_after"] = result["rows_before"]
                return result
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            result["rows_before"] = len(df)
            logger.info(f"File parsed. Rows: {len(df)}, Columns: {len(df.columns)}")
            await asyncio.sleep(0)
            
            # STEP 2: Normalize data types and columns (40% progress)
            if progress_callback:
                progress_callback(0.4)
            logger.info("STEP 2: Normalizing data types and columns")
            df = standardize_columns(df)
            df = normalize_types(df)
            logger.info(f"Normalization completed. Columns: {list(df.columns)}")
            await asyncio.sleep(0)
            
            # STEP 3: Apply filters (60% progress)
            if progress_callback:
                progress_callback(0.6)
            logger.info("STEP 3: Applying filters")
            filters = config.get("filters")
            if filters:
                df = apply_filters(df, filters)
                logger.info(f"Filters applied. Remaining rows: {len(df)}")
            await asyncio.sleep(0)
            
            # STEP 4: Remove duplicates and outliers (80% progress)
            if progress_callback:
                progress_callback(0.8)
            logger.info("STEP 4: Removing duplicates and outliers")
            if config.get("remove_duplicates", True):
                df = remove_duplicates(df)
            
            if config.get("remove_outliers", False):
                df = remove_outliers(df, method='iqr')
            
            result["rows_after"] = len(df)
            logger.info(f"Noise removal completed. Final rows: {len(df)}")
            await asyncio.sleep(0)
            
            # STEP 5: Validate results (95% progress)
            if progress_callback:
                progress_callback(0.95)
            logger.info("STEP 5: Validating results")
            validation_rules = config.get("validation_rules")
            if validation_rules:
                errors = validate_dataframe(df, validation_rules)
                if errors:
                    result["errors"].extend(errors)
                    logger.warning(f"Validation found {len(errors)} issues")
            
            # Save output
            output_format = config.get("output_format", "json")
            output_path = os.path.join(self.output_dir, f"{job_id}.{output_format}")
            
            if output_format == "json":
                df.to_json(output_path, orient='records', indent=2)
            elif output_format == "csv":
                df.to_csv(output_path, index=False)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            result["output_path"] = output_path
            result["status"] = "completed"
            result["summary"] = {
                "rows_removed": result["rows_before"] - result["rows_after"],
                "columns": len(df.columns),
                "output_format": output_format
            }
            
            if progress_callback:
                progress_callback(1.0)
            
            logger.info(f"Async pipeline completed successfully. Job: {job_id}")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            logger.error(f"Async pipeline failed: {str(e)}")
            
            # Save error report
            error_path = os.path.join(self.error_dir, f"{job_id}_error.txt")
            with open(error_path, 'w') as f:
                f.write(f"Job {job_id} Error:\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"Rows before: {result['rows_before']}\n")
                f.write(f"Rows after: {result['rows_after']}\n")
        
        return result
