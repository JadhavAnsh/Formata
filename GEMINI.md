# GEMINI.md - Formata Project Context

## 🎯 Project Overview
**Formata** is an Intelligent Data Transformation & Quality Assurance Platform designed to transform messy data into clean, validated datasets. It features a modern microservices-inspired architecture with a FastAPI backend and a Next.js frontend, leveraging **Appwrite** for Backend-as-a-Service (BaaS) capabilities including Authentication, Storage, and Database management.

### Key Technologies
- **Backend**: FastAPI (Python 3.10+), Pandas, NumPy, ydata-profiling, OpenAI, Pydantic, Appwrite Server SDK.
- **Frontend**: Next.js 15+ (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui, Appwrite Web SDK.
- **Infrastructure**: Docker, Appwrite (Auth, DB, Storage).

---

## 🏗 Architecture & Structure

### Backend (`/backend`)
Follows a modular service-oriented structure:
- `app/api/`: RESTful route handlers (ingest, process, status, result, etc.).
- `app/services/`: Core business logic (normalization, filtering, parsing, Appwrite integrations).
- `app/models/`: Pydantic schemas for request/response validation.
- `app/jobs/`: Background job processing and status management.
- `app/guards/`: Authentication middleware (Appwrite JWT verification).
- `app/config/`: Configuration management using `pydantic-settings`.
- `storage/`: Local cache for file processing (uploads, outputs, reports).

### Frontend (`/frontend`)
Modern Next.js application using the App Router:
- `app/`: Page components and layouts (login, register, dashboard, process, result).
- `components/`: UI components (shadcn/ui + custom components like `UploadBox`, `PreviewTable`).
- `services/`: API client layer for interacting with the FastAPI backend.
- `hooks/`: Custom React hooks for job status polling and data fetching.
- `context/`: `AuthContext` for Appwrite session management.

---

## 🚀 Building and Running

### Backend Setup
1. **Environment**: Create `backend/.env` based on `backend/app/config/settings.py`.
   ```env
   APPWRITE_ENDPOINT=http://localhost/v1
   APPWRITE_PROJECT_ID=...
   APPWRITE_API_KEY=...
   OPENAI_API_KEY=...
   ```
2. **Install**: `pip install -r requirements.txt` (inside a virtual environment).
3. **Run**: `uvicorn app.main:app --reload --port 8000`.
4. **Test**: `pytest` in the `backend/` directory.

### Frontend Setup
1. **Environment**: Create `frontend/.env.local`.
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_APPWRITE_ENDPOINT=...
   NEXT_PUBLIC_APPWRITE_PROJECT_ID=...
   ```
2. **Install**: `npm install`.
3. **Run**: `npm run dev` (starts on http://localhost:3000).

---

## 🛠 Development Conventions

### Coding Style
- **Python**: Follow PEP 8. Use type hints for all function signatures. Use Pydantic models for API data structures.
- **TypeScript**: Strict typing is required. Prefer functional components and React Hooks.
- **API Design**: All protected endpoints must use the `verify_appwrite_session` dependency.

### Error Handling
- **Backend**: Use `HTTPException` for API errors. Log errors using the utility logger in `app/utils/logger.py`.
- **Frontend**: Implement graceful error states in UI components and use the `ErrorTable` for processing errors.

### Testing
- **Backend**: Every service or API change should be accompanied by a test in `backend/tests/`.
- **Reproducibility**: Before fixing a bug, create a reproduction test case.

---

## 📝 Key Files
- `backend/app/main.py`: Entry point for the FastAPI application.
- `backend/app/guards/appwrite_auth.py`: JWT session verification logic.
- `backend/app/services/pipeline.py`: Main data processing orchestration logic.
- `frontend/lib/appwrite.ts`: Appwrite client configuration.
- `IMPLEMENTATION.md`: Roadmap and phase-wise migration status.
- `API.md`: Detailed backend API documentation.
