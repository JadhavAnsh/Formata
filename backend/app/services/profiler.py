"""
Data profiling service using ydata-profiling
Generates HTML reports for raw and cleaned data
"""
import os
import pandas as pd
from ydata_profiling import ProfileReport
from app.utils.logger import logger


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
    profile = ProfileReport(
        df,
        title=f"{profile_type.upper()} Data Profile - Job {job_id}",
        explorative=True,
        progress_bar=False,
        html={'style': {'full_width': True}}
    )
    
    # Save HTML report
    report_path = os.path.join(report_dir, f"{job_id}_{profile_type}_profile.html")
    profile.to_file(report_path)
    
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
