'use client';

import { useState, useEffect, useCallback } from 'react';
import { resultService } from '@/services/result.service';
import type { ProcessingResult } from '@/services/result.service';

interface UseResultOptions {
  jobId: string | null;
  enabled?: boolean;
  onSuccess?: (result: ProcessingResult) => void;
  onError?: (error: Error) => void;
}

export function useResult({
  jobId,
  enabled = true,
  onSuccess,
  onError,
}: UseResultOptions) {
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchResult = useCallback(async () => {
    if (!jobId || !enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await resultService.getResults(jobId);
      setResult(data);
      onSuccess?.(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch results');
      setError(error);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [jobId, enabled, onSuccess, onError]);

  useEffect(() => {
    if (jobId && enabled) {
      fetchResult();
    }
  }, [jobId, enabled, fetchResult]);

  return {
    result,
    isLoading,
    error,
    refetch: fetchResult,
  };
}

