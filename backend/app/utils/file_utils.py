# File utilities
import os
from typing import Optional


def save_upload(file_content: bytes, filename: str, upload_dir: str = "storage/uploads") -> str:
    """
    Save uploaded file to disk
    """
    pass


def get_file_extension(filename: str) -> str:
    """
    Get file extension
    """
    return os.path.splitext(filename)[1].lower()


def ensure_directory(path: str) -> None:
    """
    Ensure directory exists
    """
    os.makedirs(path, exist_ok=True)
