'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ProcessingProgress } from '@/components/ProcessingProgress';
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
  const [simulatedProgress, setSimulatedProgress] = useState(0);
  const [simulatedStage, setSimulatedStage] = useState('Preparing pipeline');

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

  const shouldSimulate = useMemo(() => {
    const value = searchParams.get('simulate');
    return value === '1' || value === 'true';
  }, [searchParams]);

  const { job, isLoading, error } = useJobStatus({
    jobId,
    pollInterval: 2000,
    enabled: !shouldSimulate,
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
    if (shouldSimulate) return;
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
  }, [jobId, job, filters, processingStarted, shouldSimulate]);

  useEffect(() => {
    if (!jobId || !shouldSimulate) return;

    let cancelled = false;
    const startedAt = Date.now();
    const durationMs = 6500;

    const stageForProgress = (progress: number) => {
      if (progress < 12) return 'Preparing pipeline';
      if (progress < 32) return 'Loading input + schema';
      if (progress < 58) return 'Cleaning + normalizing values';
      if (progress < 82) return 'Validating records';
      if (progress < 99) return 'Finalizing outputs';
      return 'Done';
    };

    const tick = () => {
      if (cancelled) return;
      const elapsed = Date.now() - startedAt;
      const nextProgress = Math.min(100, Math.round((elapsed / durationMs) * 100));
      setSimulatedProgress(nextProgress);
      setSimulatedStage(stageForProgress(nextProgress));

      if (nextProgress >= 100) {
        setTimeout(() => {
          if (!cancelled) router.push(`/result/${jobId}?demo=1`);
        }, 450);
      }
    };

    tick();
    const interval = window.setInterval(tick, 120);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [jobId, shouldSimulate, router]);

  if (!jobId) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-4xl">
      <h1 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6">Processing Job</h1>

      {shouldSimulate ? (
        <ProcessingProgress jobId={jobId} progress={simulatedProgress} stage={simulatedStage} />
      ) : (
        <>
          <p className="text-muted-foreground mb-4 sm:mb-6 break-all">Job ID: {jobId}</p>
      
          {job && (
            <div className="space-y-4">
              <ProgressBar progress={job.progress || 0} status={job.status} />
              <p className="text-sm text-muted-foreground">Status: {job.status}</p>
            </div>
          )}
      
          {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
      
          {error && (
            <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
              {error.message}
            </div>
          )}
        </>
      )}
    </div>
  );
}

