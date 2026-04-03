import { apiUpload } from './api';
import type { Job } from '@/types/job';

export interface IngestPreviewPayload {
  records: Array<Record<string, any>>;
  metadata?: {
    columns: string[];
    rowCount: number;
    totalRows?: number;
    sampled?: boolean;
  };
}

export interface IngestResponse extends Job {
  preview?: IngestPreviewPayload;
}

/**
 * Service for file ingestion/upload operations
 */
export const ingestService = {
  /**
   * Upload a file for processing
   */
  async uploadFile(file: File, options?: {
    filters?: Record<string, any>;
    normalization?: Record<string, any>;
    preview_rows?: number;
  }): Promise<IngestResponse> {
    return apiUpload('/ingest', file, options);
  },
};

