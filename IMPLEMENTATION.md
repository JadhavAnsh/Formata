# Master Implementation Plan: Formata + Appwrite

This document serves as the technical blueprint for migrating Formata to a BaaS (Backend-as-a-Service) architecture using **Appwrite** and implementing advanced data features.

---

## 🏗 Phase 1: Authentication & User Management (Appwrite Auth)

### **Backend (FastAPI)**
- [x] Install `appwrite` Server SDK.
- [x] Create `app/guards/appwrite_auth.py` to verify JWT tokens from the frontend.
- [x] Replace `verify_api_key` dependency with `verify_appwrite_session`.
- [x] Update `JobStore` (or Repository) to associate `user_id` with every job.

### **Frontend (Next.js)**
- [x] Install `appwrite` Web SDK.
- [x] Create `lib/appwrite.ts` configuration.
- [x] Implement `AuthContext` for global session management.
- [x] Build Login and Register pages.
- [ ] Protect routes using a Higher-Order Component (HOC) or Middleware.

### **Verification & Tests**
- **Unit Test**: Verify `appwrite_auth.py` correctly extracts and validates JWTs.
- **Integration Test**: Attempt to access `/jobs` without a valid session (should return 401).
- **Integration Test**: Attempt to access `/jobs` with a valid session (should return 200).

---

## 📦 Phase 2: Scalable Storage & Persistence (Appwrite Storage & DB)

### **Backend (FastAPI)**
- [x] Create `app/services/appwrite_storage.py` to handle file uploads/downloads to Appwrite Buckets.
- [x] Create `app/services/appwrite_db.py` to manage the `jobs` collection.
- [x] Refactor `worker.py` to:
    - [x] Download raw file from Appwrite.
    - [x] Process data locally.
    - [x] Upload result file back to Appwrite.
    - [x] Update Appwrite document with progress and status.

### **Frontend (Next.js)**
- [x] Refactor `UploadBox.tsx` (via `ingestService`) to upload directly to Appwrite Storage bucket.
- [x] Store metadata (filename, size, type) in the Appwrite `jobs` collection (via backend `ingest` call).

### **Verification & Tests**
- [x] **Unit Test**: Mock Appwrite Storage to verify file chunking and upload logic.
- [x] **Integration Test**: Verify a processing job correctly updates the status field in the Appwrite database.
- [ ] **Cleanup Test**: Ensure files are deleted from Appwrite Buckets when a job is deleted.

---

## 🔍 Phase 3: Data Preview (Client-Side Optimized)

### **Backend (FastAPI)**
- [x] New endpoint: `GET /preview/{job_id}` (Implemented but unused by frontend for performance).
- [x] Logic to stream a sample from Appwrite Storage.

### **Frontend (Next.js)**
- [x] Optimized Preview flow: Use client-side parsing for instant preview of large files.
- [x] Defer Appwrite upload until the user clicks "Continue to Process".
- [x] Maintain security by passing JWT during the final upload/register step.

### **Verification & Tests**
- [x] **Performance**: Verify that a 50MB file previews instantly without waiting for network upload.
- [x] **Security**: Ensure Appwrite Storage upload only happens for authenticated users.

---

## ⚡ Phase 4: Real-time Status & Dashboard

### **Frontend (Next.js)**
- [ ] Create `DashboardPage` (`/dashboard`) to list user jobs.
- [ ] Implement Appwrite Realtime subscription in `ProcessingProgress.tsx`.
- [ ] Listen for changes in the `jobs` collection for the specific `job_id`.

### **Verification & Tests**
- **E2E Test**: Start a job and verify the progress bar moves in real-time without page refreshes.
- **Manual Test**: Verify the dashboard updates automatically when a new job is created from another tab.

---

## 🤖 Phase 5: Advanced Vectorization & AI Export

### **Backend (FastAPI)**
- [ ] Enhance `vectors.py` with multi-provider support (OpenAI, local embeddings).
- [ ] Save generated `.pkl` and `.h5` files back to Appwrite Buckets.
- [ ] Update job metadata with vector dimensions and method used.

### **Frontend (Next.js)**
- [ ] Build a "Vectorization Options" modal.
- [ ] Add download links for vector files in the `ResultPage`.

### **Verification & Tests**
- **Unit Test**: Verify vector output shape matches the expected dimensions for "hybrid" and "text" modes.
- **Performance Test**: Measure time taken to vectorize 10,000 rows and ensure it doesn't timeout.

---

## 🛡 Phase 6: Security & Hardening

### **Common Tasks**
- [ ] Set up Appwrite ACLs: `read("user:{USER_ID}")`, `write("user:{USER_ID}")`.
- [ ] Implement CORS whitelist for production domain.
- [ ] Add input sanitization for all filter expressions.

### **Verification & Tests**
- **Security Test**: Attempt to access `job_A` using `user_B`'s credentials (should return 403/404).
- **Security Test**: Verify that processed files in Appwrite Storage are not publicly accessible.
