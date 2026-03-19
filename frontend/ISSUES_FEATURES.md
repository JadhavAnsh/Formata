# Frontend Issues & Feature Roadmap

This document outlines the current UI/UX challenges, identified bugs, and planned features for the Formata Frontend.

## 🛠 Current Issues & Technical Debt

### 1. Inefficient Upload Workflow
- **Issue**: Files are uploaded for preview locally and then again for processing.
- **Impact**: High bandwidth usage; slow UX.
- **Priority**: High (Moving to Appwrite Storage)

### 2. Lack of User Sessions
- **Issue**: No login system; jobs are ephemeral.
- **Impact**: Users cannot return to previous work or manage their account.
- **Priority**: High (Moving to Appwrite Auth)

---

## 🚀 New Features & Implementation Plan

### 1. Appwrite Integration (Auth & SDK)
- **Goal**: Add user accounts and direct-to-cloud uploads.
- **Implementation Plan**:
  - **Auth**: Add Login, Register, and Account Profile pages using Appwrite Web SDK.
  - **Storage**: Upload files directly to Appwrite Buckets from `UploadBox.tsx`. 
  - **State Management**: Persist the `job_id` (Appwrite Document ID) across sessions.

### 2. Backend-Powered Preview
- **Goal**: Fetch preview samples from the backend instead of parsing locally.
- **Implementation Plan**:
  - `PreviewPage` calls `GET /preview/{job_id}` after the initial upload to Appwrite.
  - Eliminates `sessionStorage` limits and client-side parsing failures.

### 3. Real-Time Processing Dashboard
- **Goal**: Use Appwrite Realtime to show live progress.
- **Implementation Plan**:
  - Subscribe to `databases.[DB_ID].collections.[COLL_ID].documents.[DOC_ID]` for status changes.
  - Show live error logs streamed from the backend via Appwrite.

### 4. Job History & Management
- **Goal**: A dashboard to view all processed files.
- **Implementation Plan**:
  - Create `/dashboard` to list all jobs from the Appwrite `jobs` collection.
  - Support deleting jobs, re-downloading results, and viewing reports.

### 5. Vectorization UI
- **Goal**: UI for configuring and downloading AI vectors.
- **Implementation Plan**:
  - Add configuration panel for Vectorization methods.
  - Direct download links for `.pkl` and `.h5` files from Appwrite.

---

## 📅 Timeline
- **Week 1**: Appwrite Auth UI & Cloud Upload integration.
- **Week 2**: Dashboard view & Realtime status updates.
- **Week 3**: Vectorization UI & Advanced Filtering UI.
