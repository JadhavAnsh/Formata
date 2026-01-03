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
        df_copy = df.copy()

        # Normalize values before fingerprinting
        normalized = df_copy.applymap(
            lambda x: str(x).strip().lower() if pd.notna(x) else ""
        )

        # Stable fingerprint per row
        fingerprint = normalized.apply(
            lambda row: "|".join(row.values), axis=1
        )

        # Keep first occurrence only
        deduped_df = df_copy.loc[~fingerprint.duplicated()]

        return deduped_df.reset_index(drop=True)

    except Exception:
        # Fail soft
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
        # Auto-detect numeric-like columns if not provided
        if not columns:
            columns = []
            for col in cleaned_df.columns:
                numeric_series = pd.to_numeric(cleaned_df[col], errors="coerce")
                if numeric_series.notna().sum() > len(numeric_series) * 0.6:
                    columns.append(col)

        for col in columns:
            if col not in cleaned_df.columns:
                continue

            series = pd.to_numeric(cleaned_df[col], errors="coerce")

            # Skip sparse or constant columns
            if series.notna().sum() < 10 or series.nunique(dropna=True) <= 2:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            if pd.isna(iqr) or iqr == 0:
                continue

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            # Filter safely
            mask = (series >= lower) & (series <= upper)
            cleaned_df = cleaned_df[mask]

    except Exception:
        return df

    return cleaned_df.reset_index(drop=True)
