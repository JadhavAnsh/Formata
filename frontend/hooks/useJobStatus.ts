'use client';

import { useState, useEffect, useCallback } from 'react';
import { statusService } from '@/services/status.service';
import { useAuth } from '@/context/AuthContext';
import { client } from '@/lib/appwrite';
import type { Job } from '@/types/job';

interface UseJobStatusOptions {
  jobId: string | null;
  pollInterval?: number; // milliseconds (fallback if Realtime fails)
  enabled?: boolean;
  onStatusChange?: (job: Job) => void;
}

export function useJobStatus({
  jobId,
  pollInterval = 5000, // Longer interval for fallback
  enabled = true,
  onStatusChange,
}: UseJobStatusOptions) {
  const { getJwt } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!jobId || !enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const jwt = await getJwt();
      if (!jwt) throw new Error('No JWT available');
      
      const result = await statusService.getJobStatus(jobId, jwt);
      setJob(result);
      onStatusChange?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch job status');
      setError(error);
    } finally {
      setIsLoading(false);
    }
  }, [jobId, enabled, onStatusChange, getJwt]);

  useEffect(() => {
    if (!jobId || !enabled) return;

    // 1. Fetch initial state
    fetchStatus();

    // 2. Set up Appwrite Realtime subscription
    const databaseId = process.env.NEXT_PUBLIC_APPWRITE_DATABASE_ID || '';
    const collectionId = process.env.NEXT_PUBLIC_APPWRITE_JOBS_COLLECTION_ID || '';
    
    if (!databaseId || !collectionId) {
      console.warn('Realtime configuration missing (DB or Collection ID)');
      return;
    }

    // Subscribe to this specific document
    const unsubscribe = client.subscribe(
      `databases.${databaseId}.collections.${collectionId}.documents.${jobId}`,
      (response) => {
        // Appwrite Realtime returns the raw document
        const payload = response.payload as any;
        
        // Normalize the payload to match Job interface
        const updatedJob: Job = {
          id: payload.$id,
          job_id: payload.$id,
          filename: payload['file-name'] || payload.file_name,
          status: payload.status,
          progress: payload.progress !== undefined 
            ? (payload.progress <= 1 ? payload.progress * 100 : payload.progress)
            : 0,
          createdAt: payload.created_at || payload.$createdAt,
          updatedAt: payload.completed_at || payload.$updatedAt,
          metadata: typeof payload.metadata === 'string' ? JSON.parse(payload.metadata) : payload.metadata,
        };
        
        setJob(updatedJob);
        onStatusChange?.(updatedJob);
        
        console.log('Realtime update received:', updatedJob.status, updatedJob.progress);
      }
    );

    // 3. Keep polling as a fallback (optional, but safer)
    const interval = setInterval(() => {
      if (job && (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled')) {
        clearInterval(interval);
        return;
      }
      // Only fetch if we haven't had an update in a while (e.g. 10s)
      // or just keep it as a backup
      fetchStatus();
    }, pollInterval);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [jobId, enabled, pollInterval, fetchStatus]);

  return {
    job,
    isLoading,
    error,
    refetch: fetchStatus,
  };
}
