# Full processing flow
from typing import Dict, Any, Optional, Callable
import asyncio
import os
import time
import pandas as pd

from app.services.parser import parse_csv, parse_json, parse_excel, parse_markdown
from app.services.profiler import generate_profile_html, get_profile_summary
from app.services.gemini_analyzer import analyze_profile_async
from app.services.normalization import standardize_columns, normalize_types
from app.services.filtering import apply_filters
from app.services.noise import remove_duplicates, remove_outliers
from app.services.validation import validate_schema, get_validation_errors
from app.utils.logger import logger


class ProcessingPipeline:
    """
    Orchestrates the full data processing workflow
    11-step pipeline:
    1. Upload & Create Job
    2. Parse input file
    3. Profile raw data (HTML → Gemini → Markdown)
    4. Normalize data types and columns
    5. Apply filters
    6. Remove duplicates and outliers
    7. Validate results (with SSE error streaming)
    8. Profile clean data (HTML → Gemini → Markdown)
    9. Convert/Vectorize data
    10. Save outputs and generate reports
    11. Complete with manifest
    """
    
    def __init__(self):
        self.upload_dir = "storage/uploads"
        self.output_dir = "storage/outputs"
        self.error_dir = "storage/errors"
        self.reports_dir = "storage/reports"
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.error_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
    
    async def run_async(
        self,
        job_id: str,
        file_path: str,
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete processing pipeline (asynchronous)
        Enhanced 11-step flow with profiling and AI analysis
        """
        start_time = time.time()
        
        result = {
            "job_id": job_id,
            "status": "processing",
            "rows_before": 0,
            "rows_after": 0,
            "output_path": None,
            "errors": [],
            "reports": {},
            "summary": {},
            "metadata": metadata or {}
        }
        
        try:
            logger.info(f"Starting enhanced async pipeline for job {job_id}")
            ext = os.path.splitext(file_path)[1].lower()
            
            # ============ STEP 2: Parse input file (20% progress) ============
            if progress_callback:
                progress_callback(0.2)
            logger.info("STEP 2: Parsing input file")
            
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
            
            # ============ STEP 3: Normalize data (25% progress) ============
            if progress_callback:
                progress_callback(0.25)
            logger.info("STEP 3: Normalizing data types and columns")
            
            df = standardize_columns(df)
            df = normalize_types(df)
            logger.info(f"Normalization completed. Columns: {list(df.columns)}")
            await asyncio.sleep(0)
            
            # ============ STEP 4: Apply filters (40% progress) ============
            if progress_callback:
                progress_callback(0.4)
            logger.info("STEP 4: Applying filters")
            
            filters = config.get("filters")
            if filters:
                df = apply_filters(df, filters)
                logger.info(f"Filters applied. Remaining rows: {len(df)}")
            await asyncio.sleep(0)
            
            # ============ STEP 5: Remove duplicates and outliers (50% progress) ============
            if progress_callback:
                progress_callback(0.5)
            logger.info("STEP 5: Removing duplicates and outliers")
            
            duplicates_removed = 0
            outliers_removed = 0
            
            if config.get("remove_duplicates", True):
                before_dedup = len(df)
                df = remove_duplicates(df)
                duplicates_removed = before_dedup - len(df)
                logger.info(f"Removed {duplicates_removed} duplicate rows")
            
            if config.get("remove_outliers", False):
                before_outliers = len(df)
                df = remove_outliers(df, method='iqr')
                outliers_removed = before_outliers - len(df)
                logger.info(f"Removed {outliers_removed} outlier rows")
            
            result["rows_after"] = len(df)
            await asyncio.sleep(0)
            
            # ============ STEP 6: Validate results (65% progress) ============
            if progress_callback:
                progress_callback(0.65)
            logger.info("STEP 6: Validating results")
            
            validation_rules = config.get("validation_rules")
            if validation_rules:
                errors = get_validation_errors(
                    {"records": df.to_dict(orient='records')},
                    validation_rules
                )
                if errors:
                    result["errors"].extend(errors)
                    logger.warning(f"Validation found {len(errors)} issues")
            
            await asyncio.sleep(0)
            
            # ============ STEP 7: Profile clean data (80% progress) ============
            if progress_callback:
                progress_callback(0.8)
            logger.info("STEP 7: Profiling clean data with ydata-profiling")
            
            try:
                # Generate HTML profile for clean data
                html_path = generate_profile_html(df, job_id, "clean")
                
                # Save HTML profile path directly (skip AI markdown generation)
                result["reports"]["clean_profile"] = html_path
                result["metadata"]["clean_profile_path"] = html_path
                logger.info(f"Clean profile HTML generated: {html_path}")
                
                await asyncio.sleep(0)
            
            except Exception as e:
                logger.error(f"Error profiling clean data: {str(e)}")
                result["errors"].append(f"Clean profiling failed: {str(e)}")
            
            # ============ STEP 8: Convert/Vectorize (90% progress) ============
            if progress_callback:
                progress_callback(0.9)
            logger.info("STEP 8: Converting/Vectorizing data")
            
            # TODO: Implement vectorization if needed
            # For now, just log placeholder
            logger.info("Vectorization placeholder - ready for implementation")
            await asyncio.sleep(0)
            
            # ============ STEP 9: Save outputs and generate reports (95% progress) ============
            if progress_callback:
                progress_callback(0.95)
            logger.info("STEP 9: Saving outputs and generating reports")
            
            output_format = config.get("output_format", "csv")
            output_path = os.path.join(self.output_dir, f"{job_id}.{output_format}")
            
            if output_format == "json":
                df.to_json(output_path, orient='records', indent=2)
            elif output_format == "csv":
                df.to_csv(output_path, index=False)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            result["output_path"] = output_path
            
            # Save error report
            if result["errors"]:
                error_path = os.path.join(self.error_dir, f"{job_id}_errors.txt")
                with open(error_path, 'w') as f:
                    f.write(f"Processing Errors for Job {job_id}\n")
                    f.write("=" * 50 + "\n\n")
                    for error in result["errors"]:
                        f.write(f"- {error}\n")
                result["reports"]["error_report"] = error_path
            
            logger.info(f"Outputs saved. Path: {output_path}")
            await asyncio.sleep(0)
            
            # ============ STEP 11: Complete with manifest (100% progress) ============
            processing_time = time.time() - start_time
            
            result["summary"] = {
                "rows_before": result["rows_before"],
                "rows_after": result["rows_after"],
                "rows_removed": result["rows_before"] - result["rows_after"],
                "duplicates_removed": duplicates_removed,
                "outliers_removed": outliers_removed,
                "columns": len(df.columns),
                "output_format": output_format,
                "processing_time_seconds": round(processing_time, 2),
                "error_count": len(result["errors"])
            }
            
            result["status"] = "completed"
            result["metadata"]["processing_time"] = processing_time
            
            if progress_callback:
                progress_callback(1.0)
            
            logger.info(f"Enhanced pipeline completed successfully. Job: {job_id}. Time: {processing_time:.2f}s")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            logger.error(f"Enhanced pipeline failed: {str(e)}")
            
            # Save error report
            error_path = os.path.join(self.error_dir, f"{job_id}_error.txt")
            with open(error_path, 'w') as f:
                f.write(f"Job {job_id} Error:\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"Rows before: {result['rows_before']}\n")
                f.write(f"Rows after: {result['rows_after']}\n")
        
        return result

