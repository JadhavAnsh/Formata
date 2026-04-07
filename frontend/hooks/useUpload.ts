'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ingestService } from '@/services/ingest.service';
import { useAuth } from '@/context/AuthContext';
import { queryKeys } from '@/lib/queryKeys';
import { useJobStore } from '@/stores/jobStore';
import type { Job } from '@/types/job';

interface UseUploadOptions {
  onSuccess?: (job: Job) => void;
  onError?: (error: Error) => void;
}

export function useUpload(options?: UseUploadOptions) {
  const { getJwt } = useAuth();
  const queryClient = useQueryClient();
  const upsertJob = useJobStore((state) => state.upsertJob);
  const setCurrentJobId = useJobStore((state) => state.setCurrentJobId);

  const mutation = useMutation<Job, Error, {
    file: File;
    uploadOptions?: {
      filters?: Record<string, any>;
      normalization?: Record<string, any>;
    };
  }>({
    mutationFn: async ({ file, uploadOptions }) => {
      const jwt = await getJwt();
      if (!jwt) {
        throw new Error('No JWT available');
      }
      return ingestService.uploadFile(file, jwt, uploadOptions);
    },
    onSuccess: (job) => {
      upsertJob(job);
      const id = job.job_id || job.id;
      if (id) {
        queryClient.setQueryData(queryKeys.jobStatus(id), job);
      }
      setCurrentJobId(id || null);
      options?.onSuccess?.(job);
    },
    onError: (error) => {
      options?.onError?.(error);
    },
  });

  const upload = async (
    file: File,
    uploadOptions?: {
      filters?: Record<string, any>;
      normalization?: Record<string, any>;
    }
  ) => mutation.mutateAsync({ file, uploadOptions });

  return {
    upload,
    isUploading: mutation.isPending,
    error: mutation.error,
    job: mutation.data ?? null,
  };
}

