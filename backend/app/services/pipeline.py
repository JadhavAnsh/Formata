# Full processing flow
from typing import Dict, Any, Optional, Callable
import asyncio
import os
import time
import pandas as pd

from app.services.parser import parse_csv, parse_json, parse_excel, parse_markdown
from app.services.profiler import generate_profile_html, get_profile_summary
from app.services.normalization import standardize_columns, normalize_types
from app.services.type_enforcement import enforce_types, validate_ranges, detect_column_types
from app.services.missing_data import handle_missing_data, analyze_missing_data, get_missing_data_summary
from app.services.filtering import apply_filters
from app.services.noise import remove_duplicates, remove_outliers
from app.services.validation import validate_schema, get_validation_errors
from app.utils.logger import logger


class ProcessingPipeline:
    """
    Orchestrates the full data processing workflow
    Enhanced 13-step pipeline:
    1. Upload & Create Job
    2. Parse input file
    3. Profile raw data (HTML → Gemini → Markdown)
    4. Normalize data types and columns
    5. Enforce data types (new: ensure correct types for all columns)
    6. Handle missing data (new: fill, drop, or flag missing values)
    7. Apply filters
    8. Remove duplicates and outliers
    9. Validate results (with SSE error streaming)
    10. Profile clean data (HTML → Gemini → Markdown)
    11. Convert/Vectorize data
    12. Save outputs and generate reports
    13. Complete with manifest
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
            
            initial_rows = len(df)
            logger.info(f"File parsed. Rows: {len(df)}, Columns: {len(df.columns)}")
            await asyncio.sleep(0)
            
            # ============ STEP 3: Normalize data (25% progress) ============
            if progress_callback:
                progress_callback(0.25)
            logger.info("STEP 3: Normalizing data types and columns")
            
            original_columns = list(df.columns)
            df = standardize_columns(df)
            df = normalize_types(df)
            normalized_columns = list(df.columns)
            columns_renamed = sum(1 for o, n in zip(original_columns, normalized_columns) if o != n)
            logger.info(f"Normalization completed. Columns renamed: {columns_renamed}/{len(df.columns)}")
            logger.info(f"Column names: {list(df.columns)}")
            await asyncio.sleep(0)
            
            # ============ STEP 3.5: Type Enforcement (27% progress) ============
            if config.get("enforce_types", True):
                if progress_callback:
                    progress_callback(0.27)
                logger.info("STEP 3.5: Enforcing data types")
                
                type_map = config.get("type_map")
                auto_detect = config.get("auto_detect_types", True)
                
                df, type_report = enforce_types(df, type_map=type_map, auto_detect=auto_detect)
                logger.info(f"Type enforcement completed. Columns enforced: {type_report['columns_enforced']}")
                
                if type_report['errors']:
                    result["errors"].extend([f"Type enforcement: {err}" for err in type_report['errors']])
                
                # Add to result metadata
                result["metadata"]["type_enforcement"] = type_report
                
                # Validate ranges if provided
                range_rules = config.get("range_rules")
                if range_rules:
                    df, range_violations = validate_ranges(df, range_rules)
                    if range_violations:
                        logger.warning(f"Range validation found {len(range_violations)} violations")
                        result["metadata"]["range_violations"] = range_violations
                
                await asyncio.sleep(0)
            
            # ============ STEP 3.7: Missing Data Handling (30% progress) ============
            if config.get("handle_missing_data", True):
                if progress_callback:
                    progress_callback(0.30)
                logger.info("STEP 3.7: Handling missing data")
                
                # First, analyze missing data
                missing_analysis = analyze_missing_data(df)
                logger.info(f"Missing data analysis: {missing_analysis['total_missing']} missing values")
                
                if missing_analysis['total_missing'] > 0:
                    missing_summary = get_missing_data_summary(df)
                    logger.info(f"\n{missing_summary}")
                    
                    # Handle missing data
                    strategy = config.get("missing_data_strategy")
                    default_strategy = config.get("default_missing_strategy", "fill_mean")
                    flag_missing = config.get("flag_missing_data", False)
                    
                    # If flagging is requested, add 'flag' to the strategy
                    if flag_missing and strategy:
                        for col in missing_analysis['columns'].keys():
                            if col not in strategy:
                                strategy[col] = 'flag'
                    
                    df, missing_report = handle_missing_data(
                        df,
                        strategy=strategy,
                        default_strategy=default_strategy
                    )
                    
                    logger.info(f"Missing data handled. Columns processed: {missing_report['columns_processed']}")
                    logger.info(f"Rows dropped: {missing_report['rows_dropped']}, Columns dropped: {missing_report['columns_dropped']}")
                    
                    # Add to result
                    result["metadata"]["missing_data_analysis"] = missing_analysis
                    result["metadata"]["missing_data_handling"] = missing_report
                else:
                    logger.info("No missing data detected - skipping missing data handling")
                
                await asyncio.sleep(0)
            
            # ============ STEP 4: Apply filters (40% progress) ============
            if progress_callback:
                progress_callback(0.4)
            logger.info("STEP 4: Applying filters")
            
            rows_before_filters = len(df)
            filters = config.get("filters")
            if filters:
                df = apply_filters(df, filters)
                logger.info(f"Filters applied. Remaining rows: {len(df)}")
            rows_filtered = rows_before_filters - len(df)
            await asyncio.sleep(0)
            
            # Capture rows_before right before cleaning operations
            result["rows_before"] = len(df)
            
            # ============ STEP 5: Remove duplicates and outliers (50% progress) ============
            if progress_callback:
                progress_callback(0.5)
            logger.info("STEP 5: Removing duplicates and outliers")
            
            duplicates_removed = 0
            outliers_removed = 0
            
            if config.get("remove_duplicates", True):
                before_dedup = len(df)
                logger.info(f"Before duplicate removal: {before_dedup} rows")
                df = remove_duplicates(df)
                duplicates_removed = before_dedup - len(df)
                logger.info(f"After duplicate removal: {len(df)} rows (removed {duplicates_removed})")
                if duplicates_removed == 0:
                    logger.info("No duplicates found in dataset")
            else:
                logger.info("Duplicate removal is disabled in config")
            
            if config.get("remove_outliers", False):
                before_outliers = len(df)
                logger.info(f"Before outlier removal: {before_outliers} rows")
                df = remove_outliers(df)
                outliers_removed = before_outliers - len(df)
                logger.info(f"After outlier removal: {len(df)} rows (removed {outliers_removed})")
                if outliers_removed == 0:
                    logger.info("No outliers detected using IQR method")
            else:
                logger.info("Outlier removal is disabled in config")
            
            result["rows_after"] = len(df)
            await asyncio.sleep(0)
            
            # ============ STEP 6: Validate results (65% progress) ============
            if progress_callback:
                progress_callback(0.65)
            logger.info("STEP 6: Validating results")
            
            # Check for data quality issues (missing values, invalid types, etc.)
            if config.get("detect_data_quality_issues", True):
                quality_errors = []
                
                # Check for missing values
                missing_counts = df.isnull().sum()
                for col, count in missing_counts.items():
                    if count > 0:
                        percentage = (count / len(df)) * 100
                        quality_errors.append(
                            f"Column '{col}': {count} missing values ({percentage:.1f}%)"
                        )
                
                # Check for columns with all null values
                all_null_cols = df.columns[df.isnull().all()].tolist()
                for col in all_null_cols:
                    quality_errors.append(f"Column '{col}': All values are missing")
                
                if quality_errors:
                    result["errors"].extend(quality_errors)
                    logger.warning(f"Data quality check found {len(quality_errors)} issues")
                else:
                    logger.info("Data quality check: No issues found")
            
            # Schema validation (if rules provided)
            validation_rules = config.get("validation_rules")
            schema_errors = []
            if validation_rules:
                schema_errors = get_validation_errors(
                    {"records": df.to_dict(orient='records')},
                    validation_rules
                )
                if schema_errors:
                    result["errors"].extend(schema_errors)
                    logger.warning(f"Schema validation found {len(schema_errors)} issues")
            
            # Calculate comprehensive data quality score
            logger.info("Calculating multifactor data quality score")
            from app.services.validation import calculate_data_quality_score
            
            quality_score = calculate_data_quality_score(
                df=df,
                schema=validation_rules,
                missing_data_report=result["metadata"].get("missing_data_analysis"),
                type_enforcement_report=result["metadata"].get("type_enforcement"),
                validation_errors=schema_errors if schema_errors else None
            )
            
            result["metadata"]["quality_score"] = quality_score
            logger.info(f"Data Quality Score: {quality_score['overall_score']}/100 (Grade: {quality_score['grade']})")
            logger.info(f"  - Completeness: {quality_score['completeness_score']}/100")
            logger.info(f"  - Validity: {quality_score['validity_score']}/100")
            logger.info(f"  - Consistency: {quality_score['consistency_score']}/100")
            logger.info(f"  - Accuracy: {quality_score['accuracy_score']}/100")
            
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
                "rows_initial": initial_rows,
                "rows_before_cleaning": result["rows_before"],
                "rows_after": result["rows_after"],
                "rows_filtered": rows_filtered,
                "rows_removed": result["rows_before"] - result["rows_after"],
                "duplicates_removed": duplicates_removed,
                "outliers_removed": outliers_removed,
                "total_rows_removed": initial_rows - result["rows_after"],
                "columns": len(df.columns),
                "columns_renamed": columns_renamed,
                "data_normalized": True,
                "types_enforced": result["metadata"].get("type_enforcement", {}).get("columns_enforced", 0),
                "missing_data_handled": result["metadata"].get("missing_data_handling", {}).get("columns_processed", 0),
                "output_format": output_format,
                "processing_time_seconds": round(processing_time, 2),
                "error_count": len(result["errors"]),
                "quality_score": result["metadata"].get("quality_score", {})
            }
            
            result["status"] = "completed"
            result["metadata"]["processing_time"] = processing_time
            
            if progress_callback:
                progress_callback(1.0)
            
            logger.info(f"Enhanced pipeline completed successfully. Job: {job_id}. Time: {processing_time:.2f}s")
            logger.info(f"Summary: Types enforced on {result['summary']['types_enforced']} columns, Missing data handled for {result['summary']['missing_data_handled']} columns")
            
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

