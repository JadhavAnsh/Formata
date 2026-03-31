'use client';

import { fileCache, parsedPreviewCache } from '@/app/ingest/page';
import { FilterForm } from '@/components/FilterForm';
import { PreviewTable } from '@/components/PreviewTable';
import { Button } from '@/components/ui/button';
import { ingestService } from '@/services/ingest.service';
import type { FilterParams } from '@/services/preview.service';
import { processService } from '@/services/process.service';
import { applyFiltersClientSide } from '@/utils/fileParser';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface PreviewPageProps {
  params: Promise<{
    job_id: string;
  }>;
}

export default function PreviewPage({ params }: PreviewPageProps) {
  const router = useRouter();
  const [job_id, setjob_id] = useState<string | null>(null);
  const [data, setData] = useState<Array<Record<string, any>>>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [columnTypes, setColumnTypes] = useState<Record<string, 'text' | 'numeric' | 'datetime' | 'boolean'>>({});
  const [rowCount, setRowCount] = useState<number>(0);
  const [totalRows, setTotalRows] = useState<number | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [isFiltering, setIsFiltering] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [appliedFilters, setAppliedFilters] = useState<FilterParams>({});
  const [originalData, setOriginalData] = useState<Array<Record<string, any>>>([]);

  const toError = (err: unknown, fallback: string) => {
    if (err instanceof Error) return err;

    if (err && typeof err === 'object') {
      const maybeMessage = (err as { message?: unknown }).message;
      const maybeDetail = (err as { detail?: unknown }).detail;

      if (typeof maybeMessage === 'string' && maybeMessage.trim()) {
        return new Error(maybeMessage);
      }

      if (typeof maybeDetail === 'string' && maybeDetail.trim()) {
        return new Error(maybeDetail);
      }
    }

    return new Error(fallback);
  };

  useEffect(() => {
    params.then((p) => setjob_id(p.job_id));
  }, [params]);

  useEffect(() => {
    if (!job_id) return;

    const loadPreviewData = () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Large parsed payload is kept in memory to avoid storage quota errors
        const parsedData = parsedPreviewCache.get(job_id);

        if (!parsedData) {
          // Keep backward compatibility for sessions created before this fix
          const storedData = sessionStorage.getItem(`preview_data_${job_id}`);
          if (!storedData) {
            throw new Error('Preview data expired. Please upload the file again.');
          }

          const legacyData = JSON.parse(storedData) as { parsedData?: any };
          if (!legacyData.parsedData) {
            throw new Error('Preview data expired. Please upload the file again.');
          }

          parsedPreviewCache.set(job_id, legacyData.parsedData);
        }

        const resolvedParsedData = parsedPreviewCache.get(job_id);
        if (!resolvedParsedData) {
          throw new Error('Preview data expired. Please upload the file again.');
        }
        
        setData(resolvedParsedData.records || []);
        setOriginalData(resolvedParsedData.records || []);
        setRowCount(resolvedParsedData.records?.length || 0);
        setTotalRows(resolvedParsedData.totalRows);
        setColumns(resolvedParsedData.columns || []);
        
        // Detect column types
        if (resolvedParsedData.records && resolvedParsedData.records.length > 0) {
          const detectedTypes: Record<string, 'text' | 'numeric' | 'datetime' | 'boolean'> = {};
          resolvedParsedData.columns.forEach((col: string) => {
            const sampleValue = resolvedParsedData.records[0][col];
            if (sampleValue === null || sampleValue === undefined) {
              detectedTypes[col] = 'text';
            } else if (typeof sampleValue === 'boolean') {
              detectedTypes[col] = 'boolean';
            } else if (typeof sampleValue === 'number') {
              detectedTypes[col] = 'numeric';
            } else if (typeof sampleValue === 'string') {
              const dateValue = new Date(sampleValue);
              if (!isNaN(dateValue.getTime()) && sampleValue.length > 8) {
                detectedTypes[col] = 'datetime';
              } else {
                detectedTypes[col] = 'text';
              }
            } else {
              detectedTypes[col] = 'text';
            }
          });
          setColumnTypes(detectedTypes);
        }
      } catch (err) {
        setError(toError(err, 'Failed to load preview data'));
      } finally {
        setIsLoading(false);
      }
    };

    loadPreviewData();
  }, [job_id]);

  const handleFilterSubmit = (filters: Record<string, any>) => {
    if (!job_id) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      // Client-side filtering (preview is frontend-only)
      const filtered = applyFiltersClientSide(originalData, filters);
      console.log('Filters data:', filters);
      setData(filtered);
      setRowCount(filtered.length);
      setAppliedFilters(filters as FilterParams);
    } catch (err) {
      setError(toError(err, 'Failed to apply filters'));
    } finally {
      setIsFiltering(false);
    }
  };

  const handleClearFilters = () => {
    if (!job_id) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      // Reset to original data (client-side)
      setData(originalData);
      setRowCount(originalData.length);
      setAppliedFilters({});
    } catch (err) {
      setError(toError(err, 'Failed to clear filters'));
    } finally {
      setIsFiltering(false);
    }
  };

  const handleContinueToProcess = async () => {
    if (!job_id) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      // Get file from memory cache instead of sessionStorage
      const file = fileCache.get(job_id);
      
      if (!file) {
        throw new Error('File data not found. Please upload the file again.');
      }
      
      // Call ingest API with file and filters
      const ingestResponse = await ingestService.uploadFile(file, {
        filters: Object.keys(appliedFilters).length > 0 ? appliedFilters : undefined,
      });
      
      // Extract job_id from ingest response
      const actualJobId = ingestResponse.job_id || ingestResponse.id;
      
      if (!actualJobId) {
        throw new Error('Job ID not found in ingest response');
      }
      
      // Store job_id in localStorage
      localStorage.setItem('job_id', actualJobId);
      
      // Call process API with job_id and filters
      await processService.startProcessing(actualJobId, {
        filters: Object.keys(appliedFilters).length > 0 ? appliedFilters : undefined,
        normalize: true,
        remove_duplicates: true,
        remove_outliers: false,
      });
      
      // Navigate to process page
      router.push(`/process/${actualJobId}`);
    } catch (err) {
      const resolvedError = toError(err, 'Failed to start processing');
      console.error('Failed to continue to process:', resolvedError);
      setError(resolvedError);
    } finally {
      setIsProcessing(false);
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

  return (
    <div className="container mx-auto mt-16 sm:mt-20 px-4 sm:px-6 max-w-6xl">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">Preview Data</h1>
            <p className="text-muted-foreground text-sm">Job ID: {job_id}</p>
          </div>
          <Button 
            onClick={handleContinueToProcess} 
            size="lg"
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Continue to Process'}
          </Button>
        </div>

        {error && (
          <div className="p-4 bg-destructive/10 text-destructive rounded-md text-sm">
            {error.message}
          </div>
        )}

        <div className="space-y-6">
          {/* Data Table */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Data Preview</h2>
            <PreviewTable
              data={data}
              isLoading={isLoading || isFiltering}
              rowCount={rowCount}
              totalRows={totalRows}
            />
          </div>

          {/* Filter Form */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Filter Parameters</h2>
            <FilterForm
              columns={columns}
              columnTypes={columnTypes}
              onSubmit={handleFilterSubmit}
              onClear={handleClearFilters}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

