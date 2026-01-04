# Missing data handling service
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Literal
from app.utils.logger import logger


MissingDataStrategy = Literal['fill_mean', 'fill_median', 'fill_mode', 'fill_forward', 'fill_backward', 'fill_value', 'drop_rows', 'drop_columns', 'flag']


def analyze_missing_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze missing data patterns in the DataFrame
    
    Returns:
        Dictionary containing missing data statistics and recommendations
    """
    if df is None or df.empty:
        return {"total_missing": 0, "columns": {}, "recommendations": {}}
    
    total_missing = int(df.isnull().sum().sum())
    total_cells = len(df) * len(df.columns)
    
    report = {
        "total_rows": len(df),
        "total_missing": total_missing,
        "missing_percentage": round((total_missing / total_cells) * 100, 2) if total_cells > 0 else 0.0,
        "columns": {},
        "recommendations": {}
    }
    
    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        if missing_count > 0:
            missing_pct = round((missing_count / len(df)) * 100, 2)
            
            # Determine column type for recommendation
            col_dtype = str(df[col].dtype)
            
            if 'int' in col_dtype or 'float' in col_dtype:
                recommended = 'fill_median'
            elif 'bool' in col_dtype:
                recommended = 'fill_mode'
            elif 'datetime' in col_dtype:
                recommended = 'fill_forward'
            else:
                recommended = 'fill_mode'
            
            # If too many missing values, recommend dropping
            if missing_pct > 50:
                recommended = 'drop_columns'
            
            report["columns"][col] = {
                "missing_count": missing_count,
                "missing_percentage": missing_pct,
                "dtype": col_dtype
            }
            report["recommendations"][col] = recommended
    
    return report


def handle_missing_data(
    df: pd.DataFrame,
    strategy: Optional[Dict[str, str]] = None,
    default_strategy: str = 'fill_mean',
    fill_value: Any = None,
    flag_column_suffix: str = '_missing'
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing data in DataFrame using specified strategies
    
    Args:
        df: Input DataFrame
        strategy: Dictionary mapping column names to strategies
        default_strategy: Default strategy for columns not in strategy dict
        fill_value: Value to use for 'fill_value' strategy
        flag_column_suffix: Suffix for flag columns when using 'flag' strategy
    
    Returns:
        Tuple of (processed DataFrame, handling report)
    """
    if df is None or df.empty:
        return df, {"columns_processed": 0, "rows_dropped": 0, "columns_dropped": 0, "actions": {}}
    
    df = df.copy()
    initial_rows = len(df)
    initial_cols = len(df.columns)
    
    report = {
        "columns_processed": 0,
        "rows_dropped": 0,
        "columns_dropped": 0,
        "actions": {}
    }
    
    # Analyze missing data first
    analysis = analyze_missing_data(df)
    
    # If no strategy provided, use recommendations
    if strategy is None:
        strategy = analysis.get("recommendations", {})
    
    # Process each column
    columns_to_drop = []
    
    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue  # No missing data in this column
        
        col_strategy = strategy.get(col, default_strategy)
        
        try:
            if col_strategy == 'fill_mean':
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].mean()
                    df[col] = df[col].fillna(fill_val)
                    report["actions"][col] = f"Filled with mean ({fill_val:.2f})"
                else:
                    # Fall back to mode for non-numeric
                    fill_val = df[col].mode()[0] if not df[col].mode().empty else None
                    df[col] = df[col].fillna(fill_val).infer_objects(copy=False)
                    report["actions"][col] = f"Filled with mode (mean not applicable for non-numeric)"
            
            elif col_strategy == 'fill_median':
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].median()
                    df[col] = df[col].fillna(fill_val)
                    report["actions"][col] = f"Filled with median ({fill_val:.2f})"
                else:
                    fill_val = df[col].mode()[0] if not df[col].mode().empty else None
                    df[col] = df[col].fillna(fill_val).infer_objects(copy=False)
                    report["actions"][col] = f"Filled with mode (median not applicable)"
            
            elif col_strategy == 'fill_mode':
                mode_val = df[col].mode()[0] if not df[col].mode().empty else None
                df[col] = df[col].fillna(mode_val).infer_objects(copy=False)
                report["actions"][col] = f"Filled with mode ({mode_val})"
            
            elif col_strategy == 'fill_forward':
                df[col] = df[col].ffill()
                # If still has NaN at the beginning, fill with backward
                df[col] = df[col].bfill()
                report["actions"][col] = "Forward filled (with backward fill for leading NaNs)"
            
            elif col_strategy == 'fill_backward':
                df[col] = df[col].bfill()
                # If still has NaN at the end, fill with forward
                df[col] = df[col].ffill()
                report["actions"][col] = "Backward filled (with forward fill for trailing NaNs)"
            
            elif col_strategy == 'fill_value':
                df[col] = df[col].fillna(fill_value)
                report["actions"][col] = f"Filled with custom value ({fill_value})"
            
            elif col_strategy == 'drop_columns':
                columns_to_drop.append(col)
                report["actions"][col] = "Marked for column drop"
            
            elif col_strategy == 'drop_rows':
                rows_before = len(df)
                df.dropna(subset=[col], inplace=True)
                rows_dropped = rows_before - len(df)
                report["actions"][col] = f"Dropped {rows_dropped} rows with missing values"
                report["rows_dropped"] += rows_dropped
            
            elif col_strategy == 'flag':
                flag_col_name = f"{col}{flag_column_suffix}"
                df[flag_col_name] = df[col].isnull()
                report["actions"][col] = f"Created flag column '{flag_col_name}'"
            
            report["columns_processed"] += 1
            logger.info(f"Missing data handled for '{col}': {col_strategy}")
            
        except Exception as e:
            error_msg = f"Failed to handle missing data for column '{col}': {str(e)}"
            report["actions"][col] = f"Error: {str(e)}"
            logger.warning(error_msg)
    
    # Drop columns marked for removal
    if columns_to_drop:
        df.drop(columns=columns_to_drop, inplace=True)
        report["columns_dropped"] = len(columns_to_drop)
        logger.info(f"Dropped {len(columns_to_drop)} columns: {columns_to_drop}")
    
    report["final_rows"] = len(df)
    report["final_columns"] = len(df.columns)
    
    return df, report


def get_missing_data_summary(df: pd.DataFrame) -> str:
    """
    Get a human-readable summary of missing data
    
    Returns:
        Formatted string summary
    """
    if df is None or df.empty:
        return "No data to analyze"
    
    analysis = analyze_missing_data(df)
    
    if analysis["total_missing"] == 0:
        return "✓ No missing values detected"
    
    summary_lines = [
        f"Missing Data Summary:",
        f"- Total missing values: {analysis['total_missing']} ({analysis['missing_percentage']:.2f}%)",
        f"- Affected columns: {len(analysis['columns'])}/{len(df.columns)}"
    ]
    
    if analysis["columns"]:
        summary_lines.append("\nColumns with missing data:")
        for col, info in sorted(analysis["columns"].items(), key=lambda x: x[1]["missing_percentage"], reverse=True):
            summary_lines.append(
                f"  • {col}: {info['missing_count']} values ({info['missing_percentage']:.1f}%) - "
                f"Recommended: {analysis['recommendations'].get(col, 'N/A')}"
            )
    
    return "\n".join(summary_lines)
