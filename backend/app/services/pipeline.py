# Full processing flow
from typing import Dict, Any, Optional, Callable
import asyncio
import json
import os
import time
import pandas as pd

from app.services.parser import parse_csv, parse_json, parse_excel, parse_markdown
from app.services.profiler import (
    generate_profile_html,
    get_profile_summary,
    detect_data_drift,
    save_clean_baseline,
)
from app.services.normalization import standardize_columns, prepare_for_export
from app.services.normalization_optimized import normalize_types_optimized
from app.services.normalizer import infer_semantic_schema_labels
from app.services.type_enforcement import enforce_types, validate_ranges, detect_column_types
from app.services.missing_data import handle_missing_data, analyze_missing_data, get_missing_data_summary
from app.services.filtering import apply_filters
from app.services.noise import remove_duplicates, remove_outliers
from app.services.validation import validate_schema, get_validation_errors
from app.services.vectorization import dataframe_to_vectors, save_vectors_hdf5, save_vectors_pickle
from app.config.file_size_config import FileSizeConfig, get_optimized_config
from app.utils.logger import logger
from app.services.time_tracker import get_tracker, cleanup_tracker


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
        timer = get_tracker(job_id)  # Initialize time tracker
        
        result = {
            "job_id": job_id,
            "status": "processing",
            "rows_before": 0,
            "rows_after": 0,
            "output_path": None,
            "before_data": None,
            "after_data": None,
            "errors": [],
            "reports": {},
            "summary": {},
            "metadata": metadata or {}
        }
        
        try:
            logger.info(f"Starting enhanced async pipeline for job {job_id}")
            ext = os.path.splitext(file_path)[1].lower()
            
            # Convert config to mutable dict for updates
            if isinstance(config, dict):
                config_dict = config.copy()
            else:
                config_dict = config.dict() if hasattr(config, 'dict') else {}
            
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
            raw_df_snapshot = df.copy()
            logger.info(f"File parsed. Rows: {len(df):,}, Columns: {len(df.columns)}")
            await asyncio.sleep(0)
            
            # ============ FILE SIZE OPTIMIZATION ============
            # Estimate file size and auto-adjust config
            file_size_mb = FileSizeConfig.estimate_file_size_mb(df)
            logger.info(f"Estimated data size: {file_size_mb:.1f} MB")
            
            # Apply file-size aware config
            size_aware_config = get_optimized_config(file_size_mb, user_overrides=config_dict)
            for key, value in size_aware_config.items():
                if key not in config_dict or config_dict[key] is None:
                    config_dict[key] = value
            
            result_preview_rows = int(size_aware_config.get("result_preview_rows", 2000))
            enable_auto_schema = bool(size_aware_config.get("enable_auto_schema", True))
            enable_drift_detection = bool(size_aware_config.get("enable_drift_detection", True))
            enable_profiles = bool(size_aware_config.get("enable_profiles", False))
            enable_vectorization = bool(size_aware_config.get("enable_vectorization", False))

            # Store preview-grade raw snapshot for result comparison/diff views.
            result["before_data"] = {
                "rowCount": int(len(raw_df_snapshot)),
                "rows": raw_df_snapshot.head(max(0, result_preview_rows)).to_dict(orient="records"),
            }

            if enable_profiles and file_size_mb < 50:
                try:
                    raw_profile_path = generate_profile_html(raw_df_snapshot, job_id, "raw")
                    result["reports"]["raw_profile"] = raw_profile_path
                    result["metadata"]["raw_profile_path"] = raw_profile_path
                    logger.info(f"Raw profile HTML generated: {raw_profile_path}")
                except Exception as exc:
                    logger.warning(f"Raw profiling failed: {exc}")
            
            # ============ STEP 3: Optimize Normalization (22%-25% progress) ============
            if progress_callback:
                progress_callback(0.22)
            logger.info(f"STEP 3: Normalizing data types and columns (file_size={file_size_mb:.1f}MB)")
            
            original_columns = list(df.columns)
            df = standardize_columns(df)
            
            # Use optimized hybrid detection for large files
            def norm_progress(p):
                # Map sub-progress [0, 1] to pipeline progress [0.22, 0.25]
                if progress_callback:
                    progress_callback(0.22 + p * 0.03)
            
            df = normalize_types_optimized(df, progress_callback=norm_progress)
            normalized_columns = list(df.columns)
            columns_renamed = sum(1 for o, n in zip(original_columns, normalized_columns) if o != n)
            logger.info(f"Normalization completed. Columns renamed: {columns_renamed}/{len(df.columns)}")
            logger.info(f"Column names: {list(df.columns)}")

            # Auto-schema intelligence: semantic labeling of columns.
            if enable_auto_schema and file_size_mb < 100:  # Skip RF for huge files
                try:
                    schema_labels = infer_semantic_schema_labels(df)
                    result["metadata"]["auto_schema"] = schema_labels
                except Exception as exc:
                    logger.warning(f"Auto-schema inference failed: {exc}")
            await asyncio.sleep(0)

            # Drift detection against previously stored clean baseline.
            if enable_drift_detection and file_size_mb < 100:
                try:
                    drift_report = detect_data_drift(df)
                    result["reports"]["drift"] = drift_report
                    result["metadata"]["drift_detection"] = drift_report
                    if drift_report.get("warning") and drift_report.get("status") == "drift_detected":
                        result["errors"].append(drift_report["warning"])
                except Exception as exc:
                    logger.warning(f"Drift detection failed: {exc}")
            
            # ============ STEP 3.5: Type Enforcement (27% progress) ============
            if size_aware_config.get("enforce_types", True):
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
            if size_aware_config.get("handle_missing_data", True):
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
                    default_strategy = config.get("default_missing_strategy", "preserve")
                    flag_missing = config.get("flag_missing_data", False)
                    
                    # If flagging is requested, add 'flag' to the strategy
                    if flag_missing and strategy:
                        for col in missing_analysis['columns'].keys():
                            if col not in strategy:
                                strategy[col] = 'flag'
                    
                    df, missing_report = handle_missing_data(
                        df,
                        strategy=strategy,
                        default_strategy=default_strategy,
                        use_knn_for_smart=size_aware_config.get("use_knn_imputation", False),
                        knn_neighbors=int(size_aware_config.get("knn_neighbors", 5)),
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
            
            if size_aware_config.get("remove_duplicates", True):
                before_dedup = len(df)
                logger.info(f"Before duplicate removal: {before_dedup:,} rows")
                df = remove_duplicates(df)
                duplicates_removed = before_dedup - len(df)
                logger.info(f"After duplicate removal: {len(df):,} rows (removed {duplicates_removed:,})")
                if duplicates_removed == 0:
                    logger.info("No duplicates found in dataset")
            else:
                logger.info("Duplicate removal is disabled for this file size")
            
            if size_aware_config.get("remove_outliers", False):
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
            if size_aware_config.get("detect_data_quality_issues", True):
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
            
            if enable_profiles:
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

            if enable_vectorization and file_size_mb < 100:  # Skip for huge files
                try:
                    vector_method = size_aware_config.get("vectorization_method", "hybrid")
                    vectors, vector_meta = dataframe_to_vectors(df, method=vector_method)

                    vector_pkl_path = os.path.join(self.output_dir, f"{job_id}_vectors.pkl")
                    vector_h5_path = os.path.join(self.output_dir, f"{job_id}_vectors.h5")
                    save_vectors_pickle(vectors, vector_meta, vector_pkl_path)
                    save_vectors_hdf5(vectors, vector_meta, vector_h5_path)

                    result["reports"]["vectors"] = {
                        "pkl_path": vector_pkl_path,
                        "h5_path": vector_h5_path,
                        "shape": list(vectors.shape),
                        "method": vector_method,
                    }
                    result["metadata"]["vectorization"] = {
                        "shape": list(vectors.shape),
                        "method": vector_method,
                        "n_samples": int(vector_meta.get("n_samples", 0)),
                        "n_features": int(vector_meta.get("n_features", 0)),
                    }
                except Exception as exc:
                    result["errors"].append(f"Vectorization failed: {exc}")
                    logger.warning(f"Vectorization failed for {job_id}: {exc}")
            await asyncio.sleep(0)
            
            # ============ STEP 9: Save outputs and generate reports (95% progress) ============
            if progress_callback:
                progress_callback(0.95)
            logger.info("STEP 9: Saving outputs and generating reports")
            
            output_format = size_aware_config.get("output_format", "csv")
            output_path = os.path.join(self.output_dir, f"{job_id}.{output_format}")
            export_df = prepare_for_export(df)
            
            if output_format == "json":
                export_df.to_json(output_path, orient='records', indent=2)
            elif output_format == "csv":
                export_df.to_csv(output_path, index=False)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            result["output_path"] = output_path

            result["after_data"] = {
                "rowCount": int(len(df)),
                "rows": df.head(max(0, result_preview_rows)).to_dict(orient="records"),
            }

            # Persist latest clean baseline for future drift checks.
            if enable_drift_detection:
                try:
                    baseline_path = save_clean_baseline(df)
                    result["reports"]["drift_baseline"] = baseline_path
                    result["metadata"]["drift_baseline_path"] = baseline_path
                except Exception as exc:
                    logger.warning(f"Failed to save drift baseline: {exc}")
            
            # Save error report
            if result["errors"]:
                error_path = os.path.join(self.error_dir, f"{job_id}_errors.txt")
                with open(error_path, 'w') as f:
                    f.write(f"Processing Errors for Job {job_id}\n")
                    f.write("=" * 50 + "\n\n")
                    for error in result["errors"]:
                        f.write(f"- {error}\n")
                    drift = result.get("metadata", {}).get("drift_detection")
                    if drift:
                        f.write("\nDrift Report:\n")
                        f.write(json.dumps(drift, indent=2))
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
                "drift_status": result["metadata"].get("drift_detection", {}).get("status"),
                "output_format": output_format,
                "processing_time_seconds": round(processing_time, 2),
                "error_count": len(result["errors"]),
                "quality_score": result["metadata"].get("quality_score", {})
            }
            
            result["status"] = "completed"
            result["metadata"]["processing_time"] = processing_time
            
            # Add detailed timing information
            timing_summary = timer.get_summary()
            result["metadata"]["timing_details"] = timing_summary
            timer.log_summary()
            cleanup_tracker(job_id)
            
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


