import { ErrorTable } from '@/components/ErrorTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Download, FileText, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { headers } from 'next/headers';

interface ResultPageProps {
  params: {
    job_id: string;
  };
}

function clampToPercent(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, value));
}

async function getApiBaseUrl() {
  const fromEnv = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
  if (fromEnv.startsWith('http://') || fromEnv.startsWith('https://')) return fromEnv;

  const h = await headers();
  const proto = h.get('x-forwarded-proto') || 'http';
  const host = h.get('x-forwarded-host') || h.get('host') || 'localhost:3000';
  const origin = `${proto}://${host}`;

  if (!fromEnv) return origin;
  return `${origin}${fromEnv.startsWith('/') ? '' : '/'}${fromEnv}`;
}

async function getResults(jobId: string) {
  const apiBaseUrl = await getApiBaseUrl();
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || '';

  const response = await fetch(`${apiBaseUrl}/status/${jobId}`, {
    headers: {
      ...(apiKey && { 'X-API-Key': apiKey }),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch results: ${response.statusText}`);
  }

  const job = (await response.json()) as any;
  const resultData = job.result || job.metadata?.result;

  if (!resultData) {
    throw new Error('Result data not available yet. Job may still be processing.');
  }

  return {
    jobId: job.job_id || job.id || jobId,
    beforeData: resultData.beforeData || resultData.before_data,
    afterData: resultData.afterData || resultData.after_data || resultData.data,
    errors: Array.isArray(resultData.errors)
      ? resultData.errors.map((err: any) => ({
          row: err.row || err.row_index || 0,
          column: err.column || err.column_name || '',
          message: err.message || err.error || String(err),
          value: err.value,
          code: err.code || 'VALIDATION_ERROR',
          severity: err.severity || 'error',
        }))
      : resultData.errors,
    metadata: resultData.metadata || job.metadata,
  };
}

export default async function ResultPage({ params }: ResultPageProps) {
  const job_id = params.job_id;

  let result: Awaited<ReturnType<typeof getResults>> | null = null;
  let errorMessage: string | null = null;

  try {
    result = await getResults(job_id);
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : 'Failed to load results';
  }

  const totalRows =
    result?.afterData?.rowCount ??
    result?.beforeData?.rowCount ??
    result?.afterData?.rows?.length ??
    result?.beforeData?.rows?.length ??
    0;

  const errorCount = result?.errors?.length ?? 0;
  const qualityScore = clampToPercent(totalRows > 0 ? Math.round(100 - (errorCount / totalRows) * 100) : 0);

  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (qualityScore / 100) * circumference;

  return (
    <div className="min-h-screen pt-24 sm:pt-28 pb-16 px-4 sm:px-6 relative">
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
                <p className="text-sm sm:text-base text-muted-foreground">Your dataset is now AI-ready and structured.</p>
              </div>
            </div>

            <div className="text-muted-foreground text-sm mb-6">
              <span className="opacity-80">Job ID:</span> <span className="break-all">{job_id}</span>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button className="w-full sm:w-auto sm:flex-1" asChild>
                <a href={`/result/${job_id}/download`}>
                  <Download className="mr-2 size-4" />
                  Download Clean Dataset
                </a>
              </Button>

              {errorCount > 0 ? (
                <Button variant="outline" className="w-full sm:w-auto sm:flex-1" asChild>
                  <Link href={`/error-report/${job_id}`}>
                    <FileText className="mr-2 size-4" />
                    View Error Report
                  </Link>
                </Button>
              ) : (
                <Button variant="outline" className="w-full sm:w-auto sm:flex-1" disabled>
                  <FileText className="mr-2 size-4" />
                  View Error Report
                </Button>
              )}
            </div>

            <Button variant="secondary" className="w-full mt-3" asChild>
              <a href={`/result/${job_id}/vectors`}>
                <Download className="mr-2 size-4" />
                Download Vector .pkl
              </a>
            </Button>

            {errorMessage && (
              <div className="mt-6 p-3 bg-destructive/10 text-destructive rounded-md text-sm">{errorMessage}</div>
            )}
          </div>

          <Card className="h-full">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <div className="text-xs text-muted-foreground">Total Records</div>
                  <div className="text-2xl font-semibold">{totalRows}</div>
                </div>
                <div className="text-xs text-muted-foreground">{errorCount} issues</div>
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
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg sm:text-xl font-semibold">Check Validation Errors</h2>
            <Link href="/ingest" className="text-sm text-primary hover:underline inline-flex items-center gap-2">
              <RotateCcw className="size-4" />
              Process another file
            </Link>
          </div>

          {result?.errors?.length ? (
            <div className="mt-8">
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

