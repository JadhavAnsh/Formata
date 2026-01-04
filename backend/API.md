# Formata API Documentation

Complete API reference for Formata data processing platform. All endpoints (except `/` and `/health`) require an API key.

---

## Base URL
```
http://localhost:8000
```

---

## Authentication

All protected endpoints require an API key header:

```
Headers:
  X-API-Key: your_api_key_here
```

---

## Table of Contents
1. [Health & Status](#health--status)
2. [Data Ingestion](#data-ingestion)
3. [Data Processing](#data-processing)
4. [Results & Downloads](#results--downloads)
5. [Job Management](#job-management)
6. [Error Handling](#error-handling)
7. [Data Profiling](#data-profiling)
8. [Format Conversion](#format-conversion)
9. [Vector Generation & LLM Integration](#vector-generation--llm-integration)

---

## Health & Status

### GET `/`
Get API status (No authentication required)

**Headers:**
```
None
```

**Request Body:**
```
None
```

**Response:**
```json
{
  "message": "Formata API is running"
}
```

**Status Code:** `200`

---

### GET `/health`
Health check endpoint (No authentication required)

**Headers:**
```
None
```

**Request Body:**
```
None
```

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Code:** `200`

---

## Data Ingestion

### POST `/ingest`
Upload a file for processing

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <binary file data>
```

**Supported Formats:**
- `.csv` - Comma-separated values
- `.json` - JSON objects/arrays
- `.xlsx` - Excel spreadsheet
- `.xls` - Excel spreadsheet (older format)
- `.md` - Markdown tables

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "File ingested successfully. Use /status/{job_id} to check processing status."
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `400` | Unsupported file format | File extension not supported |
| `500` | Internal server error | File upload failed |

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@data.csv"
```

---

## Data Processing

### POST `/process/{job_id}`
Start processing pipeline for an ingested job

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Path Parameters:**
```
job_id: string (UUID from /ingest response)
```

**Request Body:**
```json
{
  "normalize": true,
  "remove_duplicates": true,
  "remove_outliers": false,
  "filters": {
    "column_name": "value",
    "age": 25
  },
  "validation_rules": {
    "age": {
      "type": "number",
      "min": 0,
      "max": 120,
      "required": true
    }
  },
  "output_format": "csv",
  "detect_data_quality_issues": true
}
```

**Field Descriptions:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `normalize` | boolean | `true` | Normalize data types and column names |
| `remove_duplicates` | boolean | `true` | Remove duplicate rows |
| `remove_outliers` | boolean | `false` | Detect and flag statistical outliers |
| `filters` | object | `null` | Apply column filters (e.g., age > 25) |
| `validation_rules` | object | `null` | Custom validation rules per column |
| `output_format` | string | `"csv"` | Output format: `"csv"` or `"json"` |
| `detect_data_quality_issues` | boolean | `true` | Enable data quality analysis |

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Processing started. Monitor progress at /status/{job_id}. Errors stream via SSE at /stream-errors/{job_id}."
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `400` | Job in invalid state | Job already processed or failed |
| `500` | Internal server error | Processing initialization failed |

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/process/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "normalize": true,
    "remove_duplicates": true,
    "output_format": "csv"
  }'
```

---

## Results & Downloads

### GET `/result/{job_id}/download`
Download processed data file

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```
None
```

**Response:**
```
<binary file content>
Content-Type: text/csv or application/json
Content-Disposition: attachment; filename="job_id_clean.csv"
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `400` | Job not completed | Job still processing or failed |
| `404` | Output file not found | Result file missing |
| `500` | Internal server error | Download failed |

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/result/550e8400-e29b-41d4-a716-446655440000/download" \
  -H "X-API-Key: your_api_key_here" \
  -o result.csv
```

---

## Job Management

### GET `/jobs`
List all jobs

**Headers:**
```
X-API-Key: your_api_key_here
```

**Request Body:**
```
None
```

**Response:**
```json
[
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "data.csv",
    "status": "completed",
    "progress": 1.0,
    "created_at": "2026-01-04T10:30:00Z",
    "updated_at": "2026-01-04T10:35:00Z",
    "errors": [],
    "result": {
      "output_path": "storage/outputs/550e8400-e29b-41d4-a716-446655440000.csv",
      "rows_processed": 1000,
      "columns": ["name", "age", "email"]
    },
    "metadata": {
      "clean_profile_path": "storage/reports/550e8400-e29b-41d4-a716-446655440000_profile.html"
    }
  }
]
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `500` | Internal server error | Failed to list jobs |

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/jobs" \
  -H "X-API-Key: your_api_key_here"
```

---

### GET `/status/{job_id}`
Get current job status and progress

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```
None
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "data.csv",
  "status": "processing",
  "progress": 0.65,
  "created_at": "2026-01-04T10:30:00Z",
  "updated_at": "2026-01-04T10:33:15Z",
  "errors": [
    {
      "step": "normalization",
      "message": "Column 'age' has invalid values in rows 5, 12, 23"
    }
  ],
  "result": null,
  "metadata": {}
}
```

**Status Values:**
- `pending` - Job created, waiting to process
- `processing` - Currently processing (0.0 < progress < 1.0)
- `completed` - Processing finished successfully (progress = 1.0)
- `failed` - Processing encountered critical error
- `cancelled` - Job was cancelled

**Progress:**
- `0.0` - Not started
- `0.0 to 1.0` - Processing
- `1.0` - Completed

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `500` | Internal server error | Failed to retrieve status |

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key_here"
```

---

### GET `/jobs/{job_id}`
Get detailed job information

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```
None
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "data.csv",
  "file_path": "storage/uploads/550e8400-e29b-41d4-a716-446655440000_data.csv",
  "status": "completed",
  "progress": 1.0,
  "created_at": "2026-01-04T10:30:00Z",
  "updated_at": "2026-01-04T10:35:00Z",
  "errors": [],
  "result": {
    "output_path": "storage/outputs/550e8400-e29b-41d4-a716-446655440000.csv",
    "rows_processed": 1000,
    "columns": ["name", "age", "email"],
    "reports": {
      "error_report": "storage/errors/550e8400-e29b-41d4-a716-446655440000_errors.txt"
    }
  },
  "metadata": {
    "clean_profile_path": "storage/reports/550e8400-e29b-41d4-a716-446655440000_profile.html"
  }
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `500` | Internal server error | Failed to retrieve job details |

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key_here"
```

---

### DELETE `/jobs/{job_id}`
Delete a job and all associated data

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```
None
```

**Response:**
```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 deleted successfully",
  "deleted_files": [
    "storage/uploads/550e8400-e29b-41d4-a716-446655440000_data.csv",
    "storage/outputs/550e8400-e29b-41d4-a716-446655440000.csv",
    "storage/reports/550e8400-e29b-41d4-a716-446655440000_profile.html",
    "storage/errors/550e8400-e29b-41d4-a716-446655440000_errors.txt"
  ]
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `500` | Internal server error | Deletion failed |

**Example cURL:**
```bash
curl -X DELETE "http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key_here"
```

---

## Error Handling

### GET `/errors/{job_id}/download`
Download error report for a job

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```
None
```

**Response:**
```
<text file content>
Content-Type: text/plain
Content-Disposition: attachment; filename="job_id_errors.txt"
```

**Sample Error Report Content:**
```
Job ID: 550e8400-e29b-41d4-a716-446655440000
Processing Date: 2026-01-04 10:30:00

ERRORS ENCOUNTERED:
==================

1. [NORMALIZATION] - Column 'age' Type Coercion Failed
   - Rows affected: 5, 12, 23
   - Values: 'unknown', 'N/A', '99+'
   - Action: Kept as-is, marked for review

2. [FILTERING] - Invalid Filter Expression
   - Filter: age > "twenty"
   - Error: Cannot compare numeric column with string value
   - Action: Filter ignored

Total Errors: 2
Total Warnings: 5
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `404` | No errors to report | Job completed without errors |
| `404` | Error report not found | Report file missing |
| `500` | Internal server error | Download failed |

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/errors/550e8400-e29b-41d4-a716-446655440000/download" \
  -H "X-API-Key: your_api_key_here" \
  -o errors.txt
```

---

## Data Profiling

### GET `/profile/{job_id}`
Get HTML data profile report

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```
None
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_path": "storage/reports/550e8400-e29b-41d4-a716-446655440000_profile.html",
  "content_type": "text/html",
  "content": "<html>... profile report ...</html>"
}
```

**Profile Includes:**
- Dataset overview (rows, columns, memory usage)
- Column statistics (type, missing %, unique values)
- Correlation analysis
- Missing data patterns
- Data quality warnings
- Variable interactions

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `202` | Job still processing | Not yet available |
| `500` | Job failed | Profile not generated |
| `404` | Profile not found | Generation failed or skipped |
| `500` | Internal server error | Report retrieval failed |

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/profile/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key_here" \
  -o profile.json
```

**Display in Frontend:**
```javascript
// React example
const response = await fetch(`/profile/${jobId}`, {
  headers: { "X-API-Key": apiKey }
});
const data = await response.json();
// Display HTML in iframe or render directly
document.getElementById('profile').innerHTML = data.content;
```

---

## Format Conversion

### POST `/convert/csv-to-json`
Convert CSV file to JSON

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <CSV file binary data>
```

**Response:**
```json
{
  "status": "success",
  "format": "json",
  "data": {
    "records": [
      {
        "name": "John Doe",
        "age": "30",
        "email": "john@example.com"
      },
      {
        "name": "Jane Smith",
        "age": "25",
        "email": "jane@example.com"
      }
    ],
    "meta": {
      "source": "csv",
      "rows": 2,
      "columns": ["name", "age", "email"]
    }
  },
  "message": "Successfully converted CSV to JSON"
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `400` | File must be a CSV file | Wrong file type |
| `400` | Invalid file or not found | File read error |
| `500` | Internal server error | Conversion failed |

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/convert/csv-to-json" \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@data.csv"
```

---

### POST `/convert/json-to-csv`
Convert JSON to CSV

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": {
    "records": [
      {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
      },
      {
        "name": "Jane Smith",
        "age": 25,
        "email": "jane@example.com"
      }
    ]
  }
}
```

**Alternative Request Body (direct array):**
```json
{
  "data": [
    {
      "name": "John Doe",
      "age": 30,
      "email": "john@example.com"
    },
    {
      "name": "Jane Smith",
      "age": 25,
      "email": "jane@example.com"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "format": "csv",
  "content": "name,age,email\nJohn Doe,30,john@example.com\nJane Smith,25,jane@example.com\n",
  "message": "Successfully converted JSON to CSV"
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `400` | Empty JSON data | No data provided |
| `400` | Invalid JSON structure | Incorrect format |
| `400` | No records available | Empty records array |
| `500` | Internal server error | Conversion failed |

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/convert/json-to-csv" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "records": [
        {"name": "John", "age": 30},
        {"name": "Jane", "age": 25}
      ]
    }
  }'
```

---

### POST `/convert`
Generic format converter (JSON to CSV)

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "input_format": "json",
  "output_format": "csv",
  "data": {
    "records": [
      {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
      }
    ]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "input_format": "json",
  "output_format": "csv",
  "content": "name,age,email\nJohn Doe,30,john@example.com\n"
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `400` | Unsupported format | Format not in [csv, json] |
| `400` | Input/output must differ | Same format provided |
| `400` | CSV to JSON requires upload | Use /convert/csv-to-json |
| `500` | Internal server error | Conversion failed |

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "input_format": "json",
    "output_format": "csv",
    "data": {
      "records": [{"name": "John", "age": 30}]
    }
  }'
```

---

## Vector Generation & LLM Integration

**Overview:**  
The vector endpoints transform your clean, processed data into numerical vector embeddings that can be directly fed into Large Language Models (LLMs), machine learning algorithms, or semantic search systems. This feature bridges the gap between data processing and AI model integration.

**Why Use Vectors?**
- **LLM-Ready**: Convert tabular data into embeddings for GPT, Claude, or other LLMs
- **ML Integration**: Use with scikit-learn, TensorFlow, PyTorch for training/inference
- **Semantic Search**: Enable similarity-based search and recommendations
- **Flexible Formats**: Export as `.pkl` (Python-native) or `.h5` (cross-platform, compressed)

**How It Works:**
1. Text columns are converted to 512-dimensional embeddings using HashingVectorizer
2. Numeric columns are standardized (zero mean, unit variance)
3. Boolean columns become binary values (0/1)
4. Categorical columns are one-hot encoded or embedded based on cardinality
5. All features are combined into a single vector per data row

**Available Methods:**
- **Hybrid** (default): Best for mixed data - combines text embeddings, normalized numerics, and categorical encoding
- **Text-Only**: Treats all columns as text with 512-dim embeddings - ideal for NLP tasks
- **Numeric**: Fast, minimal vectorization - only scales numbers and encodes categoricals

### POST `/vectors/{job_id}/generate`
Generate vector embeddings from processed data

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```json
{
  "method": "hybrid"
}
```

**Method Options:**

| Method | Description | Use Case |
|--------|-------------|----------|
| `hybrid` | Text embeddings (512d) + normalized numeric + one-hot categorical | Recommended; best for mixed data types |
| `text_only` | Treats all columns as text, generates embeddings | When all data is textual |
| `numeric` | Numeric normalization + one-hot encoding | Fast processing, structured data only |

**Response:**
```json
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "vector_shape": [1000, 2048],
  "n_samples": 1000,
  "n_features": 2048,
  "method": "hybrid",
  "message": "Vectors generated successfully. Download using /vectors/{job_id}/download with format parameter.",
  "download_formats": ["pkl", "h5"]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `vector_shape` | array | `[n_samples, n_features]` dimension |
| `n_samples` | integer | Number of data rows |
| `n_features` | integer | Total vector dimensions |
| `method` | string | Vectorization method used |
| `download_formats` | array | Available download formats |

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `400` | Job not completed | Job still processing or failed |
| `400` | Invalid method | Method not in [hybrid, text_only, numeric] |
| `500` | Internal server error | Vector generation failed |

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/vectors/550e8400-e29b-41d4-a716-446655440000/generate" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "hybrid"
  }'
```

**Example Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/vectors/job_id/generate",
    headers={"X-API-Key": "your_api_key_here"},
    json={"method": "hybrid"}
)
data = response.json()
print(f"Vectors generated: {data['vector_shape']}")
```

---

### GET `/vectors/{job_id}/download`
Download vectorized data in specified format

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Query Parameters:**
```
format: string (required) - pkl or h5
```

**Response:**
```
<binary vector file>
Content-Type: application/octet-stream (pkl) or application/x-hdf (h5)
Content-Disposition: attachment; filename="job_id_vectors.pkl" or "job_id_vectors.h5"
Headers:
  X-Vector-Shape: [1000, 2048]
  X-Vector-Method: hybrid
```

**Format Comparison:**

| Format | File Size | Speed | Best For | Language Support |
|--------|-----------|-------|----------|------------------|
| `.pkl` | Smaller | Faster | Python projects, rapid prototyping | Python |
| `.h5` | Larger | Slower (gzip) | Large datasets, production systems | Python, R, JavaScript, Java |

**File Structure - Pickle (.pkl):**
```python
import pickle

with open("vectors.pkl", "rb") as f:
    data = pickle.load(f)
    
vectors = data["vectors"]              # numpy array, shape (1000, 2048)
metadata = data["metadata"]            # dict with info about vectors

# Access metadata
print(metadata["shape"])               # [1000, 2048]
print(metadata["original_columns"])    # ['name', 'age', 'email', ...]
print(metadata["feature_names"][:10])  # First 10 feature names
```

**File Structure - HDF5 (.h5):**
```python
import h5py

with h5py.File("vectors.h5", "r") as f:
    vectors = f["vectors"][:]                              # numpy array
    feature_names = [name.decode() for name in f["feature_names"][:]]
    original_columns = [col.decode() for col in f["original_columns"][:]]
    
    # Access metadata
    metadata = f["metadata"]
    shape = metadata.attrs["shape"]
    method = metadata.attrs["method"]
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `400` | Job not completed | Job still processing |
| `400` | Invalid format | Format not in [pkl, h5] |
| `404` | Output file not found | Result file missing |
| `500` | Internal server error | Download failed |

**Example cURL - Pickle:**
```bash
curl -X GET "http://localhost:8000/vectors/550e8400-e29b-41d4-a716-446655440000/download?format=pkl" \
  -H "X-API-Key: your_api_key_here" \
  -o vectors.pkl
```

**Example cURL - HDF5:**
```bash
curl -X GET "http://localhost:8000/vectors/550e8400-e29b-41d4-a716-446655440000/download?format=h5" \
  -H "X-API-Key: your_api_key_here" \
  -o vectors.h5
```

**Example Python - Using Pickle Vectors with LLM:**
```python
import pickle
import numpy as np
from transformers import GPT2LMHeadModel  # or your LLM

# Load vectors
with open("vectors.pkl", "rb") as f:
    data = pickle.load(f)
    vectors = data["vectors"]  # shape: (1000, 2048)

# Use with LLM
model = GPT2LMHeadModel.from_pretrained("gpt2")

for i, vector in enumerate(vectors[:10]):  # Process first 10
    # Feed to your LLM
    output = model(input_ids=vector)
    print(f"Sample {i}: {output}")
```

**Example Python - Using HDF5 Vectors:**
```python
import h5py
import numpy as np

# Load vectors in chunks (memory efficient for large files)
with h5py.File("vectors.h5", "r") as f:
    n_samples = f["vectors"].shape[0]
    
    # Process in batches
    batch_size = 32
    for start in range(0, n_samples, batch_size):
        end = min(start + batch_size, n_samples)
        batch_vectors = f["vectors"][start:end]  # Load only batch
        
        # Use batch_vectors with your LLM
        print(f"Processing samples {start}-{end}")
```

---

### GET `/vectors/{job_id}/info`
Get vector information without downloading

**Headers:**
```
X-API-Key: your_api_key_here
```

**Path Parameters:**
```
job_id: string (UUID)
```

**Request Body:**
```
None
```

**Response:**
```json
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "vector_info": {
    "shape": [1000, 2048],
    "n_samples": 1000,
    "n_features": 2048,
    "method": "hybrid",
    "original_columns": ["name", "age", "email", "salary", "department"],
    "feature_names": [
      "name_emb_0", "name_emb_1", "name_emb_2",
      "age_normalized", "email_emb_0", "email_emb_1",
      "salary_normalized", "department_one_hot_0",
      "... 2040 more features"
    ]
  },
  "download_formats": ["pkl", "h5"],
  "supported_methods": ["hybrid", "text_only", "numeric"]
}
```

**Status Code:** `200`

**Error Responses:**

| Status Code | Error | Description |
|------------|-------|-------------|
| `404` | Job not found | Invalid job_id |
| `400` | Job not completed | Job still processing |
| `500` | Internal server error | Failed to retrieve info |

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/vectors/550e8400-e29b-41d4-a716-446655440000/info" \
  -H "X-API-Key: your_api_key_here"
```

---

### Using Vector Files

**Quick Start with Python:**

```python
# For .pkl format (smaller, Python-only)
import pickle
import numpy as np

with open("vectors.pkl", "rb") as f:
    data = pickle.load(f)
    vectors = data["vectors"]      # numpy array: (n_samples, n_features)
    metadata = data["metadata"]    # dict with column info

print(f"Shape: {vectors.shape}")   # e.g., (1000, 2048)
print(f"Columns: {metadata['original_columns']}")

# Feed to your LLM or ML model
# Example: Use with OpenAI, scikit-learn, transformers, etc.
```

```python
# For .h5 format (larger files, cross-platform, compressed)
import h5py
import numpy as np

with h5py.File("vectors.h5", "r") as f:
    # Load all at once
    vectors = f["vectors"][:]
    
    # OR load in chunks for memory efficiency (good for large datasets)
    batch_size = 1000
    for start in range(0, f["vectors"].shape[0], batch_size):
        batch = f["vectors"][start:start+batch_size]
        # Process batch...
```

**Vector File Contents:**
- `vectors`: numpy array with shape (n_samples, n_features)
- `metadata`: Information about vectorization method, original columns, feature names
- Each row in vectors corresponds to a row in your original cleaned data

**Use Cases:**
- Train ML models (classification, regression, clustering)
- Feed data to LLMs for context or fine-tuning
- Semantic search and similarity matching
- Anomaly detection with embeddings
- Data visualization and dimensionality reduction

---

## Vector Encoding Details

### Hybrid Method (Recommended)

**Text Columns:** 512-dimensional embeddings via HashingVectorizer (normalized L2)  
**Numeric Columns:** Standardized to zero mean, unit variance  
**Boolean Columns:** Binary (0 or 1)  
**Categorical Columns:** One-hot encoded if ≤10 unique values, else embedded as text

**Example:**
```
Original Data: [name: "John", age: 30, active: true]
          ↓
name (text) → 512-dim embedding
age (numeric) → 1-dim normalized value
active (boolean) → 1-dim binary value
          ↓
Final Vector: 514 dimensions total (for 1 sample)
```

### Text-Only Method

All columns treated as text, generates 512-dimensional embeddings per column.

**Example:**
```
Original Data: [name: "John", age: 30, email: "john@example.com"]
          ↓
name → 512-dim embedding
age → 512-dim embedding (number treated as text)
email → 512-dim embedding
          ↓
Final Vector: 1536 dimensions total (for 1 sample)
```

### Numeric Method

Numeric columns standardized, categoricals one-hot encoded. Fastest option with minimal dimensions.

**Example:**
```
Original Data: [age: 30, score: 95, category: "A"]
          ↓
age → 1-dim normalized
score → 1-dim normalized
category (one-hot) → 3 dimensions (for A, B, C)
          ↓
Final Vector: 5 dimensions total (for 1 sample)
```

---

## Common Workflows with Vectors

### Workflow 5: Data → Vectors → LLM
```
1. POST /ingest → upload file, get job_id
2. POST /process/{job_id} → process data
3. GET /status/{job_id} → wait for completion
4. POST /vectors/{job_id}/generate → generate vectors (method: hybrid)
5. GET /vectors/{job_id}/download?format=h5 → download vector file
6. Feed vectors to your LLM for analysis/prediction
```

### Workflow 6: Quick Vector Inspection
```
1. POST /ingest → upload file
2. POST /process/{job_id} → process
3. GET /vectors/{job_id}/info → check vector dimensions before downloading
4. GET /vectors/{job_id}/download?format=pkl → download if suitable
```

---

## Vector Encoding Details

### Hybrid Method (Recommended)

**Text Columns:** 512-dimensional embeddings via HashingVectorizer (normalized L2)
**Numeric Columns:** Standardized to zero mean, unit variance
**Boolean Columns:** Binary (0 or 1)
**Categorical Columns:** One-hot encoded if ≤10 unique values, else embedded as text

**Example:**
```
Original Data: [name: "John", age: 30, active: true]
          ↓
name (text) → 512-dim embedding
age (numeric) → 1-dim normalized value
active (boolean) → 1-dim binary value
          ↓
Final Vector: 514 dimensions total (for 1 sample)
```

### Text-Only Method

All columns treated as text, generates 512-dimensional embeddings per column.

**Example:**
```
Original Data: [name: "John", age: 30, email: "john@example.com"]
          ↓
name → 512-dim embedding
age → 512-dim embedding (number treated as text)
email → 512-dim embedding
          ↓
Final Vector: 1536 dimensions total (for 1 sample)
```

### Numeric Method

Numeric columns standardized, categoricals one-hot encoded.

**Example:**
```
Original Data: [age: 30, score: 95, category: "A"]
          ↓
age → 1-dim normalized
score → 1-dim normalized
category (one-hot) → 3 dimensions (for A, B, C)
          ↓
Final Vector: 5 dimensions total (for 1 sample)
```

---

## Common Workflows with Vectors

### Workflow 5: Data → Vectors → LLM
```
1. POST /ingest → upload file, get job_id
2. POST /process/{job_id} → process data
3. GET /status/{job_id} → wait for completion
4. POST /vectors/{job_id}/generate → generate vectors (method: hybrid)
5. GET /vectors/{job_id}/download?format=h5 → download vector file
6. Feed vectors.h5 to your LLM for analysis/prediction
```

### Workflow 6: Quick Vector Inspection
```
1. POST /ingest → upload file
2. POST /process/{job_id} → process
3. GET /vectors/{job_id}/info → check vector dimensions before downloading
4. GET /vectors/{job_id}/download?format=pkl → download if suitable
```

### Workflow 7: Large Dataset Vector Processing
```
1. POST /ingest → upload file
2. POST /process/{job_id} → process
3. POST /vectors/{job_id}/generate?method=numeric → for memory efficiency
4. GET /vectors/{job_id}/download?format=h5 → download HDF5 (supports chunked reading)
5. Use h5py to read vectors in batches for processing
```

---

### Workflow 1: Upload → Process → Download
```
1. POST /ingest → get job_id
2. POST /process/{job_id} → start processing
3. GET /status/{job_id} → monitor progress
4. GET /result/{job_id}/download → get clean data
```

### Workflow 2: Upload → Process → Analyze → Download
```
1. POST /ingest → get job_id
2. POST /process/{job_id} → start processing
3. GET /status/{job_id} → wait for completion
4. GET /profile/{job_id} → view data profile
5. GET /errors/{job_id}/download → check errors
6. GET /result/{job_id}/download → get data
```

### Workflow 3: Format Conversion
```
1. POST /convert/csv-to-json → convert file
   OR
2. POST /convert/json-to-csv → convert data
```

### Workflow 4: Batch Job Management
```
1. GET /jobs → list all jobs
2. GET /jobs/{job_id} → check specific job
3. DELETE /jobs/{job_id} → cleanup old jobs
```

---

## Response Code Reference

| Code | Meaning | When |
|------|---------|------|
| `200` | OK | Request succeeded |
| `202` | Accepted | Resource still processing |
| `400` | Bad Request | Invalid request parameters |
| `404` | Not Found | Job/resource doesn't exist |
| `500` | Server Error | Internal server error |

---

## Rate Limiting

Currently no rate limiting. Implement as needed:
- Recommended: 100 requests/minute per API key
- File size limit: 100MB per upload

---

## Versioning

Current API Version: `1.0.0`

Future versions will be available at:
- `/api/v2/ingest`
- `/api/v2/process`
- etc.

---

## Support & Feedback

For issues or feature requests, contact the development team or file an issue in the repository.
