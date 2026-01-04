'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ProgressBar } from '@/components/ProgressBar';
import { useJobStatus } from '@/hooks/useJobStatus';
import { processService } from '@/services/process.service';
import type { FilterParams } from '@/services/preview.service';

interface ProcessPageProps {
  params: {
    job_id: string;
  };
}

export default function ProcessPage({ params }: ProcessPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const job_id = params.job_id;
  const [processingStarted, setProcessingStarted] = useState(false);

  const filters: FilterParams | null = useMemo(() => {
    const filtersParam = searchParams.get('filters');
    if (!filtersParam) return null;
    try {
      return JSON.parse(filtersParam);
    } catch {
      return null;
    }
  }, [searchParams]);

  const { job, isLoading, error } = useJobStatus({
    jobId: job_id,
    pollInterval: 2000,
    enabled: !!job_id,
    onStatusChange: (job) => {
      const jobIdToUse = job.job_id || job.id || job_id;
      if (job.status === 'completed') {
        router.push(`/result/${jobIdToUse}`);
      } else if (job.status === 'failed' || job.status === 'cancelled') {
        router.push(`/result/${jobIdToUse}`);
      }
    },
  });

  // Start processing if job is pending
  useEffect(() => {
    if (job_id && job && job.status === 'pending' && !processingStarted) {
      const startProcessing = async () => {
        try {
          setProcessingStarted(true);
          // Send filters if available, otherwise use defaults
          await processService.startProcessing(job_id, {
            filters: filters || undefined,
            normalize: true,
            remove_duplicates: true,
            remove_outliers: false,
          });
        } catch (err) {
          console.error('Failed to start processing:', err);
          setProcessingStarted(false);
        }
      };
      startProcessing();
    }
  }, [job_id, job, filters, processingStarted]);

  // Progress is already normalized to 0-100 by statusService
  const progress = job?.progress !== undefined ? job.progress : 0;
  const status = job?.status || 'pending';

  if (!job_id) {
    return (
      <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-4xl">
        <div className="p-4 bg-destructive/10 text-destructive rounded-md">
          <h2 className="text-lg font-semibold mb-2">Error</h2>
          <p>Job ID not found in URL</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-4xl">
      <h1 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6">Processing Job</h1>

      <p className="text-muted-foreground mb-4 sm:mb-6 break-all">Job ID: {job_id}</p>

      <div className="space-y-4">
        {isLoading && !job && (
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <p className="text-sm text-muted-foreground">Loading job status...</p>
          </div>
        )}

        {job && (
          <>
            <ProgressBar progress={progress} status={status} />
            <div className="space-y-2">
              <p className="text-sm font-medium">
                Status: <span className="capitalize">{status}</span>
              </p>
              {job.filename && (
                <p className="text-sm text-muted-foreground">File: {job.filename}</p>
              )}
              {job.progress !== undefined && (
                <p className="text-sm text-muted-foreground">Progress: {Math.round(progress)}%</p>
              )}
              {job.error && (
                <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                  Error: {job.error}
                </div>
              )}
            </div>
          </>
        )}

        {processingStarted && !job && (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Starting processing...</p>
            <ProgressBar progress={0} status="pending" />
          </div>
        )}

        {!job && !isLoading && !processingStarted && (
          <p className="text-sm text-muted-foreground">Waiting to start processing...</p>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-destructive/10 text-destructive rounded-md">
          <h3 className="font-semibold mb-1">Error Loading Job Status</h3>
          <p className="text-sm">{error.message}</p>
          <p className="text-xs mt-2 opacity-75">Job ID: {job_id}</p>
          <p className="text-xs opacity-75">Check the browser console for more details.</p>
        </div>
      )}
    </div>
  );
}

