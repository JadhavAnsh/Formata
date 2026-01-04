# Formata Backend API

A powerful, production-ready FastAPI backend for intelligent data processing, transformation, and quality assurance.

---

## 🚀 Overview

Formata Backend is a comprehensive data processing pipeline that handles file ingestion, transformation, cleaning, validation, and format conversion. Built with FastAPI, it provides asynchronous job processing, real-time progress tracking, and extensive data profiling capabilities.

### Key Features

- 📁 **Multi-format Support** - CSV, JSON, Excel, Markdown parsing
- 🔄 **Asynchronous Processing** - Background job processing with progress tracking
- 🧹 **Data Cleaning** - Duplicate removal, outlier detection, missing data handling
- ✅ **Quality Validation** - Schema validation and data quality checks
- 📊 **Data Profiling** - Comprehensive statistical analysis with ydata-profiling
- 🔐 **Secure API** - API key authentication for all protected endpoints
- 🎯 **Flexible Filtering** - Complex filtering rules with multiple operators
- 🔢 **Type Normalization** - Automatic data type inference and conversion
- 🤖 **Vector Generation** - OpenAI embeddings for ML/AI integration

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Architecture](#-architecture)
3. [API Endpoints](#-api-endpoints)
4. [Services](#-services)
5. [Configuration](#-configuration)
6. [Development](#-development)
7. [Testing](#-testing)

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- pip or conda

### Installation

1. **Clone and Navigate**
   ```bash
   cd backend
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file:
   ```env
   API_KEY=your_secure_api_key_here
   STORAGE_PATH=./storage
   MAX_FILE_SIZE=100  # MB
   ```

4. **Run the Server**
   ```bash
   uvicorn app.main:app --reload
   ```

   Server runs at: **http://localhost:8000**

### Quick Test
```bash
curl http://localhost:8000/health
```

---

## 🏗️ Architecture

### Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI entry point & CORS setup
│   │
│   ├── api/                    # API route handlers
│   │   ├── ingest.py           # POST /ingest - File upload
│   │   ├── process.py          # POST /process/{job_id} - Start processing
│   │   ├── status.py           # GET /status/{job_id} - Progress tracking
│   │   ├── result.py           # GET /result/{job_id} - Download results
│   │   ├── errors.py           # GET /errors/{job_id} - Error reports
│   │   ├── convert.py          # POST /convert - Format conversion
│   │   ├── jobs.py             # GET /jobs - List all jobs
│   │   ├── profile.py          # POST /profile/{job_id} - Data profiling
│   │   └── vectors.py          # POST /vectors/{job_id} - Generate embeddings
│   │
│   ├── services/               # Core business logic
│   │   ├── parser.py           # Multi-format file parsing
│   │   ├── normalization.py    # Type conversion & column standardization
│   │   ├── filtering.py        # Complex filtering engine
│   │   ├── noise.py            # Deduplication & outlier removal
│   │   ├── missing_data.py     # Missing value handling strategies
│   │   ├── validation.py       # Schema & quality validation
│   │   ├── conversion.py       # Format conversion (CSV ↔ JSON)
│   │   ├── vectorization.py    # OpenAI embeddings generation
│   │   └── pipeline.py         # Orchestrates full processing flow
│   │
│   ├── jobs/                   # Async job management
│   │   ├── store.py            # In-memory job state storage
│   │   └── worker.py           # Background task processor
│   │
│   ├── models/                 # Pydantic schemas
│   │   ├── request.py          # API request models
│   │   └── response.py         # API response models
│   │
│   ├── guards/                 # Security
│   │   └── auth.py             # API key authentication
│   │
│   ├── config/                 # Configuration
│   │   └── settings.py         # Environment variables
│   │
│   └── utils/                  # Helper functions
│       ├── file_utils.py
│       ├── date_utils.py
│       └── logger.py
│
├── storage/                    # File storage
│   ├── uploads/                # Raw uploaded files
│   ├── outputs/                # Processed clean data
│   ├── errors/                 # Error reports
│   └── reports/                # Profiling reports
│
├── tests/                      # Test suite
│   ├── test_parser.py
│   ├── test_filtering.py
│   ├── test_normalization.py
│   ├── test_noise.py
│   └── test_validation.py
│
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── API.md                      # Complete API documentation
└── IMPLEMENTATION.md           # Implementation details
```

### Data Flow Pipeline

```
┌─────────────────────┐
│   File Upload       │
│   (CSV/JSON/Excel)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Authentication    │
│   (API Key Guard)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Job Creation      │
│   (Store Job ID)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Background Worker │
│   (Async Process)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│   5-Step Pipeline:               │
│   1. Parse    → DataFrame        │
│   2. Normalize → Type Conversion │
│   3. Filter   → Apply Rules      │
│   4. Denoise  → Clean Data       │
│   5. Validate → Quality Check    │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────┐
│   Result Storage    │
│   (Outputs/Errors)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Result Retrieval  │
│   (Download/Stream) │
└─────────────────────┘
```

---

## 🔌 API Endpoints

### Health Check (Public)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status message |
| GET | `/health` | Health check |

### Data Operations (Protected)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/ingest` | Upload file and create job | ✅ |
| POST | `/process/{job_id}` | Start background processing | ✅ |
| GET | `/status/{job_id}` | Get job progress (0.0-1.0) | ✅ |
| GET | `/result/{job_id}` | Download processed data | ✅ |
| GET | `/errors/{job_id}` | Get error report | ✅ |
| POST | `/convert` | Convert CSV ↔ JSON | ✅ |
| GET | `/jobs` | List all jobs | ✅ |
| POST | `/profile/{job_id}` | Generate data profile report | ✅ |
| POST | `/vectors/{job_id}` | Generate embeddings | ✅ |

### Authentication

All protected endpoints require:
```
Headers:
  X-API-Key: your_api_key_here
```

📚 **Full API Documentation**: See [API.md](API.md)

---

## 🛠️ Services

### Core Processing Services

#### 1. **Parser Service** (`services/parser.py`)
- Parses CSV, JSON, Excel (.xlsx), and Markdown
- Automatic encoding detection
- Flexible delimiter handling
- Error tolerance and recovery

#### 2. **Normalization Service** (`services/normalization.py`)
- Automatic type inference (numeric, datetime, boolean)
- Column name standardization (snake_case)
- Missing value handling (drop, forward-fill, back-fill, mean, median, mode)
- Custom type enforcement

#### 3. **Filtering Service** (`services/filtering.py`)
- Complex filter expressions
- Operators: `>`, `<`, `>=`, `<=`, `==`, `!=`, `contains`, `starts_with`, `ends_with`, `in`, `not_in`
- Multiple filter combinations
- Column-level filtering

#### 4. **Noise Reduction Service** (`services/noise.py`)
- Duplicate removal (configurable columns)
- Outlier detection (IQR & Z-score methods)
- Statistical analysis

#### 5. **Validation Service** (`services/validation.py`)
- Schema validation
- Data quality checks
- Missing value detection
- Type consistency verification

#### 6. **Pipeline Service** (`services/pipeline.py`)
- Orchestrates all processing steps
- Progress tracking (0.0 → 1.0)
- Error collection and reporting
- Both sync and async execution

### Job Management

#### Job Store (`jobs/store.py`)
- In-memory job state management
- Job lifecycle: `pending` → `processing` → `completed`/`failed`
- Progress tracking with real-time updates
- Error history logging

#### Worker (`jobs/worker.py`)
- Asynchronous background processing
- Non-blocking execution
- Automatic error handling and recovery

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Security
API_KEY=your_secure_api_key_here

# OpenAI (Optional - for vectorization)
OPENAI_API_KEY=sk-your-openai-key-here

# Storage
STORAGE_PATH=./storage
MAX_FILE_SIZE=100  # Maximum upload size in MB

# Processing Limits
MAX_ROWS=1000000
TIMEOUT_SECONDS=600
```

### Settings (`config/settings.py`)

Managed through Pydantic settings:
- Environment variable loading
- Type validation
- Default values
- Validation on startup

---

## 👨‍💻 Development

### Running Locally

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
# Build image
docker build -t formata-backend .

# Run container
docker run -p 8000:8000 --env-file .env formata-backend
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_filtering.py

# Verbose output
pytest -v
```

### Test Structure

```
tests/
├── test_parser.py           # File parsing tests
├── test_filtering.py        # Filter logic tests
├── test_normalization.py    # Type conversion tests
├── test_noise.py            # Deduplication tests
├── test_validation.py       # Quality checks
└── test_conversion.py       # Format conversion tests
```

---

## 📦 Dependencies

Key packages:
- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Pandas** - Data manipulation
- **Pydantic** - Data validation
- **OpenPyXL** - Excel support
- **ydata-profiling** - Data profiling
- **OpenAI** - Embeddings generation
- **scikit-learn** - ML utilities

See [requirements.txt](requirements.txt) for complete list.

---

## 🔍 Additional Resources

- **[API.md](API.md)** - Complete API documentation with examples
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Implementation details and wiring
- **[Postman Collection](Formata_API.postman_collection.json)** - API testing collection

---

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

---

## 📄 License

This project is part of the Formata data processing platform.

---

## 🆘 Support

For issues and questions:
- Check [API.md](API.md) for endpoint usage
- Review [IMPLEMENTATION.md](IMPLEMENTATION.md) for architecture details
- Run tests to verify setup: `pytest`

---

**Built with ❤️ By Const_Coders**