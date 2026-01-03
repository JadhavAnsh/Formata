'use client';

import { useState, useEffect, useCallback } from 'react';
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

  const fetchStatus = useCallback(async () => {
    if (!jobId || !enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await statusService.getJobStatus(jobId);
      setJob(result);
      onStatusChange?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch job status');
      setError(error);
    } finally {
      setIsLoading(false);
    }
  }, [jobId, enabled, onStatusChange]);

  useEffect(() => {
    if (!jobId || !enabled) return;

    // Fetch immediately
    fetchStatus();

    // Set up polling if job is not completed or failed
    const interval = setInterval(() => {
      if (job && (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled')) {
        clearInterval(interval);
        return;
      }
      fetchStatus();
    }, pollInterval);

    return () => clearInterval(interval);
  }, [jobId, enabled, pollInterval, fetchStatus, job]);

  return {
    job,
    isLoading,
    error,
    refetch: fetchStatus,
  };
}

