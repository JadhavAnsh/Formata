# Backend Issues & Feature Roadmap

This document outlines the current technical debt, identified bugs, and planned features for the Formata Backend.

## 🛠 Current Issues & Technical Debt

### 1. Persistence & Data Loss
- **Issue**: All job data is currently stored in-memory (`app/jobs/store.py`). 
- **Impact**: Restarting the server wipes all job history and progress.
- **Priority**: High (Moving to Appwrite)

### 2. Basic Authentication
- **Issue**: The current `X-API-Key` guard is static and doesn't support multiple users or personal job history.
- **Impact**: No true multi-tenancy or security for user data.
- **Priority**: High (Moving to Appwrite Auth)

### 3. SSE (Server-Sent Events) Placeholder
- **Issue**: The `/stream-errors/{job_id}` endpoint is a placeholder.
- **Impact**: Real-time error reporting is not functional.
- **Priority**: Medium

---

## 🚀 New Features & Implementation Plan

### 1. Appwrite Integration (Auth, DB, Storage)
- **Goal**: Centralize user management, metadata, and file storage using Appwrite.
- **Implementation Plan**:
  - **Auth**: Integrate Appwrite Server SDK in FastAPI to verify user sessions/JWTs.
  - **Databases**: Create a `jobs` collection to store processing parameters, status, and metadata.
  - **Storage**: Use Appwrite Buckets for both raw uploads and processed result files.
  - **Permissions**: Use Appwrite's ACLs to ensure users only access their own files and job data.

### 2. Backend-Driven Data Preview
- **Goal**: Add a `/preview/{job_id}` endpoint that pulls samples from Appwrite storage.
- **Implementation Plan**:
  - Create `app/api/preview.py`.
  - Fetch file sample from Appwrite Storage -> Parse first 100 rows -> Return JSON.

### 3. Real-Time Status via Appwrite
- **Goal**: Replace custom SSE with Appwrite's native Realtime events.
- **Implementation Plan**:
  - Backend updates the `jobs` document in Appwrite.
  - Frontend listens for document changes to update progress bars and status badges instantly.

### 4. Enhanced Vectorization Support
- **Goal**: Integrate vector generation with AI services.
- **Implementation Plan**:
  - Support for generating embeddings via OpenAI/HuggingFace.
  - Export vectors directly to external vector databases.

---

## 📅 Timeline
- **Week 1**: Appwrite SDK setup & Auth/Storage migration.
- **Week 2**: Backend Preview API & Realtime status updates.
- **Week 3**: AI Vectorization features & Webhooks.
