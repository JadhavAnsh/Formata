import { apiRequest } from './api';
import type { Job } from '@/types/job';

/**
 * Service for processing operations
 */
export const processService = {
  /**
   * Start processing a job
   * @param jobId - The job ID to process
   * @param options - Processing options including filters
   */
  async startProcessing(jobId: string, options?: {
    filters?: Record<string, any>;
    normalize?: boolean;
    remove_duplicates?: boolean;
    remove_outliers?: boolean;
  }): Promise<Job> {
    // Build request body matching ProcessConfig from backend
    const body: {
      filters?: Record<string, any>;
      normalize?: boolean;
      remove_duplicates?: boolean;
      remove_outliers?: boolean;
    } = {};
    
    if (options?.filters) {
      body.filters = options.filters;
    }
    if (options?.normalize !== undefined) {
      body.normalize = options.normalize;
    }
    if (options?.remove_duplicates !== undefined) {
      body.remove_duplicates = options.remove_duplicates;
    }
    if (options?.remove_outliers !== undefined) {
      body.remove_outliers = options.remove_outliers;
    }
    console.log(body);
    
    return apiRequest(`/process/${jobId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
};

