# Deduplication and outlier removal
import pandas as pd
from typing import List


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate rows (schema-agnostic)
    """
    if df is None or df.empty:
        return df

    try:
        # Create a stable fingerprint for each row
        df_copy = df.copy()

        # Convert all values to string to handle mixed types
        fingerprint = df_copy.astype(str).apply(
            lambda row: "|".join(row.values), axis=1
        )

        # Keep first occurrence
        return df_copy.loc[~fingerprint.duplicated()].reset_index(drop=True)

    except Exception:
        return df


def remove_outliers(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    Remove outliers using IQR method
    Works dynamically on any numeric data
    """
    if df is None or df.empty:
        return df

    cleaned_df = df.copy()

    try:
        # Auto-detect numeric columns if not provided
        if not columns:
            columns = cleaned_df.select_dtypes(include="number").columns.tolist()

        for col in columns:
            if col not in cleaned_df.columns:
                continue

            series = pd.to_numeric(cleaned_df[col], errors="coerce")

            # Skip columns with too little data
            if series.notna().sum() < 10:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            if iqr == 0:
                continue

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            cleaned_df = cleaned_df[
                (series >= lower) & (series <= upper)
            ]

    except Exception:
        return df

    return cleaned_df.reset_index(drop=True)
