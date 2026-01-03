# CSV ↔ JSON conversion
import pandas as pd
from typing import Dict, Any
import os


def csv_to_json(csv_path: str) -> Dict[str, Any]:
    """
    Convert CSV to JSON (worst-case raw data safe)
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    try:
        # Read CSV safely (handles bad encoding, broken rows)
        df = pd.read_csv(
            csv_path,
            encoding="utf-8",
            encoding_errors="replace",
            on_bad_lines="skip"
        )

        # Drop completely empty rows
        df.dropna(how="all", inplace=True)

        # Normalize column names
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        # Attempt type normalization (best-effort)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="ignore")

        # Replace NaN with None (JSON-safe)
        df = df.where(pd.notnull(df), None)

        return {
            "records": df.to_dict(orient="records"),
            "meta": {
                "source": "csv",
                "rows": int(len(df)),
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

    try:
        # Extract records safely
        if isinstance(json_data, dict) and "records" in json_data:
            records = json_data["records"]
        elif isinstance(json_data, list):
            records = json_data
        else:
            raise ValueError("Invalid JSON format")

        if not records:
            raise ValueError("No records to write")

        # Normalize / flatten nested JSON
        df = pd.json_normalize(records, sep="_")

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write CSV (overwrite old file safely)
        df.to_csv(output_path, index=False)

    except Exception as e:
        raise RuntimeError(f"JSON → CSV conversion failed: {str(e)}")
