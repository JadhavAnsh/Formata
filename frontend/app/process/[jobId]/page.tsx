'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProgressBar } from '@/components/ProgressBar';
import { useJobStatus } from '@/hooks/useJobStatus';

interface ProcessPageProps {
  params: Promise<{
    jobId: string;
  }>;
}

export default function ProcessPage({ params }: ProcessPageProps) {
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);

  useEffect(() => {
    params.then((p) => setJobId(p.jobId));
  }, [params]);

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

