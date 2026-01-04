import { apiUpload } from './api';
import type { Job } from '@/types/job';

/**
 * Service for file ingestion/upload operations
 */
export const ingestService = {
  /**
   * Upload a file for processing
   */
  async uploadFile(file: File): Promise<Job> {
    return apiUpload('/ingest', file);
  },
};

