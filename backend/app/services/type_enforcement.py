# Type enforcement service
import pandas as pd
import numpy as np
import warnings
from typing import Dict, Any, List, Optional
from app.utils.logger import logger


def _parse_datetime(series: pd.Series) -> pd.Series:
    """Parse datetimes with format hints to avoid noisy warnings."""
    common_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]

    for fmt in common_formats:
        parsed = pd.to_datetime(series, errors="coerce", format=fmt)
        if parsed.notna().mean() > 0.7:
            return parsed

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Could not infer format",
            category=UserWarning,
        )
        return pd.to_datetime(series, errors="coerce", infer_datetime_format=True)


def detect_column_types(df: pd.DataFrame, confidence_threshold: float = 0.8) -> Dict[str, str]:
    """
    Detect the intended data type for each column based on content analysis
    
    Args:
        df: Input DataFrame
        confidence_threshold: Minimum ratio of valid values to enforce type (default 0.8)
    
    Returns:
        Dictionary mapping column names to detected types: 'int', 'float', 'bool', 'datetime', 'string'
    """
    detected_types = {}
    
    for col in df.columns:
        series = df[col].dropna()  # Ignore null values for type detection
        
        if len(series) == 0:
            detected_types[col] = 'string'
            continue
        
        # Convert to string for analysis
        str_series = series.astype(str).str.strip().str.lower()
        total_count = len(str_series)
        
        # Check for boolean
        bool_values = {'true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'y', 'n'}
        bool_matches = str_series.isin(bool_values).sum()
        if bool_matches / total_count >= confidence_threshold:
            detected_types[col] = 'bool'
            continue
        
        # Check for integer
        try:
            numeric = pd.to_numeric(series, errors='coerce')
            valid_numeric = numeric.notna().sum()
            
            if valid_numeric / total_count >= confidence_threshold:
                # Check if all numeric values are integers
                is_integer = (numeric.dropna() == numeric.dropna().astype(int)).all()
                if is_integer:
                    detected_types[col] = 'int'
                    continue
                else:
                    detected_types[col] = 'float'
                    continue
        except Exception:
            pass
        
        # Check for datetime
        try:
            datetime_series = _parse_datetime(series)
            valid_datetime = datetime_series.notna().sum()
            
            if valid_datetime / total_count >= confidence_threshold:
                detected_types[col] = 'datetime'
                continue
        except Exception:
            pass
        
        # Default to string
        detected_types[col] = 'string'
    
    return detected_types


def enforce_types(
    df: pd.DataFrame, 
    type_map: Optional[Dict[str, str]] = None,
    auto_detect: bool = True
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Enforce data types on DataFrame columns
    
    Args:
        df: Input DataFrame
        type_map: Optional dictionary mapping column names to desired types
        auto_detect: If True, automatically detect types for columns not in type_map
    
    Returns:
        Tuple of (processed DataFrame, enforcement report)
    """
    if df is None or df.empty:
        return df, {"columns_enforced": 0, "conversions": {}, "errors": []}
    
    df = df.copy()
    report = {
        "columns_enforced": 0,
        "conversions": {},
        "errors": []
    }
    
    # Auto-detect types if enabled
    if auto_detect:
        detected_types = detect_column_types(df)
        if type_map:
            # Merge with provided type_map (type_map takes precedence)
            detected_types.update(type_map)
        type_map = detected_types
    
    if not type_map:
        return df, report
    
    for col, target_type in type_map.items():
        if col not in df.columns:
            report["errors"].append(f"Column '{col}' not found in DataFrame")
            continue
        
        try:
            original_type = str(df[col].dtype)
            
            if target_type == 'bool':
                # Convert to boolean
                str_series = df[col].astype(str).str.strip().str.lower()
                df[col] = str_series.map({
                    'true': True, 't': True, 'yes': True, 'y': True, '1': True,
                    'false': False, 'f': False, 'no': False, 'n': False, '0': False
                })
                
            elif target_type == 'int':
                # Convert to integer
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                
            elif target_type == 'float':
                # Convert to float
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            elif target_type == 'datetime':
                # Convert to datetime
                df[col] = _parse_datetime(df[col])
                
            elif target_type == 'string':
                # Convert to string
                df[col] = df[col].astype(str).replace('nan', None)
            
            new_type = str(df[col].dtype)
            report["conversions"][col] = {
                "original": original_type,
                "target": target_type,
                "final": new_type
            }
            report["columns_enforced"] += 1
            
            logger.info(f"Type enforced: {col} ({original_type} → {new_type})")
            
        except Exception as e:
            error_msg = f"Failed to enforce type for column '{col}': {str(e)}"
            report["errors"].append(error_msg)
            logger.warning(error_msg)
    
    return df, report


def validate_ranges(
    df: pd.DataFrame,
    range_rules: Dict[str, Dict[str, Any]]
) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate numeric columns against expected ranges
    
    Args:
        df: Input DataFrame
        range_rules: Dict mapping column names to {'min': value, 'max': value, 'action': 'flag'|'drop'|'clip'}
    
    Returns:
        Tuple of (processed DataFrame, list of violations)
    """
    if df is None or df.empty or not range_rules:
        return df, []
    
    df = df.copy()
    violations = []
    
    for col, rules in range_rules.items():
        if col not in df.columns:
            continue
        
        min_val = rules.get('min')
        max_val = rules.get('max')
        action = rules.get('action', 'flag')  # 'flag', 'drop', or 'clip'
        
        # Get numeric series
        numeric_col = pd.to_numeric(df[col], errors='coerce')
        
        # Check violations
        if min_val is not None:
            below_min = numeric_col < min_val
            if below_min.any():
                violations.append({
                    "column": col,
                    "rule": "min",
                    "expected": min_val,
                    "violations_count": below_min.sum()
                })
                
                if action == 'drop':
                    df = df[~below_min]
                elif action == 'clip':
                    df.loc[below_min, col] = min_val
        
        if max_val is not None:
            above_max = numeric_col > max_val
            if above_max.any():
                violations.append({
                    "column": col,
                    "rule": "max",
                    "expected": max_val,
                    "violations_count": above_max.sum()
                })
                
                if action == 'drop':
                    df = df[~above_max]
                elif action == 'clip':
                    df.loc[above_max, col] = max_val
    
    return df, violations
