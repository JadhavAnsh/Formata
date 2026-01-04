import pandas as pd
import re


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

            # Normalize empty-like values early
            series = series.replace(
                [
                    "",
                    " ",
                    "null",
                    "none",
                    "nan",
                    "na",
                    "n/a",
                    "N/A",
                    "undefined",
                ],
                None
            )

            # ---------- BOOLEAN ----------
            lowered = series.astype(str).str.lower().str.strip()
            if lowered.isin(
                ["true", "false", "1", "0", "yes", "no"]
            ).mean() > 0.7:
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

            # ---------- NUMERIC ----------
            numeric = pd.to_numeric(series, errors="coerce")
            if numeric.notna().mean() > 0.7:
                df[col] = numeric
                continue

            # ---------- DATETIME ----------
            datetime = pd.to_datetime(
                series, errors="coerce"
            )
            if datetime.notna().mean() > 0.7:
                df[col] = datetime
                continue

            # ---------- TEXT ----------
            # Final cleanup for text columns
            df[col] = series.astype(str).str.strip()

    except Exception:
        return df

    return df
 