'use client';

import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { resultService } from '@/services/result.service';
import { statusService } from '@/services/status.service';
import { useAuth } from '@/context/AuthContext';
import { client } from '@/lib/appwrite';
import { queryKeys } from '@/lib/queryKeys';
import { useJobStore } from '@/stores/jobStore';
import type { Job } from '@/types/job';

interface UseJobStatusOptions {
  jobId: string | null;
  pollInterval?: number;
  enabled?: boolean;
  onStatusChange?: (job: Job) => void;
}

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled']);

function normalizeRealtimeJob(payload: any): Job {
  return {
    id: payload.$id,
    job_id: payload.$id,
    filename: payload['file-name'] || payload.file_name,
    status: payload.status,
    progress:
      payload.progress !== undefined
        ? payload.progress <= 1
          ? payload.progress * 100
          : payload.progress
        : 0,
    createdAt: payload.created_at || payload.$createdAt,
    updatedAt: payload.completed_at || payload.$updatedAt,
    metadata: typeof payload.metadata === 'string' ? JSON.parse(payload.metadata) : payload.metadata,
  };
}

export function useJobStatus({
  jobId,
  pollInterval = 5000,
  enabled = true,
  onStatusChange,
}: UseJobStatusOptions) {
  const { getJwt } = useAuth();
  const queryClient = useQueryClient();
  const upsertJob = useJobStore((state) => state.upsertJob);
  const setCurrentJobId = useJobStore((state) => state.setCurrentJobId);

  const query = useQuery<Job, Error>({
    queryKey: queryKeys.jobStatus(jobId as string),
    enabled: Boolean(jobId && enabled),
    queryFn: async () => {
      const jwt = await getJwt();
      if (!jwt) {
        throw new Error('No JWT available');
      }
      return statusService.getJobStatus(jobId as string, jwt);
    },
    staleTime: 0,
    placeholderData: () =>
      jobId ? useJobStore.getState().jobs[jobId] ?? undefined : undefined,
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      if (!enabled || !jobId || (status && TERMINAL_STATUSES.has(status))) {
        return false;
      }
      return pollInterval;
    },
  });

  useEffect(() => {
    if (jobId) {
      setCurrentJobId(jobId);
    }
  }, [jobId, setCurrentJobId]);

  useEffect(() => {
    if (query.data) {
      upsertJob(query.data);
      onStatusChange?.(query.data);
    }
  }, [query.data, upsertJob, onStatusChange]);

  useEffect(() => {
    if (!jobId || !enabled) return;

    const databaseId = process.env.NEXT_PUBLIC_APPWRITE_DATABASE_ID || '';
    const collectionId = process.env.NEXT_PUBLIC_APPWRITE_JOBS_COLLECTION_ID || '';

    if (!databaseId || !collectionId) {
      return;
    }

    const unsubscribe = client.subscribe(
      `databases.${databaseId}.collections.${collectionId}.documents.${jobId}`,
      (response) => {
        const updatedJob = normalizeRealtimeJob(response.payload);
        upsertJob(updatedJob);
        queryClient.setQueryData(queryKeys.jobStatus(jobId), updatedJob);
        if (TERMINAL_STATUSES.has(updatedJob.status)) {
          void getJwt().then((jwt) => {
            if (!jwt) return;
            queryClient.prefetchQuery({
              queryKey: queryKeys.jobResult(jobId),
              queryFn: () => resultService.getResults(jobId, jwt),
            });
          });
        }
        onStatusChange?.(updatedJob);
      }
    );

    return () => {
      unsubscribe();
    };
  }, [jobId, enabled, queryClient, upsertJob, onStatusChange, getJwt]);

  return {
    job: query.data ?? null,
    /** Initial load only — avoids full-page “loading” on each poll or background refetch */
    isLoading: query.isPending && !query.isPlaceholderData,
    isFetching: query.isFetching,
    error: query.error ?? null,
    refetch: query.refetch,
  };
}
