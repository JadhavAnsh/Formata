# Full processing flow
from typing import Dict, Any
import os

from services.parser import (
    parse_csv,
    parse_json,
    parse_excel,
    parse_markdown
)
from services.normalization import (
    standardize_columns,
    normalize_types
)
from services.filtering import apply_filters
from services.noise import remove_duplicates, remove_outliers
from services.conversion import csv_to_json, json_to_csv


class ProcessingPipeline:
    """
    Orchestrates the full data processing workflow
    """

    def __init__(self):
        self.upload_dir = "storage/uploads"
        self.output_dir = "storage/outputs"
        self.error_dir = "storage/errors"

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.error_dir, exist_ok=True)

    def run(self, job_id: str, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete processing pipeline
        """
        result = {
            "job_id": job_id,
            "status": "processing",
            "rows_before": 0,
            "rows_after": 0,
            "output_path": None,
            "errors": []
        }

        try:
            ext = os.path.splitext(file_path)[1].lower()

            # -------- Parse --------
            if ext == ".csv":
                df = parse_csv(file_path)

            elif ext in [".xlsx", ".xls"]:
                df = parse_excel(file_path)

            elif ext == ".json":
                json_data = parse_json(file_path)
                df = normalize_types(
                    standardize_columns(
                        __import__("pandas").DataFrame(json_data["records"])
                    )
                )

            elif ext == ".md":
                content = parse_markdown(file_path)
                result["status"] = "completed"
                result["output_path"] = None
                result["note"] = "Markdown parsed as text"
                return result

            else:
                raise ValueError(f"Unsupported file type: {ext}")

            result["rows_before"] = len(df)

            # -------- Normalize --------
            df = standardize_columns(df)
            df = normalize_types(df)

            # -------- Filtering --------
            filters = config.get("filters")
            if filters:
                df = apply_filters(df, filters)

            # -------- Noise removal --------
            if config.get("remove_duplicates", True):
                df = remove_duplicates(df)

            if config.get("remove_outliers"):
                df = remove_outliers(df, config.get("outlier_columns"))

            result["rows_after"] = len(df)

            # -------- Output --------
            output_format = config.get("output_format", "json")
            output_path = os.path.join(
                self.output_dir,
                f"{job_id}.{output_format}"
            )

            if output_format == "json":
                df.to_json(output_path, orient="records", indent=2)
            elif output_format == "csv":
                df.to_csv(output_path, index=False)
            else:
                raise ValueError("Unsupported output format")

            result["output_path"] = output_path
            result["status"] = "completed"

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))

            error_path = os.path.join(self.error_dir, f"{job_id}_error.txt")
            with open(error_path, "w") as f:
                f.write(str(e))

        return result
