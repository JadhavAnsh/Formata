'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ProgressBar } from '@/components/ProgressBar';
import { useJobStatus } from '@/hooks/useJobStatus';
import { processService } from '@/services/process.service';
import type { FilterParams } from '@/services/preview.service';

interface ProcessPageProps {
  params: Promise<{
    jobId: string;
  }>;
}

export default function ProcessPage({ params }: ProcessPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [jobId, setJobId] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterParams | null>(null);
  const [processingStarted, setProcessingStarted] = useState(false);

  useEffect(() => {
    params.then((p) => setJobId(p.jobId));
  }, [params]);

  useEffect(() => {
    // Extract filters from URL params
    const filtersParam = searchParams.get('filters');
    if (filtersParam) {
      try {
        const parsedFilters = JSON.parse(filtersParam);
        setFilters(parsedFilters);
      } catch (e) {
        console.error('Failed to parse filters from URL:', e);
      }
    }
  }, [searchParams]);

  const { job, isLoading, error } = useJobStatus({
    jobId,
    pollInterval: 2000,
    onStatusChange: (job) => {
      if (job.status === 'completed') {
        router.push(`/result/${job.id}`);
      } else if (job.status === 'failed' || job.status === 'cancelled') {
        router.push(`/result/${job.id}`);
      }
    },
  });

  // Start processing if job is pending and filters are available
  useEffect(() => {
    if (jobId && job && job.status === 'pending' && filters && !processingStarted) {
      const startProcessing = async () => {
        try {
          setProcessingStarted(true);
          await processService.startProcessing(jobId, { filters });
        } catch (err) {
          console.error('Failed to start processing:', err);
          setProcessingStarted(false);
        }
      };
      startProcessing();
    }
  }, [jobId, job, filters, processingStarted]);

  if (!jobId) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-4xl">
      <h1 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6">Processing Job</h1>
      <p className="text-muted-foreground mb-4 sm:mb-6 break-all">Job ID: {jobId}</p>
      
      {job && (
        <div className="space-y-4">
          <ProgressBar
            progress={job.progress || 0}
            status={job.status}
          />
          <p className="text-sm text-muted-foreground">
            Status: {job.status}
          </p>
        </div>
      )}
      
      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
      
      {error && (
        <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
          {error.message}
        </div>
      )}
    </div>
  );
}

