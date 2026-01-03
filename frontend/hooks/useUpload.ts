'use client';

import { useState, useCallback } from 'react';
import { ingestService } from '@/services/ingest.service';
import type { Job } from '@/types/job';

interface UseUploadOptions {
  onSuccess?: (job: Job) => void;
  onError?: (error: Error) => void;
}

export function useUpload(options?: UseUploadOptions) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [job, setJob] = useState<Job | null>(null);

  const upload = useCallback(
    async (file: File, uploadOptions?: {
      filters?: Record<string, any>;
      normalization?: Record<string, any>;
    }) => {
      setIsUploading(true);
      setError(null);

      try {
        const result = await ingestService.uploadFile(file, uploadOptions);
        setJob(result);
        options?.onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Upload failed');
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setIsUploading(false);
      }
    },
    [options]
  );

  return {
    upload,
    isUploading,
    error,
    job,
  };
}

