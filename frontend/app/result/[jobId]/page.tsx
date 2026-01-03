'use client';

import { useEffect, useState } from 'react';
import { ResultTable } from '@/components/ResultTable';
import { ErrorTable } from '@/components/ErrorTable';
import { useResult } from '@/hooks/useResult';

interface ResultPageProps {
  params: Promise<{
    jobId: string;
  }>;
}

export default function ResultPage({ params }: ResultPageProps) {
  const [jobId, setJobId] = useState<string | null>(null);

  useEffect(() => {
    params.then((p) => setJobId(p.jobId));
  }, [params]);

  const { result, isLoading, error } = useResult({ jobId });

  if (!jobId) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <h1 className="text-3xl font-bold mb-6">Processing Results</h1>
      <p className="text-muted-foreground mb-6">Job ID: {jobId}</p>
      
      {isLoading && <p className="text-muted-foreground">Loading results...</p>}
      
      {error && (
        <div className="mb-6 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
          {error.message}
        </div>
      )}
      
      {result && (
        <div className="space-y-8">
          {result.beforeData && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Before Processing</h2>
              <ResultTable beforeData={result.beforeData.rows} />
            </div>
          )}
          
          {result.afterData && (
            <div>
              <h2 className="text-xl font-semibold mb-4">After Processing</h2>
              <ResultTable afterData={result.afterData.rows} />
            </div>
          )}
          
          {result.errors && result.errors.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Validation Errors</h2>
              <ErrorTable errors={result.errors} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

