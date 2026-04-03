'use client';

import { fileCache, parsedPreviewCache } from '@/app/ingest/page';
import { FilterForm } from '@/components/FilterForm';
import { PreviewTable } from '@/components/PreviewTable';
import { Button } from '@/components/ui/button';
import type { FilterParams } from '@/services/preview.service';
import { processService } from '@/services/process.service';
import { applyFiltersClientSide } from '@/utils/fileParser';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

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
  const [filteredData, setFilteredData] = useState<Array<Record<string, any>>>([]);
  const [droppedColumns, setDroppedColumns] = useState<string[]>([]);
  const [isLightweightPreview, setIsLightweightPreview] = useState(false);
  const [lightweightPreviewReason, setLightweightPreviewReason] = useState<string>('');

  const applyDroppedColumns = (
    sourceData: Array<Record<string, any>>,
    columnsToDrop: string[]
  ): Array<Record<string, any>> => {
    if (columnsToDrop.length === 0) {
      return sourceData;
    }

    const dropSet = new Set(columnsToDrop);
    return sourceData.map((row) => {
      const nextRow: Record<string, any> = {};
      Object.keys(row).forEach((key) => {
        if (!dropSet.has(key)) {
          nextRow[key] = row[key];
        }
      });
      return nextRow;
    });
  };

  const normalizeColumnName = (columnName: string): string => {
    return columnName
      .trim()
      .toLowerCase()
      .replace(/[^\w]+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_+|_+$/g, '');
  };

  const isMissingValue = (value: unknown): boolean => {
    if (value === null || value === undefined) {
      return true;
    }

    if (typeof value === 'string') {
      return value.trim() === '';
    }

    return false;
  };

  const visibleColumns = useMemo(
    () => columns.filter((column) => !droppedColumns.includes(column)),
    [columns, droppedColumns]
  );

  const missingByColumn = useMemo(() => {
    if (!filteredData.length || !columns.length) {
      return {} as Record<string, { count: number; percentage: number }>;
    }

    const total = filteredData.length;
    const stats: Record<string, { count: number; percentage: number }> = {};

    columns.forEach((column) => {
      const missingCount = filteredData.reduce((count, row) => {
        return count + (isMissingValue(row[column]) ? 1 : 0);
      }, 0);

      stats[column] = {
        count: missingCount,
        percentage: total > 0 ? (missingCount / total) * 100 : 0,
      };
    });

    return stats;
  }, [filteredData, columns]);

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
      setIsLightweightPreview(false);
      setLightweightPreviewReason('');
      
      try {
        // Large parsed payload is kept in memory to avoid storage quota errors
        const parsedData = parsedPreviewCache.get(job_id);

        const storedData = sessionStorage.getItem(`preview_data_${job_id}`);
        const storedMeta = storedData ? JSON.parse(storedData) as { previewSkipped?: boolean; previewReason?: string } : null;

        if (storedMeta?.previewSkipped) {
          setData([]);
          setOriginalData([]);
          setFilteredData([]);
          setRowCount(0);
          setTotalRows(undefined);
          setColumns([]);
          setColumnTypes({});
          setDroppedColumns([]);
          setAppliedFilters({});
          setIsLightweightPreview(true);
          setLightweightPreviewReason(storedMeta.previewReason || 'Large file preview is unavailable.');
          return;
        }

        if (!parsedData) {
          // Keep backward compatibility for sessions created before this fix
          if (!storedData) {
            throw new Error('Preview data expired. Please upload the file again.');
          }

          const legacyData = JSON.parse(storedData) as { parsedData?: any; preview?: any };
          const fallbackParsed = legacyData.parsedData || legacyData.preview;
          if (!fallbackParsed) {
            throw new Error('Preview data expired. Please upload the file again.');
          }

          parsedPreviewCache.set(job_id, fallbackParsed);
        }

        const resolvedParsedData = parsedPreviewCache.get(job_id);
        if (!resolvedParsedData) {
          throw new Error('Preview data expired. Please upload the file again.');
        }
        
        setData(resolvedParsedData.records || []);
        setOriginalData(resolvedParsedData.records || []);
        setFilteredData(resolvedParsedData.records || []);
        setRowCount(resolvedParsedData.records?.length || 0);
        setTotalRows(resolvedParsedData.totalRows);
        setColumns(resolvedParsedData.columns || []);
        setDroppedColumns([]);
        setAppliedFilters({});
        
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
    if (isLightweightPreview) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      // Client-side filtering (preview is frontend-only)
      const filtered = applyFiltersClientSide(originalData, filters);
      console.log('Filters data:', filters);
      setFilteredData(filtered);
      setData(applyDroppedColumns(filtered, droppedColumns));
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
    if (isLightweightPreview) return;

    setIsFiltering(true);
    setError(null);
    
    try {
      // Reset to original data (client-side)
      setFilteredData(originalData);
      setData(applyDroppedColumns(originalData, droppedColumns));
      setRowCount(originalData.length);
      setAppliedFilters({});
    } catch (err) {
      setError(toError(err, 'Failed to clear filters'));
    } finally {
      setIsFiltering(false);
    }
  };

  const handleToggleDropColumn = (columnName: string, shouldDrop: boolean) => {
    setDroppedColumns((prev) => {
      const next = shouldDrop
        ? [...new Set([...prev, columnName])]
        : prev.filter((value) => value !== columnName);

      setData(applyDroppedColumns(filteredData, next));
      return next;
    });
  };

  const handleClearDroppedColumns = () => {
    setDroppedColumns([]);
    setData(filteredData);
  };

  const handleContinueToProcess = async () => {
    if (!job_id) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      // Get file from memory cache instead of sessionStorage
      const file = fileCache.get(job_id);

      // Current flow ingests before preview, so process the existing job directly.
      // Legacy fallback: if a preview-only ID is used, re-upload once.
      let actualJobId = job_id;
      if (job_id.startsWith('preview_')) {
        if (!file) {
          throw new Error('File data not found. Please upload the file again.');
        }

        const ingestService = await import('@/services/ingest.service');
        const ingestResponse = await ingestService.ingestService.uploadFile(file, {
          preview_rows: 100,
        });
        actualJobId = ingestResponse.job_id || ingestResponse.id || job_id;
      }

      localStorage.setItem('job_id', actualJobId);

      await processService.startProcessing(actualJobId, {
        filters: Object.keys(appliedFilters).length > 0 ? appliedFilters : undefined,
        normalize: true,
        remove_duplicates: true,
        remove_outliers: false,
        default_missing_strategy: 'preserve',
        enable_profiles: true,
        enable_vectorization: false,
        enable_auto_schema: true,
        enable_drift_detection: true,
        result_preview_rows: 2000,
        missing_data_strategy:
          droppedColumns.length > 0
            ? droppedColumns.reduce<Record<string, string>>((acc, column) => {
                acc[column] = 'drop_columns';
                const normalized = normalizeColumnName(column);
                if (normalized) {
                  acc[normalized] = 'drop_columns';
                }
                return acc;
              }, {})
            : undefined,
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
            {isLightweightPreview ? (
              <div className="p-4 rounded-md border bg-muted/20 text-sm text-muted-foreground">
                <p className="font-medium text-foreground mb-1">Lightweight Preview Mode</p>
                <p>{lightweightPreviewReason}</p>
                <p className="mt-2">You can continue to process this file safely without loading full preview rows in the browser.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="border rounded-lg p-4 bg-muted/20">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h3 className="text-sm font-semibold">Column Controls</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Review missing-value density and mark columns to drop before processing.
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={droppedColumns.length === 0}
                      onClick={handleClearDroppedColumns}
                    >
                      Reset Dropped Columns
                    </Button>
                  </div>

                  <div className="mt-4 border rounded-md bg-background max-h-64 overflow-auto">
                    <table className="w-full border-collapse text-sm">
                      <thead className="bg-muted sticky top-0">
                        <tr>
                          <th className="p-2 border text-left">Column</th>
                          <th className="p-2 border text-left">Missing</th>
                          <th className="p-2 border text-left">Keep / Drop</th>
                        </tr>
                      </thead>
                      <tbody>
                        {columns.map((column) => {
                          const stats = missingByColumn[column] || { count: 0, percentage: 0 };
                          const checked = droppedColumns.includes(column);

                          return (
                            <tr key={column}>
                              <td className="p-2 border align-top break-all">{column}</td>
                              <td className="p-2 border align-top">
                                {stats.count} ({stats.percentage.toFixed(1)}%)
                              </td>
                              <td className="p-2 border align-top">
                                <label className="inline-flex items-center gap-2 cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={(e) => handleToggleDropColumn(column, e.target.checked)}
                                  />
                                  <span>{checked ? 'Drop on process' : 'Keep'}</span>
                                </label>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">
                    Selected to drop: {droppedColumns.length} column(s). Missing values are preserved by default for all other columns.
                  </p>
                </div>

                <PreviewTable
                  data={data}
                  columns={visibleColumns}
                  missingByColumn={missingByColumn}
                  isLoading={isLoading || isFiltering}
                  rowCount={rowCount}
                  totalRows={totalRows}
                />
              </div>
            )}
          </div>

          {/* Filter Form */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Filter Parameters</h2>
            {isLightweightPreview ? (
              <div className="p-4 rounded-md border bg-muted/20 text-sm text-muted-foreground">
                Filters are disabled in lightweight preview mode. Click Continue to Process to apply filters server-side in the next step.
              </div>
            ) : (
              <FilterForm
                columns={columns}
                columnTypes={columnTypes}
                onSubmit={handleFilterSubmit}
                onClear={handleClearFilters}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

