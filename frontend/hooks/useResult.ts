'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { resultService } from '@/services/result.service';
import { useAuth } from '@/context/AuthContext';
import { queryKeys } from '@/lib/queryKeys';
import { useJobStore } from '@/stores/jobStore';
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
  const { getJwt } = useAuth();
  const setResultInStore = useJobStore((state) => state.setResult);

  const query = useQuery<ProcessingResult, Error>({
    queryKey: queryKeys.jobResult(jobId as string),
    enabled: Boolean(jobId && enabled),
    queryFn: async () => {
      const jwt = await getJwt();
      if (!jwt) {
        throw new Error('No JWT available');
      }
      return resultService.getResults(jobId as string, jwt);
    },
    staleTime: 30_000,
    placeholderData: () =>
      jobId ? useJobStore.getState().results[jobId] ?? undefined : undefined,
  });

  useEffect(() => {
    if (query.data && jobId) {
      setResultInStore(jobId, query.data);
      onSuccess?.(query.data);
    }
  }, [query.data, jobId, setResultInStore, onSuccess]);

  useEffect(() => {
    if (query.error) {
      onError?.(query.error);
    }
  }, [query.error, onError]);

  return {
    result: query.data ?? null,
    isLoading: query.isPending && !query.isPlaceholderData,
    isFetching: query.isFetching,
    error: query.error ?? null,
    refetch: query.refetch,
  };
}

