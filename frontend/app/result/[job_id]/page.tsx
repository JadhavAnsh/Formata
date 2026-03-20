'use client';

import { useEffect, useState } from 'react';

import { ErrorTable } from '@/components/ErrorTable';
import { PreviewTable } from '@/components/PreviewTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/context/AuthContext';
import { useResult } from '@/hooks/useResult';
import { resultService } from '@/services/result.service';
import { vectorService } from '@/services/vector.service';
import { Brain, CheckCircle2, Download, FileText, Loader2, RotateCcw, Table as TableIcon } from 'lucide-react';
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

export default function ResultPage({ params }: ResultPageProps) {
  const [job_id, setjob_id] = useState<string | null>(null);
  const router = useRouter();
  const { getJwt } = useAuth();
  
  const [isVectorizing, setIsVectorizing] = useState(false);
  const [vectorInfo, setVectorInfo] = useState<any>(null);
  const [vectorError, setVectorError] = useState<string | null>(null);
  const [vectorMethod, setVectorMethod] = useState<'hybrid' | 'text_only' | 'numeric'>('hybrid');
  const [vectorProvider, setVectorProvider] = useState<'local' | 'gemini'>('local');
  const [activeTab, setActiveTab] = useState('after');

  useEffect(() => {
    params.then((p) => setjob_id(p.job_id));
  }, [params]);

  const { result, isLoading, error } = useResult({
    jobId: job_id,
    enabled: !!job_id,
  });

  useEffect(() => {
    if (result?.metadata?.vector_info) {
      setVectorInfo(result.metadata.vector_info);
    }
  }, [result]);

  const handleGenerateVectors = async () => {
    if (!job_id) return;
    
    setIsVectorizing(true);
    setVectorError(null);
    
    try {
      const jwt = await getJwt();
      const response = await vectorService.generateVectors(job_id, {
        method: vectorMethod,
        provider: vectorProvider
      }, jwt ?? undefined);
      
      setVectorInfo(response);
    } catch (err: any) {
      console.error('Vectorization failed:', err);
      // Log more details if it's an ApiError
      if (err.status) {
        console.error(`Status: ${err.status}, Message: ${err.message}`);
      }
      setVectorError(err.message || 'Failed to generate vectors');
    } finally {
      setIsVectorizing(false);
    }
  };

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
  
  const qualityScore = clampToPercent(
    result?.metadata?.quality_score?.consistency_score ??
    result?.metadata?.summary?.quality_score?.consistency_score ??
    (totalRows > 0 ? Math.round(100 - (errorCount / totalRows) * 100) : 0)
  );

  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (qualityScore / 100) * circumference;

  return (
    <div className="min-h-screen mt-22 pt-24 sm:pt-28 pb-16 px-4 sm:px-6 relative">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(124,58,237,0.18)_0%,transparent_55%)]" />
      <div className="max-w-6xl mx-auto">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
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

            <div className="text-muted-foreground text-sm">
              <span className="opacity-80">Job ID:</span> <span className="break-all">{job_id}</span>
            </div>

            <Card className="bg-card/50 backdrop-blur-sm border-primary/10">
              <CardContent className="p-6">
                <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                  <Download className="size-5 text-primary" />
                  Download Results
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Button
                    className="w-full"
                    onClick={async () => {
                      if (!job_id) return;
                      try {
                        const jwt = await getJwt();
                        await resultService.downloadResult(job_id, jwt ?? undefined);
                      } catch (err) {
                        console.error('Download failed:', err);
                      }
                    }}
                  >
                    <Download className="mr-2 size-4" />
                    Clean Dataset (CSV)
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      if (!job_id) return;
                      router.push(`/error-report/${job_id}`);
                    }}
                  >
                    <FileText className="mr-2 size-4" />
                    Error Report
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur-sm border-primary/10">
              <CardContent className="p-6">
                <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                  <Brain className="size-5 text-primary" />
                  Advanced Vectorization
                </h3>
                
                {vectorInfo ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-3">
                      <CheckCircle2 className="size-5 text-emerald-500 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-emerald-500">Vectors Generated Successfully</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Shape: {vectorInfo.vector_shape?.join(' x ') || vectorInfo.shape?.join(' x ')} | 
                          Provider: {vectorInfo.provider} | 
                          Method: {vectorInfo.method}
                        </p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Button
                        variant="secondary"
                        onClick={async () => {
                          if (!job_id) return;
                          try {
                            const jwt = await getJwt();
                            await resultService.downloadVectorPkl(job_id, jwt ?? undefined);
                          } catch (err) {
                            console.error('Download failed:', err);
                          }
                        }}
                      >
                        <Download className="mr-2 size-4" />
                        Download .pkl
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={async () => {
                          if (!job_id) return;
                          try {
                            const jwt = await getJwt();
                            await resultService.downloadVectorH5(job_id, jwt ?? undefined);
                          } catch (err) {
                            console.error('Download failed:', err);
                          }
                        }}
                      >
                        <Download className="mr-2 size-4" />
                        Download .h5
                      </Button>
                    </div>
                    
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-xs"
                      onClick={() => setVectorInfo(null)}
                    >
                      Regenerate with different options
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground uppercase">Embedding Provider</label>
                        <select 
                          className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm"
                          value={vectorProvider}
                          onChange={(e) => setVectorProvider(e.target.value as any)}
                        >
                          <option value="local">Local Hashing (Fast, Offline)</option>
                          <option value="gemini">Google Gemini (Semantic, High-Quality)</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground uppercase">Vectorization Method</label>
                        <select 
                          className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm"
                          value={vectorMethod}
                          onChange={(e) => setVectorMethod(e.target.value as any)}
                        >
                          <option value="hybrid">Hybrid (Semantic + Numeric)</option>
                          <option value="text_only">Text Only (Treat all as text)</option>
                          <option value="numeric">Numeric Only (Scaling + One-hot)</option>
                        </select>
                      </div>
                    </div>
                    
                    {vectorError && (
                      <p className="text-xs text-destructive bg-destructive/10 p-2 rounded">{vectorError}</p>
                    )}
                    
                    <Button 
                      className="w-full" 
                      onClick={handleGenerateVectors}
                      disabled={isVectorizing}
                    >
                      {isVectorizing ? (
                        <>
                          <Loader2 className="mr-2 size-4 animate-spin" />
                          Generating Vectors...
                        </>
                      ) : (
                        <>
                          <Brain className="mr-2 size-4" />
                          Generate Vectors for LLM
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {isLoading && <p className="text-muted-foreground mt-6">Loading results...</p>}

            {error && (
              <div className="mt-6 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                {error.message}
              </div>
            )}
          </div>

          <Card className="h-fit lg:sticky lg:top-28">
            <CardContent className="p-6">
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
                  <div className="text-xs text-muted-foreground mt-1">
                    {qualityScore >= 90
                      ? 'Excellent quality. Ready for ML training.'
                      : qualityScore >= 70
                        ? 'Good quality. Review minor issues.'
                        : 'Needs review. Check validation errors.'}
                  </div>
                </div>

                <div className="w-full pt-4 mt-4 border-t border-border/50 grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-xs text-muted-foreground uppercase">Records</div>
                    <div className="text-lg font-semibold">{totalRows}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground uppercase">Issues</div>
                    <div className="text-lg font-semibold text-rose-500">{errorCount}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-10">
          <div className="flex items-center justify-end mb-4">
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
                    <div className="text-sm font-semibold text-rose-300/90">VALIDATION ERRORS</div>
                    <div className="text-xs text-muted-foreground">{result.errors.length} issues</div>
                  </div>
                  <div className="p-4 sm:p-6">
                    <ErrorTable errors={result.errors} />
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : null}

          {(result?.beforeData || result?.afterData) && (
            <div className="mt-8 space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <TableIcon className="size-5 text-primary" />
                <h3 className="text-lg font-medium">Data Preview</h3>
              </div>
              
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="mb-4">
                  <TabsTrigger value="after">Processed Data</TabsTrigger>
                  <TabsTrigger value="before">Original Data</TabsTrigger>
                </TabsList>
                
                <TabsContent value="after" className="mt-0">
                  <Card>
                    <CardContent className="p-0">
                      <PreviewTable 
                        data={result.afterData?.rows || []} 
                        rowCount={result.afterData?.rows?.length}
                        totalRows={result.afterData?.rowCount}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>
                
                <TabsContent value="before" className="mt-0">
                  <Card>
                    <CardContent className="p-0">
                      <PreviewTable 
                        data={result.beforeData?.rows || []} 
                        rowCount={result.beforeData?.rows?.length}
                        totalRows={result.beforeData?.rowCount}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

