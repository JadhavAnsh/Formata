'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { ApiRequestError } from '@/services/api';
import { statusService } from '@/services/status.service';
import type { Job } from '@/types/job';

interface UseJobStatusOptions {
  jobId: string | null;
  pollInterval?: number; // milliseconds
  enabled?: boolean;
  onStatusChange?: (job: Job) => void;
}

export function useJobStatus({
  jobId,
  pollInterval = 2000,
  enabled = true,
  onStatusChange,
}: UseJobStatusOptions) {
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const onStatusChangeRef = useRef<typeof onStatusChange>(onStatusChange);
  const currentStatusRef = useRef<Job['status'] | null>(null);
  const isFetchingRef = useRef(false);

  useEffect(() => {
    onStatusChangeRef.current = onStatusChange;
  }, [onStatusChange]);

  const fetchStatus = useCallback(async () => {
    if (!jobId || !enabled || isFetchingRef.current) return;

    isFetchingRef.current = true;
    setIsLoading(true);
    setError(null);

    try {
      const result = await statusService.getJobStatus(jobId);
      currentStatusRef.current = result.status;
      setJob(result);
      onStatusChangeRef.current?.(result);
    } catch (err) {
      const isNotFound = err instanceof ApiRequestError && err.status === 404;
      if (isNotFound) {
        currentStatusRef.current = 'failed';
      }

      const error =
        err instanceof Error
          ? err
          : new Error('Failed to fetch job status');
      setError(error);
    } finally {
      isFetchingRef.current = false;
      setIsLoading(false);
    }
  }, [jobId, enabled]);

  useEffect(() => {
    if (!jobId || !enabled) return;

    currentStatusRef.current = null;

    // Fetch immediately
    fetchStatus();

    // Set up polling if job is not completed or failed
    const interval = setInterval(() => {
      const status = currentStatusRef.current;
      if (status && (status === 'completed' || status === 'failed' || status === 'cancelled')) {
        clearInterval(interval);
        return;
      }
      fetchStatus();
    }, pollInterval);

    return () => clearInterval(interval);
  }, [jobId, enabled, pollInterval, fetchStatus]);

  return {
    job,
    isLoading,
    error,
    refetch: fetchStatus,
  };
}

