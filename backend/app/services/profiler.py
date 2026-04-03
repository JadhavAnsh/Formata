"""
Data profiling service using ydata-profiling
Generates HTML reports for raw and cleaned data
"""
import json
import os
import pandas as pd
from scipy.stats import ks_2samp
from app.utils.logger import logger

try:
    from ydata_profiling import ProfileReport
except Exception:  # pragma: no cover - optional dependency fallback
    ProfileReport = None


BASELINE_STATS_PATH = "storage/reports/clean_baseline_stats.json"


def generate_profile_html(df: pd.DataFrame, job_id: str, profile_type: str = "raw") -> str:
    """
    Generate HTML profile report for a DataFrame
    
    Args:
        df: DataFrame to profile
        job_id: Job identifier
        profile_type: "raw" or "clean"
    
    Returns:
        Path to generated HTML report
    """
    logger.info(f"Generating {profile_type} data profile for job {job_id}")
    
    # Create reports directory
    report_dir = "storage/reports"
    os.makedirs(report_dir, exist_ok=True)
    
    # Generate profile with ydata-profiling
    # Use explorative config for better performance and compatibility
    report_path = os.path.join(report_dir, f"{job_id}_{profile_type}_profile.html")
    if ProfileReport is None:
        logger.warning(f"ydata-profiling is unavailable; writing fallback profile for job {job_id}")
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write(
                "<html><head><meta charset='utf-8'><title>Profile unavailable</title></head><body>"
                f"<h1>{profile_type.upper()} Data Profile - Job {job_id}</h1>"
                "<p>ydata-profiling is not installed in this environment.</p>"
                "</body></html>"
            )
        logger.info(f"Profile report generated: {report_path}")
        return report_path

    try:
        profile = ProfileReport(
            df,
            title=f"{profile_type.upper()} Data Profile - Job {job_id}",
            explorative=True,
            progress_bar=False,
            html={'style': {'full_width': True}}
        )

        # Save HTML report
        profile.to_file(report_path)
    except Exception as exc:
        logger.warning(f"ydata-profiling failed for {profile_type} profile on job {job_id}: {exc}")
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write(
                "<html><head><meta charset='utf-8'><title>Profile unavailable</title></head><body>"
                f"<h1>{profile_type.upper()} Data Profile - Job {job_id}</h1>"
                "<p>ydata-profiling could not render this dataset.</p>"
                f"<pre>{exc}</pre>"
                "</body></html>"
            )
    
    logger.info(f"Profile report generated: {report_path}")
    return report_path



def get_profile_summary(df: pd.DataFrame) -> dict:
    """
    Extract key statistics from DataFrame for quick summary
    
    Args:
        df: DataFrame to summarize
    
    Returns:
        Dictionary with key statistics
    """
    try:
        summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_cells": len(df) * len(df.columns),
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
            "duplicate_rows": df.duplicated().sum()
        }
        return summary
    
    except Exception as e:
        logger.error(f"Error getting profile summary: {str(e)}")
        raise


def _build_distribution_baseline(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    baseline = {
        "row_count": int(len(df)),
        "numeric_columns": numeric_cols,
        "samples": {},
    }
    for col in numeric_cols:
        series = pd.to_numeric(df[col], errors='coerce').dropna()
        if not series.empty:
            baseline["samples"][col] = series.astype(float).tolist()
    return baseline


def save_clean_baseline(df: pd.DataFrame, baseline_path: str = BASELINE_STATS_PATH) -> str:
    """
    Persist a clean baseline profile used by drift detection for future uploads.
    """
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    baseline = _build_distribution_baseline(df)
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f)
    return baseline_path


def detect_data_drift(
    df: pd.DataFrame,
    baseline_path: str = BASELINE_STATS_PATH,
    alpha: float = 0.05,
) -> dict:
    """
    Compare current data distributions against the stored clean baseline using KS test.
    """
    report = {
        "status": "ok",
        "baseline_path": baseline_path,
        "has_baseline": os.path.exists(baseline_path),
        "alpha": alpha,
        "drifted_columns": [],
        "column_results": {},
        "warning": None,
    }

    if df is None or df.empty:
        report["status"] = "skipped"
        report["warning"] = "No data available for drift detection"
        return report

    if not os.path.exists(baseline_path):
        report["status"] = "no_baseline"
        report["warning"] = "No baseline found; drift detection skipped"
        return report

    try:
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        baseline_samples = baseline.get("samples", {})
        for col, base_vals in baseline_samples.items():
            if col not in df.columns:
                continue

            current_vals = pd.to_numeric(df[col], errors='coerce').dropna().astype(float).tolist()
            if len(base_vals) < 10 or len(current_vals) < 10:
                continue

            stat, pvalue = ks_2samp(base_vals, current_vals)
            drifted = bool(pvalue < alpha)
            report["column_results"][col] = {
                "ks_statistic": float(stat),
                "p_value": float(pvalue),
                "drifted": drifted,
            }
            if drifted:
                report["drifted_columns"].append(col)

        if report["drifted_columns"]:
            report["status"] = "drift_detected"
            report["warning"] = (
                "Data Drift warning: KS test indicates distribution changes in "
                + ", ".join(report["drifted_columns"])
            )

        return report
    except Exception as exc:
        logger.warning(f"Drift detection failed: {exc}")
        report["status"] = "error"
        report["warning"] = f"Drift detection error: {exc}"
        return report
