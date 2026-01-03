# Filters & parameters
import pandas as pd
from typing import Dict, Any


def _resolve_column(df: pd.DataFrame, key: str) -> str | None:
    """Resolve column name dynamically"""
    key = key.lower()

    for col in df.columns:
        col_l = col.lower()
        if key == col_l or key in col_l or col_l in key:
            return col

    return None


def _detect_column_type(series: pd.Series) -> str:
    """
    Detect column type dynamically
    """
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # Try datetime
    try:
        parsed = pd.to_datetime(series, errors="coerce")
        if parsed.notna().sum() > len(series) * 0.6:
            return "datetime"
    except Exception:
        pass

    return "text"


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply fully dynamic filters:
    - column name resolved dynamically
    - column type detected at runtime
    - filter logic adapts automatically
    """
    if df is None or df.empty or not filters:
        return df

    filtered_df = df.copy()

    for key, rule in filters.items():
        if not isinstance(rule, dict):
            continue

        column = _resolve_column(filtered_df, key)
        if not column:
            continue

        try:
            series = filtered_df[column]
            col_type = _detect_column_type(series)
            op = rule.get("op")

            # ---------- NUMERIC ----------
            if col_type == "numeric":
                s = pd.to_numeric(series, errors="coerce")

                if op in [">", ">=", "<", "<="]:
                    v = pd.to_numeric(rule.get("value"), errors="coerce")
                    filtered_df = filtered_df[
                        eval(f"s {op} v")
                    ]

                elif op == "between":
                    min_v = pd.to_numeric(rule.get("min"), errors="coerce")
                    max_v = pd.to_numeric(rule.get("max"), errors="coerce")
                    filtered_df = filtered_df[(s >= min_v) & (s <= max_v)]

                elif op in ["equals", "=="]:
                    v = pd.to_numeric(rule.get("value"), errors="coerce")
                    filtered_df = filtered_df[s == v]

            # ---------- DATETIME ----------
            elif col_type == "datetime":
                s = pd.to_datetime(series, errors="coerce")

                if op in ["range", "between"]:
                    start = pd.to_datetime(rule.get("start"), errors="coerce")
                    end = pd.to_datetime(rule.get("end"), errors="coerce")
                    filtered_df = filtered_df[(s >= start) & (s <= end)]

                elif op in ["equals", "=="]:
                    v = pd.to_datetime(rule.get("value"), errors="coerce")
                    filtered_df = filtered_df[s == v]

            # ---------- BOOLEAN ----------
            elif col_type == "boolean":
                v = bool(rule.get("value"))
                filtered_df = filtered_df[series == v]

            # ---------- TEXT / MIXED ----------
            else:
                s = series.astype(str)

                if op in ["equals", "=="]:
                    filtered_df = filtered_df[s == str(rule.get("value"))]

                elif op == "contains":
                    filtered_df = filtered_df[
                        s.str.contains(str(rule.get("value")), case=False, na=False)
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
                    values = [str(v) for v in rule.get("value", [])]
                    filtered_df = filtered_df[s.isin(values)]

        except Exception:
            # One bad column/filter never kills the batch
            continue

    return filtered_df


def filter_by_date_range(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Generic date range filter (auto-detects datetime column)
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    for col in df.columns:
        try:
            s = pd.to_datetime(df[col], errors="coerce")
            if s.notna().sum() > len(s) * 0.6:
                start = pd.to_datetime(start_date, errors="coerce")
                end = pd.to_datetime(end_date, errors="coerce")
                return df[(s >= start) & (s <= end)]
        except Exception:
            continue

    return df
