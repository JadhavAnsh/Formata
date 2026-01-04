# CSV ↔ JSON conversion

import pandas as pd
from typing import Dict, Any
import os


def csv_to_json(csv_path: str) -> Dict[str, Any]:
    """
    Convert CSV to JSON (worst-case raw data safe)
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    try:
        # Read everything as string first (max safety)
        df = pd.read_csv(
            csv_path,
            dtype=str,
            encoding="utf-8",
            encoding_errors="replace",
            on_bad_lines="skip"
        )

        # Drop fully empty rows
        df.dropna(how="all", inplace=True)

        # Normalize column names
        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"[^\w]+", "_", regex=True)
            .str.strip("_")
        )

        # Normalize cell values + best-effort typing
        for col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace(
                    {
                        "": None,
                        "none": None,
                        "null": None,
                        "nan": None,
                        "na": None,
                        "n/a": None,
                        "undefined": None
                    }
                )
            )

            # Try numeric conversion safely
            numeric_series = pd.to_numeric(df[col], errors="coerce")
            if numeric_series.notna().sum() > 0:
                df[col] = numeric_series.where(numeric_series.notna(), df[col])

        # JSON-safe conversion
        records = df.where(pd.notnull(df), None).to_dict(orient="records")

        return {
            "records": records,
            "meta": {
                "source": "csv",
                "rows": len(records),
                "columns": list(df.columns)
            }
        }

    except Exception as e:
        raise RuntimeError(f"CSV → JSON conversion failed: {str(e)}")


def json_to_csv(json_data: Dict[str, Any], output_path: str) -> None:
    """
    Convert JSON to CSV (handles nested & inconsistent JSON)
    """
    if not json_data:
        raise ValueError("Empty JSON data provided")

    # Extract records safely
    if isinstance(json_data, dict):
        records = json_data.get("records", [])
    elif isinstance(json_data, list):
        records = json_data
    else:
        raise ValueError("Invalid JSON structure")

    if not records:
        raise ValueError("No records available for CSV conversion")

    # Flatten nested JSON
    df = pd.json_normalize(records, sep="_", max_level=10)

    # Normalize column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.strip("_")
    )

    # Normalize cell values
    df = df.map(
        lambda x: None
        if str(x).strip().lower()
        in {"", "none", "null", "nan", "na", "n/a", "undefined"}
        else x
    )

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Check if there's a directory component
        os.makedirs(output_dir, exist_ok=True)

    # Write CSV
    df.to_csv(output_path, index=False)
