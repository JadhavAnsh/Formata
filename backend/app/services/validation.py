# Schema validation
from typing import Dict, Any, List
import pandas as pd


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
