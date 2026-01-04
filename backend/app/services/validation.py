# Schema validation
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def _check_type(value: Any, expected_type: str) -> bool:
    """Internal type checker"""
    if value is None:
        return True  # null handling is done via 'required'

    try:
        if expected_type == "string":
            return isinstance(value, str)

        if expected_type == "number":
            float(value)
            return True

        if expected_type == "boolean":
            return isinstance(value, bool)

        if expected_type == "datetime":
            pd.to_datetime(value)
            return True

    except Exception:
        return False

    return True


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a schema
    """
    if not data or not schema:
        return True

    records = data.get("records", [])
    if not isinstance(records, list):
        return False

    for row in records:
        for field, rules in schema.items():
            value = row.get(field)

            # Required field check
            if rules.get("required") and value is None:
                return False

            # Type check
            expected_type = rules.get("type")
            if expected_type and not _check_type(value, expected_type):
                return False

            # Numeric constraints
            if expected_type == "number" and value is not None:
                if "min" in rules and float(value) < rules["min"]:
                    return False
                if "max" in rules and float(value) > rules["max"]:
                    return False

    return True


def get_validation_errors(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Get list of validation errors
    """
    errors: List[str] = []

    if not data or not schema:
        return errors

    records = data.get("records", [])
    if not isinstance(records, list):
        return ["Invalid data format: expected records list"]

    for idx, row in enumerate(records):
        for field, rules in schema.items():
            value = row.get(field)

            # Required field
            if rules.get("required") and value is None:
                errors.append(f"Row {idx}: Missing required field '{field}'")
                continue

            expected_type = rules.get("type")
            if expected_type and not _check_type(value, expected_type):
                errors.append(
                    f"Row {idx}: Field '{field}' expected {expected_type}, got {type(value).__name__}"
                )
                continue

            # Numeric rules
            if expected_type == "number" and value is not None:
                try:
                    val = float(value)
                    if "min" in rules and val < rules["min"]:
                        errors.append(
                            f"Row {idx}: Field '{field}' below min {rules['min']}"
                        )
                    if "max" in rules and val > rules["max"]:
                        errors.append(
                            f"Row {idx}: Field '{field}' above max {rules['max']}"
                        )
                except Exception:
                    errors.append(
                        f"Row {idx}: Field '{field}' not numeric"
                    )

    return errors


def calculate_data_quality_score(
    df: pd.DataFrame,
    schema: Dict[str, Any] = None,
    missing_data_report: Dict[str, Any] = None,
    type_enforcement_report: Dict[str, Any] = None,
    validation_errors: List[str] = None
) -> Dict[str, Any]:
    """
    Calculate a comprehensive multifactor data quality score (0-100)
    
    Args:
        df: The processed DataFrame
        schema: Optional schema for validation
        missing_data_report: Report from missing data handling
        type_enforcement_report: Report from type enforcement
        validation_errors: List of validation errors
    
    Returns:
        Dictionary containing individual scores and overall quality score
    """
    if df is None or df.empty:
        return {
            "overall_score": 0.0,
            "completeness_score": 0.0,
            "validity_score": 0.0,
            "consistency_score": 0.0,
            "accuracy_score": 0.0,
            "grade": "F",
            "factors": {}
        }
    
    # 1. COMPLETENESS SCORE (0-100): Based on missing data
    completeness_score = _calculate_completeness_score(df, missing_data_report)
    
    # 2. VALIDITY SCORE (0-100): Based on type correctness and schema compliance
    validity_score = _calculate_validity_score(
        df, schema, type_enforcement_report, validation_errors
    )
    
    # 3. CONSISTENCY SCORE (0-100): Based on data uniformity and patterns
    consistency_score = _calculate_consistency_score(df)
    
    # 4. ACCURACY SCORE (0-100): Based on outliers and duplicates
    accuracy_score = _calculate_accuracy_score(df)
    
    # Calculate weighted overall score
    # Weights: Completeness (30%), Validity (30%), Consistency (20%), Accuracy (20%)
    overall_score = (
        completeness_score * 0.30 +
        validity_score * 0.30 +
        consistency_score * 0.20 +
        accuracy_score * 0.20
    )
    
    # Assign grade
    grade = _assign_quality_grade(overall_score)
    
    return {
        "overall_score": round(overall_score, 2),
        "completeness_score": round(completeness_score, 2),
        "validity_score": round(validity_score, 2),
        "consistency_score": round(consistency_score, 2),
        "accuracy_score": round(accuracy_score, 2),
        "grade": grade,
        "factors": {
            "completeness": {
                "score": round(completeness_score, 2),
                "weight": 30,
                "description": "Measures data completeness and missing values"
            },
            "validity": {
                "score": round(validity_score, 2),
                "weight": 30,
                "description": "Measures type correctness and schema compliance"
            },
            "consistency": {
                "score": round(consistency_score, 2),
                "weight": 20,
                "description": "Measures data uniformity and format patterns"
            },
            "accuracy": {
                "score": round(accuracy_score, 2),
                "weight": 20,
                "description": "Measures data correctness and outlier presence"
            }
        }
    }


def _calculate_completeness_score(
    df: pd.DataFrame,
    missing_data_report: Dict[str, Any] = None
) -> float:
    """
    Calculate completeness score based on missing data
    100 = no missing values, 0 = all values missing
    """
    total_cells = len(df) * len(df.columns)
    if total_cells == 0:
        return 100.0
    
    missing_count = int(df.isnull().sum().sum())
    completeness_ratio = 1 - (missing_count / total_cells)
    
    # Apply exponential scaling to penalize high missing rates more severely
    score = completeness_ratio * 100
    
    # Additional penalty for columns with very high missing rates
    if missing_data_report and 'columns' in missing_data_report:
        high_missing_cols = sum(
            1 for col_data in missing_data_report['columns'].values()
            if col_data.get('missing_percentage', 0) > 50
        )
        if high_missing_cols > 0:
            penalty = min(20, high_missing_cols * 5)
            score = max(0, score - penalty)
    
    return max(0.0, min(100.0, score))


def _calculate_validity_score(
    df: pd.DataFrame,
    schema: Dict[str, Any] = None,
    type_enforcement_report: Dict[str, Any] = None,
    validation_errors: List[str] = None
) -> float:
    """
    Calculate validity score based on type correctness and schema compliance
    100 = all data valid, 0 = all data invalid
    """
    score = 100.0
    
    # Penalty for type enforcement errors
    if type_enforcement_report:
        errors = type_enforcement_report.get('errors', [])
        if errors:
            # Deduct 5 points per type error (max 40 points)
            penalty = min(40, len(errors) * 5)
            score -= penalty
    
    # Penalty for validation errors
    if validation_errors:
        # Deduct based on error count relative to data size
        total_records = len(df)
        error_ratio = len(validation_errors) / max(total_records, 1)
        penalty = min(40, error_ratio * 100)
        score -= penalty
    
    # Bonus for schema compliance (if schema provided)
    if schema:
        is_valid = validate_schema({"records": df.to_dict(orient='records')}, schema)
        if is_valid:
            score = min(100, score + 10)
    
    return max(0.0, min(100.0, score))


def _calculate_consistency_score(df: pd.DataFrame) -> float:
    """
    Calculate consistency score based on data uniformity and patterns
    100 = highly consistent, 0 = highly inconsistent
    """
    if len(df) == 0:
        return 100.0
    
    score = 100.0
    column_scores = []
    
    for col in df.columns:
        col_score = 100.0
        non_null_values = df[col].dropna()
        
        if len(non_null_values) == 0:
            continue
        
        # Check data type consistency
        if df[col].dtype == 'object':
            # For string columns, check format consistency
            str_values = non_null_values.astype(str)
            
            # Check for mixed case patterns
            has_upper = str_values.str.isupper().any()
            has_lower = str_values.str.islower().any()
            has_mixed = (~str_values.str.isupper() & ~str_values.str.islower()).any()
            
            if sum([has_upper, has_lower, has_mixed]) > 1:
                col_score -= 15
            
            # Check for leading/trailing whitespace inconsistency
            has_whitespace = (str_values != str_values.str.strip()).any()
            if has_whitespace:
                col_score -= 10
        
        # Check for data range consistency (coefficient of variation)
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_values = pd.to_numeric(non_null_values, errors='coerce').dropna()
            if len(numeric_values) > 1:
                mean_val = numeric_values.mean()
                if mean_val != 0:
                    cv = numeric_values.std() / abs(mean_val)
                    # High coefficient of variation suggests inconsistency
                    if cv > 2:
                        col_score -= 20
                    elif cv > 1:
                        col_score -= 10
        
        column_scores.append(max(0, col_score))
    
    # Average across all columns
    if column_scores:
        score = sum(column_scores) / len(column_scores)
    
    return max(0.0, min(100.0, score))


def _calculate_accuracy_score(df: pd.DataFrame) -> float:
    """
    Calculate accuracy score based on outliers and duplicate presence
    100 = no outliers/duplicates, 0 = many outliers/duplicates
    """
    if len(df) == 0:
        return 100.0
    
    score = 100.0
    
    # Check for duplicates
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        duplicate_ratio = duplicate_count / len(df)
        penalty = min(30, duplicate_ratio * 100)
        score -= penalty
    
    # Check for outliers in numeric columns using IQR method
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    outlier_ratio_total = 0
    numeric_col_count = 0
    
    for col in numeric_cols:
        non_null = df[col].dropna()
        if len(non_null) < 4:
            continue
        
        Q1 = non_null.quantile(0.25)
        Q3 = non_null.quantile(0.75)
        IQR = Q3 - Q1
        
        if IQR > 0:
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = ((non_null < lower_bound) | (non_null > upper_bound)).sum()
            outlier_ratio = outliers / len(non_null)
            outlier_ratio_total += outlier_ratio
            numeric_col_count += 1
    
    if numeric_col_count > 0:
        avg_outlier_ratio = outlier_ratio_total / numeric_col_count
        penalty = min(30, avg_outlier_ratio * 100)
        score -= penalty
    
    return max(0.0, min(100.0, score))


def _assign_quality_grade(score: float) -> str:
    """
    Assign a letter grade based on quality score
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
