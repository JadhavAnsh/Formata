# CSV ↔ JSON conversion

import pandas as pd
from typing import Dict, Any
import os
import json

from app.services.normalization import normalize_types, standardize_columns, prepare_for_export


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

        df = standardize_columns(df)
        df = normalize_types(df)

        export_df = prepare_for_export(df)

        # JSON-safe conversion
        records = json.loads(export_df.to_json(orient="records"))

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
    df = normalize_types(df)
    export_df = prepare_for_export(df)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Check if there's a directory component
        os.makedirs(output_dir, exist_ok=True)

    # Write CSV
    export_df.to_csv(output_path, index=False)
