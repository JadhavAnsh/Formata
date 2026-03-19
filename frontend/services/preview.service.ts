import { apiGet } from './api';

// Preview data interfaces

export interface PreviewData {
  records: Array<Record<string, any>>;
  columns: string[];
  totalRows?: number;
  preview_count?: number;
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
 * Service for fetching data previews
 */
export const previewService = {
  /**
   * Get a preview of the data for a job
   */
  async getPreview(jobId: string, jwt?: string): Promise<PreviewData> {
    try {
      return await apiGet<PreviewData>(`/preview/${jobId}`, jwt);
    } catch (error) {
      console.error('Error fetching preview:', error);
      throw error;
    }
  }
};
