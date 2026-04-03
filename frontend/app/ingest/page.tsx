'use client';

import { UploadBox } from '@/components/UploadBox';
import { ingestService } from '@/services/ingest.service';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

// Store files in memory using a Map
export const fileCache = new Map<string, File>();
// Keep legacy map for backward compatibility with existing preview page fallback.
export const parsedPreviewCache = new Map<string, any>();

export default function IngestPage() {
  const router = useRouter();
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [statusText, setStatusText] = useState('Uploading file...');

  const handleFileSelect = async (file: File) => {
    if (isParsing) return;

    setIsParsing(true);
    setError(null);
    
    try {
      setStatusText('Generating sampled preview...');

      const ingestResponse = await ingestService.uploadFile(file, { preview_rows: 100 });
      const jobId = ingestResponse.job_id || ingestResponse.id;
      if (!jobId) {
        throw new Error('Job ID not found in ingest response');
      }

      fileCache.set(jobId, file);

      const fileData = {
        previewId: jobId,
        fileName: file.name,
        fileType: file.name.split('.').pop()?.toLowerCase(),
        fileSize: file.size,
        uploadedAt: new Date().toISOString(),
        parsedData: ingestResponse.preview
          ? {
              records: ingestResponse.preview.records || [],
              columns: ingestResponse.preview.metadata?.columns || [],
              totalRows: ingestResponse.preview.metadata?.totalRows,
            }
          : undefined,
      };

      if (fileData.parsedData) {
        parsedPreviewCache.set(jobId, fileData.parsedData);
      }

      sessionStorage.setItem(`preview_data_${jobId}`, JSON.stringify(fileData));
      router.push(`/preview/${jobId}`);
    } catch (err) {
      console.error('File parsing failed:', err);
      setError(err instanceof Error ? err : new Error('Failed to parse file'));
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-4xl flex flex-col items-center">
      <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold italic mb-4 sm:mb-6 text-center">
        MESSY DATA TO STRUCTURED DATA
      </h1>
      <p className="text-center text-gray-500 mb-6 sm:mb-8 text-base sm:text-lg leading-relaxed max-w-2xl">
        Upload raw data from CSV, Excel, or JSON and let Formata clean, normalize, and structure it automatically.
      </p>
      
      <div className="w-full max-w-2xl">
        <UploadBox
          onFileSelect={handleFileSelect}
          disabled={isParsing}
        />
      </div>
      
      {isParsing && (
        <p className="mt-4 text-sm text-gray-500 center">
          {statusText}
        </p>
      )}
      
      {error && (
        <p className="mt-4 text-sm text-red-500 center">
          {error.message}
        </p>
      )}
    </div>
  );
}

