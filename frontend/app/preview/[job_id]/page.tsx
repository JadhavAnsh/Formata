'use client';

import { FilterForm } from '@/components/FilterForm';
import { PreviewTable } from '@/components/PreviewTable';
import { Button } from '@/components/ui/button';
import { previewService } from '@/services/preview.service';
import type { FilterParams } from '@/services/preview.service';
import { processService } from '@/services/process.service';
import { applyFiltersClientSide } from '@/utils/fileParser';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';

interface PreviewPageProps {
  params: Promise<{
    job_id: string;
  }>;
}

export default function PreviewPage({ params }: PreviewPageProps) {
  const { getJwt } = useAuth();
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

  useEffect(() => {
    params.then((p) => setjob_id(p.job_id));
  }, [params]);

  const loadPreviewData = useCallback(async () => {
    if (!job_id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const jwt = await getJwt();
      if (!jwt) throw new Error('Authentication failed');

      const previewData = await previewService.getPreview(job_id, jwt);
      
      setData(previewData.records || []);
      setOriginalData(previewData.records || []);
      setRowCount(previewData.records?.length || 0);
      setTotalRows(previewData.totalRows);
      setColumns(previewData.columns || []);
      
      // Detect column types
      if (previewData.records && previewData.records.length > 0) {
        const detectedTypes: Record<string, 'text' | 'numeric' | 'datetime' | 'boolean'> = {};
        previewData.columns.forEach((col: string) => {
          const sampleValue = previewData.records[0][col];
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
      console.error('Failed to load preview:', err);
      setError(err instanceof Error ? err : new Error('Failed to load preview data'));
    } finally {
      setIsLoading(false);
    }
  }, [job_id, getJwt]);

  useEffect(() => {
    loadPreviewData();
  }, [loadPreviewData]);

  const handleFilterSubmit = (filters: Record<string, any>) => {
    if (!job_id) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      // Client-side filtering on the preview sample
      const filtered = applyFiltersClientSide(originalData, filters);
      setData(filtered);
      setRowCount(filtered.length);
      setAppliedFilters(filters as FilterParams);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to apply filters'));
    } finally {
      setIsFiltering(false);
    }
  };

  const handleClearFilters = () => {
    if (!job_id) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      setData(originalData);
      setRowCount(originalData.length);
      setAppliedFilters({});
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to clear filters'));
    } finally {
      setIsFiltering(false);
    }
  };

  const handleContinueToProcess = async () => {
    if (!job_id) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const jwt = await getJwt();
      if (!jwt) throw new Error('Authentication failed');
      
      // Store job_id in localStorage for other hooks
      localStorage.setItem('job_id', job_id);
      
      // Call process API with job_id and the filters applied in preview
      await processService.startProcessing(job_id, {
        filters: Object.keys(appliedFilters).length > 0 ? appliedFilters : undefined,
        normalize: true,
        remove_duplicates: true,
        remove_outliers: false,
      }, jwt);
      
      // Navigate to process page
      router.push(`/process/${job_id}`);
    } catch (err) {
      console.error('Failed to continue to process:', err);
      setError(err instanceof Error ? err : new Error('Failed to start processing'));
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

