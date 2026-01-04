'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { resultService } from '@/services/result.service';

interface ErrorReportPageProps {
  params: Promise<{
    job_id: string;
  }>;
}

export default function ErrorReportPage({ params }: ErrorReportPageProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then((p) => setJobId(p.job_id));
  }, [params]);

  const fetchReport = useCallback(async (id: string) => {
    setHtmlContent(null);
    setError(null);
    setIsLoading(true);

    try {
      const report = await resultService.getProfileReport(id);
      setHtmlContent(report.content);
    } catch (err) {
      console.error('Failed to fetch profile report:', err);
      setError(err instanceof Error ? err.message : 'Failed to load error report');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (jobId) {
      fetchReport(jobId);
    }
  }, [jobId, fetchReport]);

  if (!jobId) {
    return (
      <div className="min-h-screen pt-24 sm:pt-28 pb-16 px-4 sm:px-6 relative">
        <div className="flex items-center justify-center p-8">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 sm:pt-28 pb-16 px-4 sm:px-6 relative">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(124,58,237,0.12)_0%,transparent_55%)]" />
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold leading-tight">Error Report</h1>
            <p className="text-sm text-muted-foreground break-all">
              <span className="opacity-80">Job ID:</span> {jobId}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
            <Button variant="outline" className="w-full sm:w-auto" asChild>
              <Link href={`/result/${jobId}`}>Back to Results</Link>
            </Button>
          </div>
        </div>

        <div className="border rounded-lg overflow-hidden bg-background">
          {isLoading && (
            <div className="flex items-center justify-center h-[75vh]">
              <p className="text-muted-foreground">Loading report...</p>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-[75vh]">
              <p className="text-destructive">{error}</p>
            </div>
          )}
          {htmlContent && (
            <iframe
              title="Error report"
              srcDoc={htmlContent}
              className="w-full h-[75vh]"
              sandbox="allow-scripts allow-same-origin"
            />
          )}
        </div>
      </div>
    </div>
  );
}
