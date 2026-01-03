# Constants
# Supported file formats
SUPPORTED_FORMATS = ["csv", "json", "xlsx", "xls", "md"]

# Job statuses
JOB_STATUS_PENDING = "pending"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

# File size limits (in bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Storage paths
UPLOAD_DIR = "storage/uploads"
OUTPUT_DIR = "storage/outputs"
ERROR_DIR = "storage/errors"
