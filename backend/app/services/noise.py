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
        initial_count = len(df_copy)

        # Try simple drop_duplicates first (exact matches)
        df_deduped = df_copy.drop_duplicates()
        exact_dupes_removed = initial_count - len(df_deduped)
        
        print(f"[DEDUPE] Initial rows: {initial_count}")
        print(f"[DEDUPE] After exact match removal: {len(df_deduped)} (removed {exact_dupes_removed})")
        
        # If no exact duplicates, try normalized deduplication
        if exact_dupes_removed == 0:
            # Normalize values before fingerprinting
            # Use map() instead of deprecated applymap()
            normalized = df_copy.map(
                lambda x: str(x).strip().lower() if pd.notna(x) else ""
            )

            # Stable fingerprint per row
            fingerprint = normalized.apply(
                lambda row: "|".join(row.values), axis=1
            )

            # Keep first occurrence only
            df_deduped = df_copy.loc[~fingerprint.duplicated()]
            fuzzy_dupes_removed = initial_count - len(df_deduped)
            print(f"[DEDUPE] After fuzzy match removal: {len(df_deduped)} (removed {fuzzy_dupes_removed})")

        return df_deduped.reset_index(drop=True)

    except Exception as e:
        # Fail soft but log the error
        print(f"[DEDUPE ERROR] {str(e)}")
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
