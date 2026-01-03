import pandas as pd
import re


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names dynamically
    """
    if df is None or df.empty:
        return df

    try:
        new_columns = []
        seen = {}

        for col in df.columns:
            # Normalize name
            clean = str(col).strip().lower()
            clean = re.sub(r"[^\w]+", "_", clean)
            clean = re.sub(r"_+", "_", clean).strip("_")

            # Handle duplicate column names
            if clean in seen:
                seen[clean] += 1
                clean = f"{clean}_{seen[clean]}"
            else:
                seen[clean] = 0

            new_columns.append(clean)

        df = df.copy()
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

            # Skip already clean numeric columns
            if pd.api.types.is_numeric_dtype(series):
                continue

            # Try boolean conversion
            lowered = series.astype(str).str.lower()
            if lowered.isin(["true", "false", "1", "0", "yes", "no"]).mean() > 0.6:
                df[col] = lowered.map(
                    {
                        "true": True,
                        "1": True,
                        "yes": True,
                        "false": False,
                        "0": False,
                        "no": False,
                    }
                )
                continue

            # Try numeric conversion
            numeric = pd.to_numeric(series, errors="coerce")
            if numeric.notna().mean() > 0.6:
                df[col] = numeric
                continue

            # Try datetime conversion
            datetime = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
            if datetime.notna().mean() > 0.6:
                df[col] = datetime
                continue

            # Else: keep as text (object)

    except Exception:
        return df

    return df
