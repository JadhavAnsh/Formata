'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';

interface ErrorReportPageProps {
  params: Promise<{
    job_id: string;
  }>;
}

export default function ErrorReportPage({ params }: ErrorReportPageProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [isIframeLoading, setIsIframeLoading] = useState(true);

  useEffect(() => {
    params.then((p) => setJobId(p.job_id));
  }, [params]);

  useEffect(() => {
    const applyTheme = () => {
      setTheme(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    };

    applyTheme();

    const observer = new MutationObserver(applyTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setIsIframeLoading(true);
  }, [jobId, theme]);

  const iframeSrc = useMemo(() => {
    if (!jobId) return null;
    const searchParams = new URLSearchParams({ theme });
    return `/error-report/${jobId}/file?${searchParams.toString()}`;
  }, [jobId, theme]);

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
            <Button className="w-full sm:w-auto" asChild>
              <a href={`/error-report/${jobId}/pdf?theme=${theme}`}>Download PDF</a>
            </Button>
            
          </div>
        </div>

        <div className="border rounded-lg overflow-hidden bg-background relative">
          {isIframeLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm z-10">
              <p className="text-muted-foreground">Loading report...</p>
            </div>
          )}
          {iframeSrc && (
            <iframe
              title="Error report"
              src={iframeSrc}
              className="w-full h-[75vh]"
              sandbox="allow-scripts allow-same-origin"
              onLoad={() => setIsIframeLoading(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
