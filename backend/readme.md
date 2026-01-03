backend/
├── app/
│   ├── main.py                 # FastAPI entry point
│   │
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── ingest.py           # /ingest
│   │   ├── process.py          # /process/{job_id}
│   │   ├── status.py           # /status/{job_id}
│   │   ├── result.py           # /result/{job_id}
│   │   ├── errors.py           # /errors/{job_id}
│   │   └── convert.py          # /convert
│   │
│   ├── services/               # Core logic (IMPORTANT)
│   │   ├── __init__.py
│   │   ├── parser.py           # CSV, JSON, Excel, MD parsing
│   │   ├── normalization.py    # Type conversion
│   │   ├── filtering.py        # Filters & parameters
│   │   ├── noise.py            # Deduplication, outliers
│   │   ├── validation.py       # Schema validation
│   │   ├── conversion.py       # CSV ↔ JSON
│   │   ├── vectorization.py    # Embeddings (optional)
│   │   └── pipeline.py         # Full processing flow
│   │
│   ├── jobs/                   # Async job handling
│   │   ├── __init__.py
│   │   ├── store.py            # In-memory job store
│   │   └── worker.py           # Background processing
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── request.py          # Input schemas
│   │   └── response.py         # Output schemas
│   │
│   ├── utils/                  # Helpers
│   │   ├── __init__.py
│   │   ├── file_utils.py
│   │   ├── date_utils.py
│   │   ├── logger.py
│   │   └── constants.py
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py         # Env variables
│
├── storage/
│   ├── uploads/                # Raw files
│   ├── outputs/                # Clean structured data
│   └── errors/                 # Error reports
│
├── requirements.txt
├── .env
└── README.md