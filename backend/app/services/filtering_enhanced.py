# Enhanced filtering with multi-filter support, statistical filters, and text analysis
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re


def _resolve_column(df: pd.DataFrame, key: str) -> str | None:
    """Resolve column by exact match, substring, or fuzzy matching"""
    key = key.lower().strip()

    for col in df.columns:
        col_l = col.lower()
        if key == col_l or key in col_l or col_l in key:
            return col

    return None


def _detect_column_type(series: pd.Series) -> str:
    """
    Detect column type with enhanced text analysis
    Returns: 'boolean', 'numeric', 'datetime', or 'text'
    """
    # Check explicit type first
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    
    # Count non-null values
    non_null_count = series.notna().sum()
    total_count = len(series)
    
    if non_null_count == 0:
        return "text"  # Default to text if all null
    
    threshold = 0.6
    
    # Try numeric conversion
    try:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() / non_null_count > threshold:
            return "numeric"
    except Exception:
        pass

    # Try datetime conversion with multiple formats (more robust)
    try:
        parsed = _try_parse_datetime(series)
        if parsed is not None and parsed.notna().sum() / non_null_count > threshold:
            return "datetime"
    except Exception:
        pass

    # Text analysis for text columns
    # Check for URI patterns, codes, identifiers vs prose
    text_indicators = _analyze_text_content(series, non_null_count)
    if text_indicators['is_text_dominant']:
        return "text"

    # Default to text if not clearly numeric or datetime
    return "text"


def _try_parse_datetime(series: pd.Series) -> Optional[pd.Series]:
    """Try parsing with multiple datetime formats"""
    common_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S.%f",
        "%m/%d/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
    ]
    
    for fmt in common_formats:
        try:
            parsed = pd.to_datetime(series, errors="coerce", format=fmt)
            if parsed.notna().sum() > 0:
                return parsed
        except Exception:
            continue
    
    # Fallback to pandas inference
    try:
        return pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
    except Exception:
        return None


def _analyze_text_content(series: pd.Series, non_null_count: int) -> Dict[str, Any]:
    """Analyze text content to determine if it's primarily text or structured data"""
    indicators = {
        'is_text_dominant': False,
        'avg_length': 0,
        'unique_ratio': 0,
        'contains_special_chars': 0,
    }
    
    try:
        str_series = series.dropna().astype(str)
        
        if len(str_series) == 0:
            return indicators
        
        # Average length of values
        avg_length = str_series.str.len().mean()
        indicators['avg_length'] = avg_length
        
        # Uniqueness ratio (high unique = likely text or IDs)
        unique_ratio = str_series.nunique() / len(str_series)
        indicators['unique_ratio'] = unique_ratio
        
        # Count values with special chars that suggest prose/text
        text_pattern = r'[a-z]{3,}|[A-Z][a-z]{2,}'  # Words with 3+ chars
        has_words = str_series.str.contains(text_pattern, regex=True, na=False).sum()
        word_ratio = has_words / len(str_series)
        
        # Text is dominant if: avg length > 15, word ratio > 0.4
        indicators['is_text_dominant'] = (avg_length > 15 and word_ratio > 0.4) or word_ratio > 0.6
        
    except Exception:
        pass
    
    return indicators


def _apply_text_search(df: pd.DataFrame, value: str) -> pd.DataFrame:
    """Global text search across all columns"""
    value = str(value).lower().strip()
    if not value:
        return df

    mask = pd.Series(False, index=df.index)

    for col in df.columns:
        try:
            s = df[col].astype(str).str.lower()
            mask |= s.str.contains(value, na=False, regex=False)
        except Exception:
            continue

    return df[mask]


def _apply_date_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Apply date range filter without converting to numeric"""
    try:
        start_dt = pd.to_datetime(start, errors="coerce")
        end_dt = pd.to_datetime(end, errors="coerce")

        if pd.isna(start_dt) or pd.isna(end_dt):
            return df

        # Find datetime columns and apply filter to the first valid one
        for col in df.columns:
            try:
                s = pd.to_datetime(df[col], errors="coerce")
                valid_count = s.notna().sum()
                
                if valid_count > len(s) * 0.6:
                    return df[(s >= start_dt) & (s <= end_dt)].copy()
            except Exception:
                continue

        return df
    except Exception:
        return df


def _apply_numeric_range(df: pd.DataFrame, min_v: Any, max_v: Any) -> pd.DataFrame:
    """Apply numeric range filter"""
    try:
        min_v = pd.to_numeric(min_v, errors="coerce")
        max_v = pd.to_numeric(max_v, errors="coerce")

        if pd.isna(min_v) or pd.isna(max_v):
            return df

        for col in df.columns:
            try:
                s = pd.to_numeric(df[col], errors="coerce")
                if s.notna().sum() > len(s) * 0.6:
                    return df[(s >= min_v) & (s <= max_v)].copy()
            except Exception:
                continue

        return df
    except Exception:
        return df


def _apply_statistical_filter(
    series: pd.Series,
    operator: str,
    value: Optional[float] = None,
    std_dev_multiplier: float = 1.0
) -> pd.Series:
    """
    Apply statistical filter (mean, median, mode, std deviation)
    Returns boolean mask for rows to keep
    """
    try:
        numeric_series = pd.to_numeric(series, errors="coerce")
        
        if operator == "gt_mean":
            threshold = numeric_series.mean()
            return numeric_series > threshold
        
        elif operator == "lt_mean":
            threshold = numeric_series.mean()
            return numeric_series < threshold
        
        elif operator == "gt_median":
            threshold = numeric_series.median()
            return numeric_series > threshold
        
        elif operator == "lt_median":
            threshold = numeric_series.median()
            return numeric_series < threshold
        
        elif operator == "within_std":
            # Keep values within N standard deviations of mean
            mean = numeric_series.mean()
            std = numeric_series.std()
            lower = mean - (std_dev_multiplier * std)
            upper = mean + (std_dev_multiplier * std)
            return (numeric_series >= lower) & (numeric_series <= upper)
        
        elif operator == "outliers":
            # Identify outliers (outside Nth std dev)
            mean = numeric_series.mean()
            std = numeric_series.std()
            lower = mean - (std_dev_multiplier * std)
            upper = mean + (std_dev_multiplier * std)
            return (numeric_series < lower) | (numeric_series > upper)
        
        elif operator == "iqr":
            # Interquartile range outlier detection
            Q1 = numeric_series.quantile(0.25)
            Q3 = numeric_series.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - (1.5 * IQR)
            upper = Q3 + (1.5 * IQR)
            return (numeric_series >= lower) & (numeric_series <= upper)
        
        else:
            return pd.Series(True, index=series.index)
    
    except Exception:
        return pd.Series(True, index=series.index)


def _apply_single_filter(
    filtered_df: pd.DataFrame,
    column: str,
    rule: Dict[str, Any]
) -> pd.DataFrame:
    """Apply a single filter rule to a column"""
    
    try:
        series = filtered_df[column]
        col_type = _detect_column_type(series)
        op = rule.get("op")
        
        # NUMERIC FILTERS
        if col_type == "numeric":
            s = pd.to_numeric(series, errors="coerce")
            
            if op == ">":
                v = pd.to_numeric(rule.get("value"), errors="coerce")
                if not pd.isna(v):
                    filtered_df = filtered_df[s > v]
            
            elif op == ">=":
                v = pd.to_numeric(rule.get("value"), errors="coerce")
                if not pd.isna(v):
                    filtered_df = filtered_df[s >= v]
            
            elif op == "<":
                v = pd.to_numeric(rule.get("value"), errors="coerce")
                if not pd.isna(v):
                    filtered_df = filtered_df[s < v]
            
            elif op == "<=":
                v = pd.to_numeric(rule.get("value"), errors="coerce")
                if not pd.isna(v):
                    filtered_df = filtered_df[s <= v]
            
            elif op in {"equals", "=="}:
                v = pd.to_numeric(rule.get("value"), errors="coerce")
                if not pd.isna(v):
                    filtered_df = filtered_df[s == v]
            
            elif op == "between":
                min_v = pd.to_numeric(rule.get("min"), errors="coerce")
                max_v = pd.to_numeric(rule.get("max"), errors="coerce")
                if not pd.isna(min_v) and not pd.isna(max_v):
                    filtered_df = filtered_df[(s >= min_v) & (s <= max_v)]
            
            # Statistical filters
            elif op in {"gt_mean", "lt_mean", "gt_median", "lt_median", 
                       "within_std", "outliers", "iqr"}:
                std_mult = rule.get("std_multiplier", 1.0)
                mask = _apply_statistical_filter(s, op, std_dev_multiplier=std_mult)
                filtered_df = filtered_df[mask]
        
        # DATETIME FILTERS
        elif col_type == "datetime":
            s = pd.to_datetime(series, errors="coerce")
            
            if op in {"range", "between"}:
                start = pd.to_datetime(rule.get("start"), errors="coerce")
                end = pd.to_datetime(rule.get("end"), errors="coerce")
                if not pd.isna(start) and not pd.isna(end):
                    filtered_df = filtered_df[(s >= start) & (s <= end)]
            
            elif op in {"equals", "=="}:
                v = pd.to_datetime(rule.get("value"), errors="coerce")
                if not pd.isna(v):
                    filtered_df = filtered_df[s == v]
        
        # BOOLEAN FILTERS
        elif col_type == "boolean":
            v = rule.get("value")
            if isinstance(v, str):
                v = v.lower() in {"true", "1", "yes"}
            filtered_df = filtered_df[series == v]
        
        # TEXT FILTERS
        else:
            s = series.astype(str).str.strip()
            
            if op in {"equals", "=="}:
                filtered_df = filtered_df[
                    s.str.lower() == str(rule.get("value")).lower()
                ]
            
            elif op == "contains":
                filtered_df = filtered_df[
                    s.str.contains(str(rule.get("value")), case=False, na=False, regex=False)
                ]
            
            elif op == "starts_with":
                filtered_df = filtered_df[
                    s.str.startswith(str(rule.get("value")), na=False)
                ]
            
            elif op == "ends_with":
                filtered_df = filtered_df[
                    s.str.endswith(str(rule.get("value")), na=False)
                ]
            
            elif op == "in":
                values = [str(v).lower().strip() for v in rule.get("value", [])]
                filtered_df = filtered_df[s.str.lower().isin(values)]
            
            elif op == "regex":
                pattern = rule.get("value", "")
                filtered_df = filtered_df[
                    s.str.contains(pattern, case=False, na=False, regex=True)
                ]
    
    except Exception as e:
        # Log but don't fail - try to continue with other filters
        print(f"[FILTER ERROR] Column '{column}' filter failed: {str(e)}")
    
    return filtered_df


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply filters to dataframe with support for multi-filters per column
    Filters can be single rules or arrays of rules (OR logic for arrays, AND between columns)
    """
    if df is None or df.empty or not filters:
        return df

    filtered_df = df.copy()

    # ---------- GLOBAL / META FILTERS ----------
    if "_textSearch" in filters:
        rule = filters.get("_textSearch", {})
        if rule.get("op") == "contains":
            filtered_df = _apply_text_search(
                filtered_df, rule.get("value")
            )

    if "_dateRange" in filters:
        rule = filters.get("_dateRange", {})
        if rule.get("op") in {"range", "between"}:
            filtered_df = _apply_date_range(
                filtered_df, rule.get("start"), rule.get("end")
            )

    if "_numericRange" in filters:
        rule = filters.get("_numericRange", {})
        if rule.get("op") == "between":
            filtered_df = _apply_numeric_range(
                filtered_df, rule.get("min"), rule.get("max")
            )

    # ---------- COLUMN-SPECIFIC FILTERS ----------
    for key, rule in filters.items():
        if key.startswith("_"):
            continue

        if not isinstance(rule, (dict, list)):
            continue

        column = _resolve_column(filtered_df, key)
        if not column:
            continue

        # Handle multiple filters on same column (array)
        if isinstance(rule, list):
            # Multiple filters: combine with OR logic (union of results)
            column_results = []
            for single_rule in rule:
                if isinstance(single_rule, dict):
                    # Apply filter and get matching indices
                    temp_df = _apply_single_filter(filtered_df.copy(), column, single_rule)
                    column_results.append(set(temp_df.index))
            
            # Union all results (OR logic)
            if column_results:
                combined_indices = column_results[0]
                for result_set in column_results[1:]:
                    combined_indices = combined_indices.union(result_set)
                filtered_df = filtered_df.loc[list(combined_indices)]
        
        # Single filter rule (dict)
        elif isinstance(rule, dict):
            filtered_df = _apply_single_filter(filtered_df, column, rule)

    return filtered_df.reset_index(drop=True)


def filter_by_date_range(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """Utility: Filter by date range"""
    if df is None or df.empty:
        return df

    return _apply_date_range(df, start_date, end_date)
