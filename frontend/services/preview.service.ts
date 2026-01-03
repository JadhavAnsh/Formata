import { apiRequest } from './api';

export interface PreviewData {
  records: Array<Record<string, any>>;
  metadata?: {
    columns: string[];
    rowCount: number;
    totalRows?: number;
    fileType?: string;
    converted?: boolean;
  };
}

export interface FilterParams {
  [column: string]: {
    op: string;
    value?: any;
    min?: any;
    max?: any;
    start?: any;
    end?: any;
  };
}

/**
 * Service for preview operations
 */
export const previewService = {
  /**
   * Fetch preview data for a job
   */
  async getPreviewData(jobId: string): Promise<PreviewData> {
    return apiRequest<PreviewData>(`/preview/${jobId}`);
  },

  /**
   * Apply filters to preview data
   */
  async applyFilters(jobId: string, filters: FilterParams): Promise<PreviewData> {
    return apiRequest<PreviewData>(`/preview/${jobId}/filter`, {
      method: 'POST',
      body: JSON.stringify(filters),
    });
  },
};

