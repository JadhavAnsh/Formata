import { apiRequest } from './api';
import type { Dataset } from '@/types/dataset';
import type { ValidationError } from '@/types/error';

export interface ProcessingResult {
  jobId: string;
  beforeData?: Dataset;
  afterData?: Dataset;
  errors?: ValidationError[];
  metadata?: Record<string, any>;
}

/**
 * Service for fetching processing results
 */
export const resultService = {
  /**
   * Get processing results for a job
   */
  async getResults(jobId: string): Promise<ProcessingResult> {
    return apiRequest(`/result/${jobId}`);
  },
};

