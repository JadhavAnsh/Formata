# Formata

<div align="center">

**Intelligent Data Transformation & Quality Assurance Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.1-black?logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Documentation](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 Overview

Formata is a modern, production-ready data processing platform that transforms messy data into clean, validated datasets. Built with FastAPI and Next.js, it provides a complete suite of tools for data ingestion, cleaning, transformation, validation, and quality assurance.

Whether you're dealing with inconsistent formats, missing values, duplicates, or outliers, Formata's intelligent pipeline handles it all with real-time progress tracking and comprehensive error reporting.

### Why Formata?

- ⚡ **Fast & Scalable** - Asynchronous processing with job queuing
- 🎨 **Modern UI** - Beautiful, responsive interface built with Next.js and shadcn/ui
- 🔧 **Flexible** - Supports multiple file formats and custom transformations
- 📊 **Insightful** - Advanced data profiling with statistical analysis
- 🔐 **Secure** - API key authentication and safe file handling
- 🤖 **AI-Ready** - OpenAI embeddings generation for ML/AI workflows

---

## ✨ Features

### Data Processing
- **Multi-format Support** - CSV, JSON, Excel, Markdown
- **Smart Parsing** - Automatic delimiter detection and type inference
- **Data Cleaning** - Duplicate removal, outlier detection, missing data imputation
- **Type Normalization** - Automatic data type conversion and validation
- **Advanced Filtering** - Complex rules with multiple operators (equals, contains, range, etc.)
- **Schema Validation** - Ensure data integrity with custom validation rules

### Data Quality & Profiling
- **Quality Scoring** - Comprehensive data quality metrics
- **Statistical Analysis** - Powered by ydata-profiling
- **Error Reporting** - Detailed validation error reports with line-level details
- **Before/After Comparison** - Visual diff of transformations

### AI & ML Integration
- **Vector Generation** - OpenAI embeddings for semantic search and ML
- **LLM-Ready Outputs** - Optimized formats for AI/ML pipelines

### Developer Experience
- **RESTful API** - Well-documented endpoints with OpenAPI/Swagger
- **Real-time Progress** - WebSocket-style job status polling
- **Postman Collection** - Ready-to-use API testing collection
- **Comprehensive Testing** - Extensive test suite for all core features

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm/yarn/pnpm
- **Git**

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/JadhavAnsh/Formata.git
cd Formata
```

#### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
API_KEY=your_secure_api_key_here
STORAGE_PATH=./storage
MAX_FILE_SIZE=100
OPENAI_API_KEY=your_openai_key  # Optional, for vector generation
EOF

# Start the server
uvicorn app.main:app --reload
```

Backend will be running at **http://localhost:8000**

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or
yarn install
# or
pnpm install

# Create environment file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your_secure_api_key_here
EOF

# Start the development server
npm run dev
# or
yarn dev
# or
pnpm dev
```

Frontend will be running at **http://localhost:3000**

#### 4. Access the Application

Open your browser and navigate to:
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🏗️ Architecture

Formata follows a modern microservices architecture with clear separation between frontend and backend:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                    (Next.js + React)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Ingest  │  │  Process │  │  Result  │  │  Convert │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                       │ REST API
        ┌──────────────┴──────────────────────────────────────┐
        │                   Backend                           │
        │                (FastAPI + Python)                   │
        │  ┌──────────────────────────────────────────────┐  │
        │  │           API Layer (Routes)                 │  │
        │  │  /ingest  /process  /result  /convert  etc.  │  │
        │  └──────────────────┬───────────────────────────┘  │
        │  ┌──────────────────┴───────────────────────────┐  │
        │  │           Services Layer                     │  │
        │  │  Parser │ Normalizer │ Filter │ Profiler    │  │
        │  └──────────────────┬───────────────────────────┘  │
        │  ┌──────────────────┴───────────────────────────┐  │
        │  │           Job Processing                     │  │
        │  │  Queue Management │ Background Workers      │  │
        │  └──────────────────────────────────────────────┘  │
        │  ┌──────────────────────────────────────────────┐  │
        │  │           Storage Layer                      │  │
        │  │  Uploads │ Outputs │ Reports │ Errors       │  │
        │  └──────────────────────────────────────────────┘  │
        └─────────────────────────────────────────────────────┘
```

### Backend Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   ├── services/         # Core business logic
│   ├── models/           # Request/Response models
│   ├── jobs/             # Job queue & worker
│   ├── guards/           # Authentication middleware
│   ├── config/           # Configuration & settings
│   └── utils/            # Helper functions
├── storage/              # File storage
└── tests/                # Test suite
```

### Frontend Structure

```
frontend/
├── app/                  # Next.js pages (App Router)
├── components/           # React components
│   ├── ui/              # shadcn/ui components
│   └── *.tsx            # Custom components
├── services/            # API service layer
├── hooks/               # Custom React hooks
├── types/               # TypeScript definitions
└── utils/               # Utility functions
```

---

## 📖 API Documentation

### Core Endpoints

#### Health & Status
- `GET /` - API status
- `GET /health` - Health check

#### Data Operations
- `POST /ingest` - Upload and ingest data file
- `POST /process/{job_id}` - Start data processing pipeline
- `GET /status/{job_id}` - Get job processing status
- `GET /result/{job_id}` - Download processed results
- `GET /errors/{job_id}` - Retrieve error reports

#### Advanced Features
- `POST /convert` - Convert between formats (CSV ↔ JSON)
- `POST /profile/{job_id}` - Generate comprehensive data profile
- `POST /vectors/{job_id}` - Generate OpenAI embeddings
- `GET /jobs` - List all processing jobs

### Authentication

All protected endpoints require an API key:

```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/jobs
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Postman Collection**: Available in `backend/Formata_API.postman_collection.json`

For detailed API documentation, see [backend/API.md](backend/API.md)

---

## 🔧 Configuration

### Backend Configuration

Create a `.env` file in the `backend/` directory:

```env
# Required
API_KEY=your_secure_api_key_here

# Storage Configuration
STORAGE_PATH=./storage
MAX_FILE_SIZE=100  # in MB

# Optional - For vector generation
OPENAI_API_KEY=sk-your-openai-key

# Optional - Server settings
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

### Frontend Configuration

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your_secure_api_key_here
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_conversion.py

# Run with coverage
pytest --cov=app tests/

# Run specific test categories
pytest tests/test_filtering.py -v
pytest tests/test_normalization.py -v
```

### Test Coverage

The backend includes comprehensive tests for:
- ✅ File parsing (CSV, JSON, Excel, Markdown)
- ✅ Data type normalization and conversion
- ✅ Filtering with complex rules
- ✅ Missing data handling
- ✅ Outlier detection and removal
- ✅ Quality score calculation
- ✅ Schema validation

---

## 🐳 Docker Deployment

### Backend Docker

```bash
cd backend

# Build image
docker build -t formata-backend .

# Run container
docker run -p 8000:8000 \
  -e API_KEY=your_api_key \
  -v $(pwd)/storage:/app/storage \
  formata-backend
```

### Docker Compose (Coming Soon)

Full-stack deployment with frontend and backend:

```bash
docker-compose up -d
```

---

## 📊 Usage Examples

### 1. Upload and Process Data

```bash
# Upload file
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your_api_key" \
  -F "file=@data.csv"
  
# Response: {"job_id": "abc123"}

# Start processing
curl -X POST http://localhost:8000/process/abc123 \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "remove_duplicates": true,
    "handle_missing": "drop",
    "filters": [
      {
        "column": "age",
        "operator": "greater_than",
        "value": 18
      }
    ]
  }'

# Check status
curl http://localhost:8000/status/abc123 \
  -H "X-API-Key: your_api_key"

# Download results
curl http://localhost:8000/result/abc123 \
  -H "X-API-Key: your_api_key" \
  --output processed_data.csv
```

### 2. Data Profiling

```bash
curl -X POST http://localhost:8000/profile/abc123 \
  -H "X-API-Key: your_api_key"
```

### 3. Format Conversion

```bash
curl -X POST http://localhost:8000/convert \
  -H "X-API-Key: your_api_key" \
  -F "file=@data.csv" \
  -F "output_format=json"
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **Language**: Python 3.10+
- **Data Processing**: Pandas, NumPy
- **Profiling**: ydata-profiling
- **AI/ML**: OpenAI, scikit-learn
- **Validation**: Pydantic
- **Server**: Uvicorn

### Frontend
- **Framework**: Next.js 16.1 (App Router)
- **Language**: TypeScript 5.0
- **UI Library**: React 19.2
- **Component System**: shadcn/ui
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Animations**: Motion

---

## 📁 Project Structure

```
Formata/
├── backend/                    # FastAPI backend
│   ├── app/                   # Application code
│   │   ├── api/              # API routes
│   │   ├── services/         # Business logic
│   │   ├── models/           # Data models
│   │   ├── jobs/             # Job processing
│   │   ├── guards/           # Auth middleware
│   │   ├── config/           # Configuration
│   │   └── utils/            # Utilities
│   ├── storage/              # File storage
│   ├── tests/                # Test suite
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend container
│
├── frontend/                  # Next.js frontend
│   ├── app/                  # Pages (App Router)
│   ├── components/           # React components
│   ├── services/             # API services
│   ├── hooks/                # Custom hooks
│   ├── types/                # TypeScript types
│   ├── utils/                # Utilities
│   └── package.json          # Node dependencies
│
├── LICENSE                    # MIT License
└── README.md                  # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Data profiling by [ydata-profiling](https://github.com/ydataai/ydata-profiling)
- Icons by [Lucide](https://lucide.dev/)

---

## 📞 Support

For issues, questions, or suggestions:

- **GitHub Issues**: [Create an issue](https://github.com/JadhavAnsh/Formata/issues)
- **Documentation**: See [backend/API.md](backend/API.md) and [backend/IMPLEMENTATION.md](backend/IMPLEMENTATION.md)

---

<div align="center">

**Made with ❤️ by Team Const_Coders**

⭐ Star this repo if you find it helpful!

</div>
