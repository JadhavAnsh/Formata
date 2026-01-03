frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Landing page
│   │
│   ├── ingest/
│   │   └── page.tsx            # File upload screen
│   │
│   ├── process/
│   │   └── [jobId]/
│   │       └── page.tsx        # Processing + progress
│   │
│   ├── result/
│   │   └── [jobId]/
│   │       └── page.tsx        # Clean output + errors
│   │
│   └── convert/
│       └── page.tsx            # CSV ↔ JSON conversion
│
├── components/
│   ├── UploadBox.tsx           # Drag & drop file upload
│   ├── ProgressBar.tsx         # Real-time progress
│   ├── FilterForm.tsx          # Filters & parameters
│   ├── NormalizationForm.tsx   # Type conversion options
│   ├── ResultTable.tsx         # Before / After table
│   ├── ErrorTable.tsx          # Validation errors
│   ├── FileConverter.tsx       # Convert CSV ↔ JSON
│   └── Navbar.tsx
│
├── services/
│   ├── api.ts                  # Axios / fetch wrapper
│   ├── ingest.service.ts
│   ├── process.service.ts
│   ├── status.service.ts
│   ├── result.service.ts
│   └── convert.service.ts
│
├── hooks/
│   ├── useUpload.ts            # Upload logic
│   ├── useJobStatus.ts         # Poll job status
│   └── useResult.ts            # Fetch results
│
├── types/
│   ├── job.ts
│   ├── dataset.ts
│   └── error.ts
│
├── styles/
│   └── globals.css             # Tailwind / global styles
│
├── public/
│   └── logo.svg
│
├── tailwind.config.ts
├── next.config.js
├── tsconfig.json
└── package.json
