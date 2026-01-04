import pandas as pd
from typing import Dict, Any
import json
import os
import re


def parse_csv(file_path: str) -> pd.DataFrame:
    """Parse CSV file (worst-case safe)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        df = pd.read_csv(
            file_path,
            dtype=str,                    # read everything as text first
            encoding="utf-8",
            encoding_errors="replace",
            on_bad_lines="skip"
        )

        # Drop completely empty rows
        df.dropna(how="all", inplace=True)

        # Trim whitespace from all cells
        df = df.map(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        return df.reset_index(drop=True)

    except Exception as e:
        raise RuntimeError(f"Failed to parse CSV: {str(e)}")


def parse_json(file_path: str) -> Dict[str, Any]:
    """Parse JSON file (object / list / nested safe)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read().strip()

        if not raw:
            return {"records": []}

        data = json.loads(raw)

        # Case 1: list of records
        if isinstance(data, list):
            return {"records": data}

        # Case 2: dict wrapper
        if isinstance(data, dict):
            for key in ["records", "data", "items", "results", "rows"]:
                if key in data and isinstance(data[key], list):
                    return {"records": data[key]}

            # Single object → wrap as record
            return {"records": [data]}

        raise ValueError("Unsupported JSON structure")

    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON: {str(e)}")


def parse_excel(file_path: str) -> pd.DataFrame:
    """Parse Excel file (multi-sheet safe)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    try:
        sheets = pd.read_excel(
            file_path,
            sheet_name=None,
            dtype=str
        )

        frames = []

        for _, df in sheets.items():
            if df is None or df.empty:
                continue

            df.dropna(how="all", inplace=True)

            # Trim whitespace
            df = df.map(
                lambda x: x.strip() if isinstance(x, str) else x
            )

            frames.append(df)

        if not frames:
            return pd.DataFrame()

        return pd.concat(frames, ignore_index=True)

    except Exception as e:
        raise RuntimeError(f"Failed to parse Excel: {str(e)}")


def parse_markdown(file_path: str) -> str:
    """Parse Markdown file (table + text safe)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Normalize whitespace
        content = re.sub(r"\r\n", "\n", content)
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()

    except Exception as e:
        raise RuntimeError(f"Failed to parse Markdown: {str(e)}")
