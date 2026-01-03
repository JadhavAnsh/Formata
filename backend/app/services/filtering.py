# Filters & parameters

import pandas as pd
from typing import Dict, Any


def _resolve_column(df: pd.DataFrame, key: str) -> str | None:
    key = key.lower().strip()

    for col in df.columns:
        col_l = col.lower()
        if key == col_l or key in col_l or col_l in key:
            return col

    return None


def _detect_column_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    try:
        parsed = pd.to_datetime(series, errors="coerce")
        if parsed.notna().sum() > len(series) * 0.6:
            return "datetime"
    except Exception:
        pass

    return "text"


def _apply_text_search(df: pd.DataFrame, value: str) -> pd.DataFrame:
    value = str(value).lower().strip()
    if not value:
        return df

    mask = pd.Series(False, index=df.index)

    for col in df.columns:
        try:
            s = df[col].astype(str).str.lower()
            mask |= s.str.contains(value, na=False)
        except Exception:
            continue

    return df[mask]


def _apply_date_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_dt = pd.to_datetime(start, errors="coerce")
    end_dt = pd.to_datetime(end, errors="coerce")

    if pd.isna(start_dt) or pd.isna(end_dt):
        return df

    for col in df.columns:
        try:
            s = pd.to_datetime(df[col], errors="coerce")
            if s.notna().sum() > len(s) * 0.6:
                return df[(s >= start_dt) & (s <= end_dt)]
        except Exception:
            continue

    return df


def _apply_numeric_range(df: pd.DataFrame, min_v: Any, max_v: Any) -> pd.DataFrame:
    min_v = pd.to_numeric(min_v, errors="coerce")
    max_v = pd.to_numeric(max_v, errors="coerce")

    if pd.isna(min_v) or pd.isna(max_v):
        return df

    for col in df.columns:
        try:
            s = pd.to_numeric(df[col], errors="coerce")
            if s.notna().sum() > len(s) * 0.6:
                return df[(s >= min_v) & (s <= max_v)]
        except Exception:
            continue

    return df


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
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

        if not isinstance(rule, dict):
            continue

        column = _resolve_column(filtered_df, key)
        if not column:
            continue

        try:
            series = filtered_df[column]
            col_type = _detect_column_type(series)
            op = rule.get("op")

            # NUMERIC
            if col_type == "numeric":
                s = pd.to_numeric(series, errors="coerce")

                if op in {">", ">=", "<", "<="}:
                    v = pd.to_numeric(rule.get("value"), errors="coerce")
                    if not pd.isna(v):
                        filtered_df = filtered_df[eval(f"s {op} v")]

                elif op in {"equals", "=="}:
                    v = pd.to_numeric(rule.get("value"), errors="coerce")
                    filtered_df = filtered_df[s == v]

                elif op == "between":
                    min_v = pd.to_numeric(rule.get("min"), errors="coerce")
                    max_v = pd.to_numeric(rule.get("max"), errors="coerce")
                    filtered_df = filtered_df[(s >= min_v) & (s <= max_v)]

            # DATETIME
            elif col_type == "datetime":
                s = pd.to_datetime(series, errors="coerce")

                if op in {"range", "between"}:
                    start = pd.to_datetime(rule.get("start"), errors="coerce")
                    end = pd.to_datetime(rule.get("end"), errors="coerce")
                    filtered_df = filtered_df[(s >= start) & (s <= end)]

                elif op in {"equals", "=="}:
                    v = pd.to_datetime(rule.get("value"), errors="coerce")
                    filtered_df = filtered_df[s == v]

            # BOOLEAN
            elif col_type == "boolean":
                v = bool(rule.get("value"))
                filtered_df = filtered_df[series == v]

            # TEXT
            else:
                s = series.astype(str).str.strip()

                if op in {"equals", "=="}:
                    filtered_df = filtered_df[
                        s.str.lower() == str(rule.get("value")).lower()
                    ]

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
                    values = [str(v).lower() for v in rule.get("value", [])]
                    filtered_df = filtered_df[
                        s.str.lower().isin(values)
                    ]

        except Exception:
            continue

    return filtered_df


def filter_by_date_range(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    return _apply_date_range(df, start_date, end_date)
