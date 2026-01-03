'use client';

import { useEffect, useMemo, useState } from 'react';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ResultTable } from '@/components/ResultTable';
import { ErrorTable } from '@/components/ErrorTable';
import { useResult } from '@/hooks/useResult';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Download, RotateCcw } from 'lucide-react';
import type { ProcessingResult } from '@/services/result.service';

interface ResultPageProps {
  params: Promise<{
    jobId: string;
  }>;
}

function downloadJson(filename: string, value: unknown) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function clampToPercent(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, value));
}

export default function ResultPage({ params }: ResultPageProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const isDemo = searchParams.get('demo') === '1';

  useEffect(() => {
    params.then((p) => setJobId(p.jobId));
  }, [params]);

  const demoResult: ProcessingResult | null = useMemo(() => {
    if (!jobId) return null;

    const beforeRows = [
      { id: '001', email: 'alice@example.com', age: '29', signup_date: '2024-10-01', active: 'true' },
      { id: '002', email: 'bob@example.com', age: 'not_a_number', signup_date: '2024/11/03', active: 'yes' },
      { id: '003', email: 'cara@example.com', age: '41', signup_date: '2024-12-09', active: 'false' },
      { id: '004', email: 'dan@example.com', age: '34', signup_date: 'invalid_date', active: 'true' },
    ];

    const afterRows = [
      { id: 1, email: 'alice@example.com', age: 29, signup_date: '2024-10-01', active: true },
      { id: 2, email: 'bob@example.com', age: null, signup_date: '2024-11-03', active: true },
      { id: 3, email: 'cara@example.com', age: 41, signup_date: '2024-12-09', active: false },
      { id: 4, email: 'dan@example.com', age: 34, signup_date: null, active: true },
    ];

    return {
      jobId,
      beforeData: {
        columns: [
          { name: 'id', type: 'string' },
          { name: 'email', type: 'string' },
          { name: 'age', type: 'string' },
          { name: 'signup_date', type: 'string' },
          { name: 'active', type: 'string' },
        ],
        rows: beforeRows,
        rowCount: beforeRows.length,
        metadata: {
          source: 'demo',
          processedAt: new Date().toISOString(),
          transformations: ['type-normalization', 'date-parsing', 'boolean-mapping', 'validation'],
        },
      },
      afterData: {
        columns: [
          { name: 'id', type: 'number' },
          { name: 'email', type: 'string' },
          { name: 'age', type: 'number', nullable: true },
          { name: 'signup_date', type: 'date', nullable: true },
          { name: 'active', type: 'boolean' },
        ],
        rows: afterRows,
        rowCount: afterRows.length,
        metadata: {
          source: 'demo',
          processedAt: new Date().toISOString(),
          transformations: ['type-normalization', 'date-parsing', 'boolean-mapping', 'validation'],
        },
      },
      errors: [
        { row: 2, column: 'age', message: 'Invalid number', value: 'not_a_number', code: 'INVALID_NUMBER', severity: 'error' },
        { row: 4, column: 'signup_date', message: 'Invalid date', value: 'invalid_date', code: 'INVALID_DATE', severity: 'error' },
      ],
    };
  }, [jobId]);

  const { result: apiResult, isLoading: isApiLoading, error: apiError } = useResult({
    jobId,
    enabled: !isDemo,
  });

  const result = isDemo ? demoResult : apiResult;
  const isLoading = isDemo ? false : isApiLoading;
  const error = isDemo ? null : apiError;

  if (!jobId) {
    return <div>Loading...</div>;
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
                <p className="text-sm sm:text-base text-muted-foreground">
                  Your dataset is now AI-ready and structured.
                </p>
              </div>
            </div>

            <div className="text-muted-foreground text-sm mb-6">
              <span className="opacity-80">Job ID:</span> <span className="break-all">{jobId}</span>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                className="w-full sm:w-auto sm:flex-1"
                disabled={!result?.afterData?.rows?.length}
                onClick={() => downloadJson(`formata-clean-${jobId}.json`, result?.afterData?.rows ?? [])}
              >
                <Download className="mr-2 size-4" />
                Download Clean Dataset
              </Button>
              <Button
                variant="outline"
                className="w-full sm:w-auto sm:flex-1"
                disabled={!result?.errors?.length}
                onClick={() => downloadJson(`formata-errors-${jobId}.json`, result?.errors ?? [])}
              >
                <Download className="mr-2 size-4" />
                Download Error Report
              </Button>
            </div>

            {isLoading && <p className="text-muted-foreground mt-6">Loading results...</p>}

            {error && (
              <div className="mt-6 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                {error.message}
              </div>
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
            <h2 className="text-lg sm:text-xl font-semibold">Transformation Preview</h2>
            <Link href="/ingest" className="text-sm text-primary hover:underline inline-flex items-center gap-2">
              <RotateCcw className="size-4" />
              Process another file
            </Link>
          </div>

          {result && (
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardContent className="p-0">
                  <div className="px-4 sm:px-6 py-4 border-b bg-muted/30 flex items-center justify-between">
                    <div className="text-sm font-semibold text-rose-300/90">BEFORE: RAW DATA</div>
                    <div className="text-xs text-muted-foreground">
                      {result.beforeData?.rows?.length ?? 0} rows
                    </div>
                  </div>
                  <div className="p-4 sm:p-6">
                    {result.beforeData ? <ResultTable beforeData={result.beforeData.rows} /> : <div className="text-muted-foreground">No raw data</div>}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-0">
                  <div className="px-4 sm:px-6 py-4 border-b bg-muted/30 flex items-center justify-between">
                    <div className="text-sm font-semibold text-emerald-300/90">AFTER: STRUCTURED DATA</div>
                    <div className="text-xs text-muted-foreground">
                      {result.afterData?.rows?.length ?? 0} rows
                    </div>
                  </div>
                  <div className="p-4 sm:p-6">
                    {result.afterData ? <ResultTable afterData={result.afterData.rows} /> : <div className="text-muted-foreground">No structured data</div>}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

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

