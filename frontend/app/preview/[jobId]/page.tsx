'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PreviewTable } from '@/components/PreviewTable';
import { FilterForm } from '@/components/FilterForm';
import { Button } from '@/components/ui/button';
import { previewService, type FilterParams } from '@/services/preview.service';
import { applyFiltersClientSide } from '@/utils/fileParser';

interface PreviewPageProps {
  params: Promise<{
    jobId: string;
  }>;
}

export default function PreviewPage({ params }: PreviewPageProps) {
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);
  const [data, setData] = useState<Array<Record<string, any>>>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [columnTypes, setColumnTypes] = useState<Record<string, 'text' | 'numeric' | 'datetime' | 'boolean'>>({});
  const [rowCount, setRowCount] = useState<number>(0);
  const [totalRows, setTotalRows] = useState<number | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [isFiltering, setIsFiltering] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [appliedFilters, setAppliedFilters] = useState<FilterParams>({});
  const [isUsingLocalData, setIsUsingLocalData] = useState(false);
  const [originalData, setOriginalData] = useState<Array<Record<string, any>>>([]);

  useEffect(() => {
    params.then((p) => setJobId(p.jobId));
  }, [params]);

  useEffect(() => {
    if (!jobId) return;

    const loadPreviewData = async () => {
      setIsLoading(true);
      setError(null);
      
      // Check for local data first (temporary bypass)
      if (jobId.startsWith('temp_')) {
        try {
          const storedData = localStorage.getItem(`preview_data_${jobId}`);
          if (storedData) {
            const fileData = JSON.parse(storedData);
            const parsedData = fileData.parsedData;
            
            setData(parsedData.records || []);
            setOriginalData(parsedData.records || []);
            setRowCount(parsedData.records?.length || 0);
            setTotalRows(parsedData.totalRows);
            setColumns(parsedData.columns || []);
            setIsUsingLocalData(true);
            
            // Detect column types
            if (parsedData.records && parsedData.records.length > 0) {
              const detectedTypes: Record<string, 'text' | 'numeric' | 'datetime' | 'boolean'> = {};
              parsedData.columns.forEach((col: string) => {
                const sampleValue = parsedData.records[0][col];
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
            
            setIsLoading(false);
            return;
          }
        } catch (err) {
          console.warn('Failed to load local data, falling back to API:', err);
        }
      }
      
      // Fall back to API
      try {
        const result = await previewService.getPreviewData(jobId);
        setData(result.records || []);
        setOriginalData(result.records || []);
        setRowCount(result.records?.length || 0);
        
        if (result.metadata) {
          setColumns(result.metadata.columns || []);
          setTotalRows(result.metadata.totalRows);
          
          // Detect column types from data (simple heuristic)
          if (result.records && result.records.length > 0) {
            const detectedTypes: Record<string, 'text' | 'numeric' | 'datetime' | 'boolean'> = {};
            result.metadata.columns.forEach((col) => {
              const sampleValue = result.records[0][col];
              if (sampleValue === null || sampleValue === undefined) {
                detectedTypes[col] = 'text';
              } else if (typeof sampleValue === 'boolean') {
                detectedTypes[col] = 'boolean';
              } else if (typeof sampleValue === 'number') {
                detectedTypes[col] = 'numeric';
              } else if (typeof sampleValue === 'string') {
                // Try to detect date
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
        }
        setIsUsingLocalData(false);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load preview data'));
      } finally {
        setIsLoading(false);
      }
    };

    loadPreviewData();
  }, [jobId]);

  const handleFilterSubmit = async (filters: Record<string, any>) => {
    if (!jobId) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      if (isUsingLocalData) {
        // Client-side filtering
        const filtered = applyFiltersClientSide(originalData, filters);
        setData(filtered);
        setRowCount(filtered.length);
        setAppliedFilters(filters as FilterParams);
      } else {
        // API filtering
        const result = await previewService.applyFilters(jobId, filters as FilterParams);
        setData(result.records || []);
        setRowCount(result.records?.length || 0);
        setAppliedFilters(filters as FilterParams);
        
        if (result.metadata) {
          setTotalRows(result.metadata.totalRows);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to apply filters'));
    } finally {
      setIsFiltering(false);
    }
  };

  const handleClearFilters = async () => {
    if (!jobId) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      if (isUsingLocalData) {
        // Reset to original data
        setData(originalData);
        setRowCount(originalData.length);
        setAppliedFilters({});
      } else {
        // API reset
        const result = await previewService.getPreviewData(jobId);
        setData(result.records || []);
        setRowCount(result.records?.length || 0);
        setAppliedFilters({});
        
        if (result.metadata) {
          setTotalRows(result.metadata.totalRows);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to clear filters'));
    } finally {
      setIsFiltering(false);
    }
  };

  const handleContinueToProcess = () => {
    // Pass filters via URL params or state
    const filterParams = new URLSearchParams();
    if (Object.keys(appliedFilters).length > 0) {
      filterParams.set('filters', JSON.stringify(appliedFilters));
    }
    const queryString = filterParams.toString();
    router.push(`/process/${jobId}${queryString ? `?${queryString}` : ''}`);
  };

  if (!jobId) {
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
            <p className="text-muted-foreground text-sm">Job ID: {jobId}</p>
            {isUsingLocalData && (
              <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                ⚠️ Using temporary client-side parsing (API not available)
              </p>
            )}
          </div>
          <Button onClick={handleContinueToProcess} size="lg">
            Continue to Process
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

