# Next.js + shadcn Project Structure

This project is a **data transformation tool** built on **Next.js (App Router)**, using the **shadcn/ui** components.
---

## Folder Layout

```bash
frontend/
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Landing page
│   │   │
│   │   ├── ingest/
│   │   │   └── page.tsx            # File upload/ingestion screen
│   │   │
│   │   ├── process/
│   │   │   └── [jobId]/
│   │   │       └── page.tsx        # Processing + progress
│   │   │
│   │   ├── result/
│   │   │   └── [jobId]/
│   │   │       └── page.tsx        # Clean output + errors
│   │   │
│   │   ├── convert/
│   │   │   └── page.tsx            # CSV ↔ JSON conversion UI
│   │   │
│   │   └── globals.css             # Tailwind + global styles
│   │
│   ├── components/
│   │   ├── ui/                     # shadcn/ui generated components live here[3][4]
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   └── ...others
│   │   │
│   │   ├── UploadBox.tsx           # Drag & drop file upload (uses ui components)
│   │   ├── ProgressBar.tsx         # Real-time progress display
│   │   ├── FilterForm.tsx          # Filters & parameters
│   │   ├── NormalizationForm.tsx   # Type conversion options
│   │   ├── ResultTable.tsx         # Before / After table
│   │   ├── ErrorTable.tsx          # Validation errors
│   │   ├── FileConverter.tsx       # CSV ↔ JSON conversion
│   │   └── Navbar.tsx              # Top navigation
│   │
│   ├── services/
│   │   ├── api.ts                  # Fetch/Axios wrapper
│   │   ├── ingest.service.ts
│   │   ├── process.service.ts
│   │   ├── status.service.ts
│   │   ├── result.service.ts
│   │   └── convert.service.ts
│   │
│   ├── hooks/
│   │   ├── useUpload.ts            # Upload logic
│   │   ├── useJobStatus.ts         # Poll job status
│   │   └── useResult.ts            # Fetch results
│   │
│   ├── types/
│   │   ├── job.ts                  # Job metadata and status
│   │   ├── dataset.ts              # Dataset models
│   │   └── error.ts                # Error/result schemas
│   │
│   └── lib/
│       └── utils.ts                # Utility functions (cn helper, etc.)
│
├── public/
│   ├── logo.svg
│   └── ...                         # Static assets
│
├── tailwind.config.ts
├── next.config.mjs
├── tsconfig.json
└── package.json
```

sequenceDiagram
    participant User
    participant IngestPage
    participant PreviewPage
    participant PreviewAPI
    participant ProcessPage
    participant ProcessAPI

    User->>IngestPage: Upload file
    IngestPage->>PreviewAPI: POST /ingest
    PreviewAPI-->>IngestPage: job_id
    IngestPage->>PreviewPage: Navigate to /preview/{job_id}
    PreviewPage->>PreviewAPI: GET /preview/{job_id}
    PreviewAPI->>PreviewAPI: Convert JSON to CSV if needed
    PreviewAPI-->>PreviewPage: CSV data (JSON format)
    PreviewPage->>PreviewPage: Display table
    User->>PreviewPage: Apply filters
    PreviewPage->>PreviewAPI: POST /preview/{job_id}/filter
    PreviewAPI->>PreviewAPI: Apply filters using filtering.py
    PreviewAPI-->>PreviewPage: Filtered data
    PreviewPage->>PreviewPage: Update table
    User->>PreviewPage: Click "Continue to Process"
    PreviewPage->>ProcessPage: Navigate with filters
    ProcessPage->>ProcessAPI: POST /process/{job_id} with filters