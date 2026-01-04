'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PreviewTable } from '@/components/PreviewTable';
import { FilterForm } from '@/components/FilterForm';
import { Button } from '@/components/ui/button';
import type { FilterParams } from '@/services/preview.service';
import { applyFiltersClientSide } from '@/utils/fileParser';
import { ingestService } from '@/services/ingest.service';
import { processService } from '@/services/process.service';

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

  useEffect(() => {
    params.then((p) => setjob_id(p.job_id));
  }, [params]);

  useEffect(() => {
    if (!job_id) return;

    const loadPreviewData = () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Load parsed data from sessionStorage (stored after upload)
        const storedData = sessionStorage.getItem(`preview_data_${job_id}`);
        if (!storedData) {
          throw new Error('Preview data not found. Please upload the file again.');
        }
        
        const fileData = JSON.parse(storedData);
        const parsedData = fileData.parsedData;
        
        setData(parsedData.records || []);
        setOriginalData(parsedData.records || []);
        setRowCount(parsedData.records?.length || 0);
        setTotalRows(parsedData.totalRows);
        setColumns(parsedData.columns || []);
        
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
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load preview data'));
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
      // Reset to original data (client-side)
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
      // Reconstruct the file from sessionStorage
      const fileDataBase64 = sessionStorage.getItem(`file_data_${job_id}`);
      const fileName = sessionStorage.getItem(`file_name_${job_id}`);
      const fileType = sessionStorage.getItem(`file_type_${job_id}`);
      
      if (!fileDataBase64 || !fileName) {
        throw new Error('File data not found. Please upload the file again.');
      }
      
      // Convert base64 back to File object
      const binaryString = atob(fileDataBase64);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: fileType || 'application/octet-stream' });
      const file = new File([blob], fileName, { type: fileType || 'application/octet-stream' });
      
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

