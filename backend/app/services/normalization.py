import pandas as pd
import re
import warnings


MISSING_TOKENS = {
    "",
    " ",
    "null",
    "none",
    "nan",
    "na",
    "n/a",
    "n.a.",
    "undefined",
    "unknown",
    "not_provided",
    "not provided",
    "missing",
    "-",
    "--",
}

NUMERIC_HINTS = {
    "age",
    "amount",
    "balance",
    "count",
    "cost",
    "income",
    "number",
    "price",
    "quantity",
    "qty",
    "revenue",
    "salary",
    "score",
    "total",
    "value",
}

DATE_HINTS = {
    "birth",
    "created",
    "date",
    "dob",
    "joined",
    "join",
    "timestamp",
    "time",
    "updated",
}

EMAIL_HINTS = {"email", "mail"}
BOOL_HINTS = {"active", "bool", "enabled", "flag", "has_", "is_", "valid"}

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NUMERIC_PATTERN = re.compile(r"-?\d+(?:[,.]\d+)?")


def _normalize_missing_value(value):
    if value is None:
        return None

    if isinstance(value, float) and pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    if text.lower() in MISSING_TOKENS:
        return None

    return text


def _column_role(column_name: str) -> str:
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


def _clean_series(series: pd.Series) -> pd.Series:
    return series.map(_normalize_missing_value)


def _coerce_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = _clean_series(series)

    def _extract(value):
        if value is None:
            return pd.NA
        text = str(value).strip().lower()
        if text in MISSING_TOKENS:
            return pd.NA

        text = re.sub(r"[₹$€£¥,%]", "", text)
        text = re.sub(r"\b(years?|yrs?|rs|usd|inr|gbp|eur|k|m)\b", "", text)
        match = NUMERIC_PATTERN.search(text.replace(" ", ""))
        if not match:
            return pd.NA

        token = match.group(0).replace(",", "")
        try:
            if "." in token:
                return float(token)
            return int(token)
        except Exception:
            try:
                return float(token)
            except Exception:
                return pd.NA

    numeric = cleaned.map(_extract)
    numeric = pd.to_numeric(numeric, errors="coerce")

    if numeric.notna().sum() == 0:
        return numeric

    non_null = numeric.dropna()
    if not non_null.empty and (non_null == non_null.astype(int)).all():
        return numeric.astype("Int64")

    return numeric


def _coerce_datetime_series(series: pd.Series) -> pd.Series:
    cleaned = _clean_series(series)
    common_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%b %d %Y",
        "%b %d %Y %H:%M:%S",
    ]

    def _parse_single(value):
        normalized = _normalize_missing_value(value)
        if normalized is None:
            return pd.NaT

        for fmt in common_formats:
            parsed = pd.to_datetime(normalized, errors="coerce", format=fmt)
            if not pd.isna(parsed):
                return parsed

        return pd.to_datetime(normalized, errors="coerce", dayfirst=True)

    parsed = cleaned.map(_parse_single)
    return pd.to_datetime(parsed, errors="coerce")


def _coerce_boolean_series(series: pd.Series) -> pd.Series:
    cleaned = _clean_series(series)
    lowered = cleaned.astype("string").str.lower().str.strip()
    mapped = lowered.map(
        {
            "true": True,
            "t": True,
            "yes": True,
            "y": True,
            "1": True,
            "false": False,
            "f": False,
            "no": False,
            "n": False,
            "0": False,
        }
    )
    return mapped.astype(object)


def _parse_datetime(series: pd.Series) -> pd.Series:
    """Parse datetimes without noisy warnings by trying common formats first."""
    if series is None:
        return series

    cleaned = _clean_series(series)
    common_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]

    parsed = pd.Series(pd.NaT, index=cleaned.index, dtype="datetime64[ns]")
    for fmt in common_formats:
        candidate = pd.to_datetime(cleaned, errors="coerce", format=fmt)
        parsed = parsed.fillna(candidate)

    # Fallback: allow mixed formats but silence the pandas warning
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Could not infer format",
            category=UserWarning,
        )
        fallback = pd.to_datetime(cleaned, errors="coerce")

    if parsed.notna().any():
        return parsed.fillna(fallback)

    return fallback


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names dynamically
    """
    if df is None or df.empty:
        return df

    try:
        df = df.copy()
        new_columns = []
        seen = {}

        for col in df.columns:
            clean = str(col).strip().lower()
            clean = re.sub(r"[^\w]+", "_", clean)
            clean = re.sub(r"_+", "_", clean).strip("_")

            # Handle empty or invalid column names
            if not clean:
                clean = "column"

            # Resolve duplicates deterministically
            if clean in seen:
                seen[clean] += 1
                clean = f"{clean}_{seen[clean]}"
            else:
                seen[clean] = 0

            new_columns.append(clean)

        df.columns = new_columns
        return df

    except Exception:
        return df


def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert and normalize data types dynamically
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    try:
        for col in df.columns:
            series = df[col]
            cleaned = _clean_series(series)
            role = _column_role(col)

            # ---------- BOOLEAN ----------
            if role == "boolean":
                df[col] = _coerce_boolean_series(cleaned)
                continue

            # ---------- DATETIME ----------
            if role == "datetime":
                datetime = _coerce_datetime_series(cleaned)
                if datetime.notna().mean() > 0.35:
                    df[col] = datetime
                    continue

            datetime = _coerce_datetime_series(cleaned)
            if datetime.notna().mean() > 0.7:
                df[col] = datetime
                continue

            # ---------- NUMERIC ----------
            numeric = _coerce_numeric_series(cleaned)

            if role == "numeric" and numeric.notna().mean() > 0.35:
                df[col] = numeric
                continue

            if numeric.notna().mean() > 0.7:
                df[col] = numeric
                continue

            # ---------- EMAIL ----------
            if role == "email":
                emails = cleaned.astype("string").str.strip()
                df[col] = emails.where(emails.str.match(EMAIL_PATTERN, na=False), None)
                continue

            # ---------- TEXT ----------
            # Final cleanup for text columns
            df[col] = cleaned.astype(object)

    except Exception:
        return df

    return df


def prepare_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a cleaned DataFrame for CSV/JSON export.

    Datetime columns are converted to ISO-8601 strings so exported CSV files do
    not leak epoch timestamps or pandas internal integer representations.
    """
    if df is None or df.empty:
        return df

    export_df = df.copy()

    for col in export_df.columns:
        series = export_df[col]

        # Already-typed datetime columns should be exported as readable dates.
        if pd.api.types.is_datetime64_any_dtype(series):
            export_df[col] = series.dt.strftime("%Y-%m-%d").where(series.notna(), None)
            continue

        role = _column_role(col)
        if role != "datetime":
            continue

        parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)

        # Some pipeline paths surface datetimes as epoch integers (nanoseconds).
        # Convert those back to datetime so exports stay human-readable.
        if parsed.notna().mean() < 0.35:
            numeric = pd.to_numeric(series, errors="coerce")
            numeric = numeric.where(numeric != -9223372036854775808, pd.NA)
            epoch_parsed = pd.to_datetime(numeric, errors="coerce", unit="ns")
            if epoch_parsed.notna().mean() > parsed.notna().mean():
                parsed = epoch_parsed

        if parsed.notna().mean() > 0.35:
            export_df[col] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), None)

    return export_df
 