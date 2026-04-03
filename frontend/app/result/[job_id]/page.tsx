'use client';

import { useEffect, useState } from 'react';

import { ErrorTable } from '@/components/ErrorTable';
import { ResultView } from '@/components/ResultView';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useResult } from '@/hooks/useResult';
import { resultService } from '@/services/result.service';
import { Download, FileText, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface ResultPageProps {
  params: Promise<{
    job_id: string;
  }>;
}

function clampToPercent(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, value));
}

function formatTimingStep(value: any): string {
  if (value && typeof value === 'object') {
    if (typeof value.duration_formatted === 'string' && value.duration_formatted) {
      return value.duration_formatted;
    }
    if (typeof value.duration_seconds === 'number' && Number.isFinite(value.duration_seconds)) {
      return `${value.duration_seconds.toFixed(2)}s`;
    }
  }

  if (typeof value === 'number' && Number.isFinite(value)) {
    return `${value.toFixed(2)}s`;
  }

  return String(value ?? '');
}

export default function ResultPage({ params }: ResultPageProps) {
  const [job_id, setjob_id] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    params.then((p) => setjob_id(p.job_id));
  }, [params]);

  const { result, isLoading, error } = useResult({
    jobId: job_id,
    enabled: !!job_id,
  });

  const canDownloadClean = Boolean(result?.afterData?.rows?.length || result?.afterData?.rowCount);

  if (!job_id) {
    return (
      <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-6xl">
        <div className="flex items-center justify-center p-8">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  const totalRows =
    result?.afterData?.rowCount ??
    result?.beforeData?.rowCount ??
    result?.afterData?.rows?.length ??
    result?.beforeData?.rows?.length ??
    0;

  const errorCount = result?.errors?.length ?? 0;
  
  // Use consistency_score from API if available, otherwise fallback to calculated score
  const qualityScore = clampToPercent(
    result?.metadata?.quality_score?.consistency_score ??
    result?.metadata?.summary?.quality_score?.consistency_score ??
    (totalRows > 0 ? Math.round(100 - (errorCount / totalRows) * 100) : 0)
  );

  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (qualityScore / 100) * circumference;
  const timingDetails = result?.metadata?.timing_details;
  const totalTiming =
    timingDetails?.total_formatted ??
    timingDetails?.total_time ??
    (typeof result?.metadata?.processing_time === 'number'
      ? `${result.metadata.processing_time.toFixed(2)}s`
      : undefined);

  return (
    <div className="min-h-screen mt-22 pt-24 sm:pt-28 pb-16 px-4 sm:px-6 relative" suppressHydrationWarning>
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(124,58,237,0.18)_0%,transparent_55%)]" />
      <div className="max-w-6xl mx-auto">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="size-9 rounded-full bg-primary/15 ring-1 ring-primary/25 flex items-center justify-center">
                <div className="size-3 rounded-full bg-primary" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-semibold leading-tight">Processing Complete</h1>
                <p className="text-sm sm:text-base text-muted-foreground">
                  Your dataset is now AI-ready and structured.
                </p>
              </div>
            </div>

            <div className="text-muted-foreground text-sm mb-6">
              <span className="opacity-80">Job ID:</span> <span className="break-all">{job_id}</span>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                className="w-full sm:w-auto sm:flex-1"
                disabled={!canDownloadClean || isLoading}
                onClick={() => {
                  if (!job_id) return;
                  setActionError(null);
                  resultService.downloadResult(job_id).catch((err) => {
                    console.error('Download failed:', err);
                    const message = err instanceof Error ? err.message : 'Failed to download result file.';
                    setActionError(message);
                  });
                }}
              >
                <Download className="mr-2 size-4" />
                Download Clean Dataset
              </Button>
              <Button
                variant="outline"
                className="w-full sm:w-auto sm:flex-1"
                onClick={() => {
                  if (!job_id) return;
                  router.push(`/error-report/${job_id}`);
                }}
              >
                <FileText className="mr-2 size-4" />
                View Error Report
              </Button>
            </div>

            <Button
              variant="secondary"
              className="w-full mt-3"
              onClick={() => {
                if (!job_id) return;
                setActionError(null);
                resultService.downloadVectorPkl(job_id).catch((err) => {
                  console.error('Download failed:', err);
                  const message = err instanceof Error ? err.message : 'Failed to download vector file.';
                  setActionError(message);
                });
              }}
            >
              <Download className="mr-2 size-4" />
              Download Vector .pkl
            </Button>

            <Button
              variant="secondary"
              className="w-full mt-3"
              onClick={() => {
                if (!job_id) return;
                setActionError(null);
                resultService.downloadVectorH5(job_id).catch((err) => {
                  console.error('Download failed:', err);
                  const message = err instanceof Error ? err.message : 'Failed to download vector file.';
                  setActionError(message);
                });
              }}
            >
              <Download className="mr-2 size-4" />
              Download Vector .h5
            </Button>

            {isLoading && <p className="text-muted-foreground mt-6">Loading results...</p>}

            {error && (
              <div className="mt-6 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                {error.message}
              </div>
            )}

            {actionError && (
              <div className="mt-3 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                {actionError}
              </div>
            )}
          </div>

          <Card className="h-full">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-6">
                {/* <div>
                  <div className="text-xs text-muted-foreground">Total Records</div>
                  <div className="text-2xl font-semibold">{totalRows}</div>
                </div> */}
                {/* <div className="text-xs text-muted-foreground">{errorCount} issues</div> */}
              </div>

              <div className="flex flex-col items-center justify-center gap-4">
                <div className="relative size-44">
                  <svg viewBox="0 0 120 120" className="size-44 -rotate-90">
                    <circle
                      cx="60"
                      cy="60"
                      r={radius}
                      fill="none"
                      stroke="currentColor"
                      className="text-muted/40"
                      strokeWidth="10"
                    />
                    <circle
                      cx="60"
                      cy="60"
                      r={radius}
                      fill="none"
                      stroke="currentColor"
                      className="text-emerald-500"
                      strokeWidth="10"
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      strokeDashoffset={dashOffset}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <div className="text-3xl font-semibold tabular-nums">{qualityScore}%</div>
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Quality</div>
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-sm font-medium">Data Quality Score</div>
                  <div className="text-xs text-muted-foreground">
                    {qualityScore >= 90
                      ? 'Excellent quality. Ready for ML training.'
                      : qualityScore >= 70
                        ? 'Good quality. Review minor issues.'
                        : 'Needs review. Check validation errors.'}
                  </div>
                </div>

                {(timingDetails || result?.metadata?.processing_time !== undefined) && (
                  <div suppressHydrationWarning className="w-full pt-4 border-t">
                    <div className="text-sm font-medium mb-3">Processing Time</div>
                    <div className="space-y-2 text-xs text-muted-foreground">
                      {totalTiming && (
                        <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                          <span className="font-medium text-foreground">Total Time:</span>
                          <span suppressHydrationWarning className="font-semibold text-primary">
                            {totalTiming}
                          </span>
                        </div>
                      )}
                      {timingDetails?.steps && Object.entries(timingDetails.steps).length > 0 && (
                        <div className="space-y-1 mt-2">
                          <div className="font-medium text-foreground text-[11px]">Steps:</div>
                          {Object.entries(timingDetails.steps).map(([step, time]: [string, any]) => (
                            <div key={step} suppressHydrationWarning className="flex items-center justify-between pl-2 pr-1">
                              <span className="capitalize text-xs">{step.replace(/_/g, ' ')}:</span>
                              <span className="text-xs text-muted-foreground">{formatTimingStep(time)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-10">
          <div className="flex items-center justify-end mb-4">
            {/* <h2 className="text-lg sm:text-xl font-semibold">Check Validation Errors</h2> */}
            <Link href="/ingest" className="text-sm text-primary hover:underline inline-flex items-center gap-2">
              <RotateCcw className="size-4" />
              Process another file
            </Link>
          </div>

          {result?.afterData?.rows?.length ? (
            <Card>
              <CardContent className="p-0">
                <div className="px-4 sm:px-6 py-4 border-b bg-muted/30 flex items-center justify-between">
                  <div className="text-sm font-semibold">Visual Diff: Raw vs Processed</div>
                  <div className="text-xs text-muted-foreground">
                    {result.afterData?.rowCount ?? result.afterData.rows.length} rows
                  </div>
                </div>
                <div className="p-4 sm:p-6">
                  <ResultView
                    beforeRows={result.beforeData?.rows || []}
                    afterRows={result.afterData.rows || []}
                  />
                </div>
              </CardContent>
            </Card>
          ) : null}

          {result?.errors?.length ? (
            <div className="mt-8" suppressHydrationWarning>
              <Card>
                <CardContent className="p-0">
                  <div className="px-4 sm:px-6 py-4 border-b bg-muted/30 flex items-center justify-between">
                    <div className="text-sm font-semibold">Validation Errors</div>
                    <div className="text-xs text-muted-foreground">{result.errors.length} issues</div>
                  </div>
                  <div className="p-4 sm:p-6">
                    <ErrorTable errors={result.errors} />
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

