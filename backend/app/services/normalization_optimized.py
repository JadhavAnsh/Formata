"""
Optimized normalization with intelligent sampling and hybrid rule-based + ML approach.
Production-grade for large files (10MB+).

Key optimizations:
1. File size aware sampling (large files use 10k sample for expensive ops)
2. Rule-based type detection first (fast), RF only for ambiguous
3. Vectorized operations instead of row-by-row processing
4. Early error value detection (skip "errXXX", "???", etc.)
5. Sub-progress tracking
"""

import pandas as pd
import numpy as np
import re
import warnings
from typing import Dict, Any, Optional, Callable, Tuple
from sklearn.ensemble import RandomForestClassifier

from app.utils.logger import logger

# ============================================================================
# CONSTANTS
# ============================================================================

MISSING_TOKENS = {
    "", " ", "null", "none", "nan", "na", "n/a", "n.a.",
    "undefined", "unknown", "not_provided", "not provided",
    "missing", "-", "--", "?", "??", "???",
}

ERROR_PATTERNS = [
    re.compile(r"^err\d+$", re.IGNORECASE),  # err123, ERR456
    re.compile(r"^\?+$"),  # ???, ?, etc.
    re.compile(r"^n\.a\.?$", re.IGNORECASE),
]

NUMERIC_HINTS = {
    "age", "amount", "balance", "count", "cost", "income",
    "number", "price", "qty", "quantity", "revenue",
    "salary", "score", "total", "value", "duration",
}

DATE_HINTS = {
    "birth", "created", "date", "dob", "joined", "join",
    "timestamp", "time", "updated", "modified", "start", "end",
}

EMAIL_HINTS = {"email", "mail", "contact"}
BOOL_HINTS = {"active", "bool", "enabled", "flag", "has_", "is_", "valid"}

# Compiled patterns for fast matching
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NUMERIC_PATTERN = re.compile(r"-?\d+(?:[,.]\d+)?")
BOOL_PATTERN = re.compile(r"^(true|false|yes|no|t|f|y|n|1|0)$", re.IGNORECASE)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _is_error_value(value: Any) -> bool:
    """Check if value looks like a data error (errXXX, ???, etc.)"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    text = str(value).strip()
    return any(pattern.match(text) for pattern in ERROR_PATTERNS)


def _is_missing_value(value: Any) -> bool:
    """Check if value represents missing data"""
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    text = str(value).strip()
    return text.lower() in MISSING_TOKENS


def _normalize_missing_value(value: Any) -> Optional[str]:
    """Normalize missing/error values to None"""
    if _is_error_value(value) or _is_missing_value(value):
        return None
    text = str(value).strip()
    return text if text else None


def _column_role_heuristic(column_name: str) -> str:
    """Fast keyword-based column role detection"""
    lowered = str(column_name).lower()
    if any(hint in lowered for hint in EMAIL_HINTS):
        return "email"
    if any(hint in lowered for hint in DATE_HINTS):
        return "datetime"
    if any(hint in lowered for hint in BOOL_HINTS):
        return "boolean"
    if any(hint in lowered for hint in NUMERIC_HINTS):
        return "numeric"
    return "text"


def _get_file_size_mb(series: pd.Series) -> float:
    """Estimate series memory size in MB"""
    return series.memory_usage(deep=True) / (1024 ** 2)


# ============================================================================
# VECTORIZED TYPE DETECTION (Fast Path)
# ============================================================================


def _fast_detect_type(series: pd.Series, column_name: str, role_hint: str) -> Tuple[str, float]:
    """
    Fast vectorized type detection. Returns (type, confidence).
    Confidence < 0.7 means rule-based detection was uncertain.
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return ("text", 0.5)

    non_error = non_null[~non_null.apply(_is_error_value)]
    if len(non_error) == 0:
        return ("text", 0.3)

    text_series = non_error.astype(str).str.strip()
    total = len(text_series)

    # ---- BOOLEAN (fastest, high-confidence) ----
    bool_matches = text_series.str.lower().isin(
        ["true", "false", "yes", "no", "t", "f", "y", "n", "1", "0"]
    ).sum()
    if bool_matches / total > 0.9:
        return ("boolean", 0.95)
    if role_hint == "boolean" and bool_matches / total > 0.5:
        return ("boolean", 0.75)

    # ---- NUMERIC (vectorized) ----
    try:
        numeric = pd.to_numeric(text_series, errors="coerce")
        numeric_ratio = numeric.notna().sum() / total
        if numeric_ratio > 0.95:
            # Check if int or float
            is_int = (numeric.dropna() == numeric.dropna().astype(int)).all()
            type_ = "int" if is_int else "float"
            return (type_, 0.95)
        if numeric_ratio > 0.7:
            return ("float", 0.8)
        if role_hint == "numeric" and numeric_ratio > 0.5:
            return ("float", 0.7)
    except Exception:
        pass

    # ---- DATETIME (vectorized, try common formats only) ----
    try:
        # Try ISO format first (most common in modern systems)
        parsed = pd.to_datetime(text_series, errors="coerce", format="%Y-%m-%d %H:%M:%S.%f")
        datetime_ratio = parsed.notna().sum() / total
        if datetime_ratio > 0.9:
            return ("datetime", 0.95)
        if datetime_ratio > 0.7:
            return ("datetime", 0.85)
        
        # Try other common formats
        if datetime_ratio < 0.5:
            parsed = pd.to_datetime(text_series, errors="coerce", format="%Y-%m-%d")
            datetime_ratio = parsed.notna().sum() / total
            if datetime_ratio > 0.9:
                return ("datetime", 0.95)
            if datetime_ratio > 0.7:
                return ("datetime", 0.85)
        
        if role_hint == "datetime" and datetime_ratio > 0.5:
            return ("datetime", 0.7)
    except Exception:
        pass

    # ---- EMAIL (regex vectorized) ----
    email_matches = text_series.str.match(EMAIL_PATTERN).sum()
    if email_matches / total > 0.8:
        return ("email", 0.9)

    # ---- TEXT (default) ----
    return ("text", 0.5)


# ============================================================================
# HYBRID DETECTION: Rule-Based + RandomForest
# ============================================================================


def _hybrid_type_detection(
    df: pd.DataFrame,
    sample_size: Optional[int] = None,
    progress_callback: Optional[Callable[[float], None]] = None
) -> Dict[str, Tuple[str, float]]:
    """
    Hybrid type detection: use fast rules first, RF only for ambiguous columns.
    
    For large files (10MB+), sample 5k-10k rows for expensive operations.
    
    Returns:
        Dict[column_name] = (type, confidence)
    """
    if df is None or df.empty:
        return {}

    # Auto-determine sample size based on dataframe memory
    if sample_size is None:
        df_size_mb = sum(df[col].memory_usage(deep=True) for col in df.columns) / (1024 ** 2)
        if df_size_mb > 50:  # Very large file
            sample_size = 5000
        elif df_size_mb > 10:  # Large file
            sample_size = 10000
        else:
            sample_size = None  # Use full dataset

    use_sample = sample_size and len(df) > sample_size
    work_df = df.sample(n=sample_size, random_state=42) if use_sample else df
    
    logger.info(
        f"Hybrid type detection: using {'sample of' if use_sample else 'full'} "
        f"{len(work_df):,} rows from {len(df):,} for expensive RF operations"
    )

    type_results = {}
    ambiguous_columns = []
    
    # Phase 1: Fast rule-based detection
    for col in df.columns:
        role = _column_role_heuristic(col)
        series = df[col]  # Use full dataset for rule-based (vectorized, fast)
        
        detected_type, confidence = _fast_detect_type(series, col, role)
        type_results[col] = (detected_type, confidence)
        
        if confidence < 0.7:
            ambiguous_columns.append(col)
        
        if progress_callback:
            progress_callback(0.05)  # Each column is ~5% of detection

    # Phase 2: RandomForest for ambiguous columns only
    if ambiguous_columns:
        logger.info(f"Running RF on {len(ambiguous_columns)} ambiguous columns")
        rf_types = _random_forest_detection(work_df[ambiguous_columns])
        
        for col, (rf_type, rf_conf) in rf_types.items():
            # Blend rule-based and RF: if RF is high-confidence, use it
            if rf_conf > 0.75:
                type_results[col] = (rf_type, rf_conf)
        
        if progress_callback:
            progress_callback(0.1)

    return type_results


def _random_forest_detection(df_sample: pd.DataFrame) -> Dict[str, Tuple[str, float]]:
    """
    Random Forest semantic type detection on sample.
    Fast because it runs on sampled data only.
    """
    try:
        from app.services.normalizer import _column_features, _synthetic_training_set
        
        x_train, y_train = _synthetic_training_set()
        clf = RandomForestClassifier(
            n_estimators=100,  # Reduced from 300 for speed
            random_state=42,
            class_weight="balanced_subsample",
            max_depth=10,  # Reduced from 14
            n_jobs=-1,  # Parallel processing
        )
        clf.fit(x_train, y_train)

        results = {}
        for col in df_sample.columns:
            try:
                features = _column_features(col, df_sample[col])
                probs = clf.predict_proba([features])[0]
                classes = clf.classes_.tolist()
                
                ranked = sorted(zip(classes, probs), key=lambda item: item[1], reverse=True)
                predicted, confidence = ranked[0][0], float(ranked[0][1])
                
                # Map semantic labels to base types
                semantic_to_base = {
                    "Email": "email",
                    "DateTime": "datetime",
                    "Boolean": "boolean",
                    "Numeric": "float",
                    "Integer": "int",
                }
                base_type = semantic_to_base.get(predicted, "text")
                results[col] = (base_type, confidence)
            except Exception as e:
                logger.warning(f"RF detection failed for {col}: {e}")
                results[col] = ("text", 0.5)
        
        return results
    
    except Exception as e:
        logger.warning(f"RandomForest detection failed: {e}")
        return {}


# ============================================================================
# OPTIMIZED COERCION FUNCTIONS
# ============================================================================


def _coerce_to_type(series: pd.Series, target_type: str) -> pd.Series:
    """Vectorized type coercion"""
    # Normalize errors and missing values
    cleaned = series.apply(_normalize_missing_value)

    if target_type == "boolean":
        str_series = cleaned.astype(str).str.lower().str.strip()
        bool_map = {
            "true": True, "t": True, "yes": True, "y": True, "1": True,
            "false": False, "f": False, "no": False, "n": False, "0": False,
        }
        return str_series.map(bool_map)

    elif target_type in ("int", "float"):
        numeric_series = pd.to_numeric(cleaned, errors="coerce")
        if target_type == "int":
            return numeric_series.astype("Int64")
        return numeric_series

    elif target_type == "datetime":
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Could not infer format")
            return pd.to_datetime(cleaned, errors="coerce")

    elif target_type == "email":
        return cleaned

    else:  # "text"
        return cleaned.astype(str).replace("nan", None)


# ============================================================================
# MAIN OPTIMIZED NORMALIZATION
# ============================================================================


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Fast column name standardization (vectorized)"""
    if df is None or df.empty:
        return df

    df = df.copy()
    new_columns = []
    seen = {}

    for col in df.columns:
        clean = str(col).strip().lower()
        clean = re.sub(r"[^\w]+", "_", clean)
        clean = re.sub(r"_+", "_", clean).strip("_")

        if not clean:
            clean = "column"

        if clean in seen:
            seen[clean] += 1
            clean = f"{clean}_{seen[clean]}"
        else:
            seen[clean] = 0

        new_columns.append(clean)

    df.columns = new_columns
    return df


def normalize_types_optimized(
    df: pd.DataFrame,
    progress_callback: Optional[Callable[[float], None]] = None
) -> pd.DataFrame:
    """
    Production-grade optimized type normalization.
    
    Uses hybrid rule-based + RandomForest for ambiguous columns.
    Samples large files for expensive operations.
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    
    # Phase 1: Run hybrid type detection
    if progress_callback:
        progress_callback(0.0)
    
    type_map = _hybrid_type_detection(df, progress_callback=progress_callback)
    
    if progress_callback:
        progress_callback(0.15)

    # Phase 2: Apply coercions
    for col, (target_type, confidence) in type_map.items():
        try:
            if target_type != "text":  # Skip text coercion (expensive for large series)
                df[col] = _coerce_to_type(df[col], target_type)
                logger.debug(
                    f"Coerced {col} to {target_type} (confidence: {confidence:.2f})"
                )
        except Exception as e:
            logger.warning(f"Coercion failed for {col} to {target_type}: {e}")

    if progress_callback:
        progress_callback(0.25)

    return df


# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    """Backwards compatible wrapper"""
    return normalize_types_optimized(df)
