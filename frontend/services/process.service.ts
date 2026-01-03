import { apiRequest } from './api';
import type { Job } from '@/types/job';

/**
 * Service for processing operations
 */
export const processService = {
  /**
   * Start processing a job
   */
  async startProcessing(jobId: string, options?: {
    filters?: Record<string, any>;
    normalization?: Record<string, any>;
  }): Promise<Job> {
    return apiRequest(`/process/${jobId}`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  },
};

